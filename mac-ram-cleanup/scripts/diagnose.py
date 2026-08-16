#!/usr/bin/env python3
"""macOS RAM diagnose. Read-only. Never purges caches or allocates pressure."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

PAGE_SIZE_RE = re.compile(r"page size of (\d+) bytes")
VM_LINE_RE = re.compile(r'^"?([^"]+?)"?:\s+(\d+)\.?$')
SWAP_RE = re.compile(r"(total|used|free)\s*=\s*([\d.]+)([MG])", re.I)
FREE_PCT_RE = re.compile(r"System-wide memory free percentage:\s*(\d+)%")
BOOT_SEC_RE = re.compile(r"sec\s*=\s*(\d+)")

FAMILY_RULES: tuple[tuple[str, str], ...] = (
    ("com.docker", "Docker Desktop"),
    ("docker", "Docker Desktop"),
    ("orbstack", "OrbStack"),
    ("vmware", "VMware"),
    ("windowserver", "WindowServer"),
    ("kernel_task", "kernel_task"),
    ("mdworker", "Spotlight"),
    ("mds_stores", "Spotlight"),
    ("mds", "Spotlight"),
    ("photoanalysis", "Photos analysis"),
    ("photolibrary", "Photos analysis"),
    ("google chrome", "Chrome family"),
    ("chromium", "Chrome family"),
    ("brave", "Chrome family"),
    ("msedge", "Edge"),
    ("firefox", "Firefox family"),
    ("zen.app", "Zen/Firefox family"),
    ("cursor.app", "Cursor"),
    ("virtualization.framework", "Virtualization.framework"),
)

NEVER_QUIT = frozenset({"kernel_task", "WindowServer", "launchd", "init"})
PressureBand = Literal["green", "yellow", "red", "unknown"]


@dataclass(frozen=True)
class VmSnapshot:
    page_size: int
    pages: dict[str, int]


@dataclass(frozen=True)
class Proc:
    pid: int
    rss_bytes: int
    command: str
    family: str


@dataclass
class Report:
    pressure_band: PressureBand
    kernel_pressure: int | None
    physical_bytes: int
    page_size: int
    swap_mib: dict[str, float]
    swapout_delta: int
    swapin_delta: int
    pageout_delta: int
    compressor_occupied_bytes: int
    compressor_stored_bytes: int
    tool_free_percent: int | None
    disk: dict[str, int | str]
    uptime_days: float | None
    sample_seconds: float
    top_processes: list[Proc]
    families: list[dict[str, int | str]]
    advice: list[str]
    warnings: list[str]


def run(argv: list[str], *, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)


def human_bytes(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def parse_vm_stat(text: str) -> VmSnapshot:
    page_match = PAGE_SIZE_RE.search(text)
    if not page_match:
        raise ValueError("vm_stat missing page size")
    pages: dict[str, int] = {}
    for line in text.splitlines():
        line_match = VM_LINE_RE.match(line.strip())
        if line_match:
            pages[line_match.group(1)] = int(line_match.group(2))
    return VmSnapshot(page_size=int(page_match.group(1)), pages=pages)


def mib_from_swap_token(amount: str, unit: str) -> float:
    value = float(amount)
    return value * 1024 if unit.upper() == "G" else value


def parse_swapusage(text: str) -> dict[str, float]:
    parsed = {key: 0.0 for key in ("total", "used", "free")}
    for key, amount, unit in SWAP_RE.findall(text):
        parsed[key.lower()] = mib_from_swap_token(amount, unit)
    return parsed


def parse_memory_pressure_tool(text: str) -> int | None:
    match = FREE_PCT_RE.search(text)
    return int(match.group(1)) if match else None


def page_bytes(snapshot: VmSnapshot, key: str) -> int:
    return snapshot.pages.get(key, 0) * snapshot.page_size


def process_family(command: str) -> str:
    lower = command.lower()
    for needle, label in FAMILY_RULES:
        if needle in lower:
            return label
    app = re.search(r"/([^/]+)\.app/", command)
    if app:
        return app.group(1)
    return Path(command.split()[0]).name[:40]


def parse_ps(text: str) -> list[Proc]:
    procs: list[Proc] = []
    for line in text.splitlines():
        parts = line.split(None, 2)
        if len(parts) < 3:
            continue
        try:
            rss_bytes = int(parts[1]) * 1024
            command = parts[2].strip()
            procs.append(
                Proc(int(parts[0]), rss_bytes, command, process_family(command))
            )
        except ValueError:
            continue
    return procs


def coalesce_families(procs: list[Proc]) -> list[dict[str, int | str]]:
    totals: dict[str, int] = {}
    for proc in procs:
        totals[proc.family] = totals.get(proc.family, 0) + proc.rss_bytes
    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    return [{"family": name, "rss_bytes": size} for name, size in ranked[:12]]


def pressure_band(
    *, kernel: int | None, swapout_delta: int, swap_used_mib: float
) -> PressureBand:
    thrashing = swapout_delta > 0
    if kernel == 0 and not thrashing:
        return "green"
    if thrashing:
        return "red"
    if kernel is not None and kernel > 0:
        return "red" if kernel >= 80 or swap_used_mib > 4096 else "yellow"
    if kernel is None and not thrashing:
        return "green"
    return "unknown"


def quittable(procs: list[Proc]) -> Proc | None:
    for proc in procs:
        base = Path(proc.command.split()[0]).name
        if base in NEVER_QUIT or proc.family in NEVER_QUIT:
            continue
        return proc
    return None


def build_advice(report: Report) -> list[str]:
    disk_used = int(report.disk.get("capacity_percent", 0))
    if report.pressure_band == "green":
        lines = [
            "Do nothing to RAM. Kernel reports no pressure; full RAM + compression is healthy."
        ]
        hog = quittable(report.top_processes)
        if hog and hog.rss_bytes >= 8 * 1024**3:
            lines.append(
                f"Optional headroom only: quit {hog.family} ({human_bytes(hog.rss_bytes)}) if you do not need it."
            )
        if disk_used >= 85:
            lines.append("Disk is tight; swap may stall. Use mac-cleanup, not a RAM cleaner.")
        return lines
    hog = quittable(report.top_processes)
    lines = [
        "Pressure is elevated or swapouts occurred during the sample. Fix the hog; do not purge caches."
    ]
    if hog:
        lines.append(
            f"Top quittable: pid {hog.pid} {hog.family} ({human_bytes(hog.rss_bytes)}). Save, then quit/restart it."
        )
    if any(item["family"] == "Docker Desktop" for item in report.families):
        lines.append("Docker Desktop holds a static VM. Stop Docker, or switch to OrbStack for dynamic reclaim.")
    if any("Chrome" in item["family"] or item["family"] == "Edge" for item in report.families):
        lines.append("Enable browser Memory Saver / Sleeping Tabs; fully quit (Cmd+Q); prefer Safari when possible.")
    if disk_used >= 85:
        lines.append("Keep 10–20% disk free so swap files can grow. Audit disk with mac-cleanup.")
    if report.uptime_days is not None and report.uptime_days >= 7:
        lines.append("Uptime ≥ 7 days: a reboot clears leaked anonymous memory and accumulated swap files.")
    lines.append("Never sudo purge, RAM-cleaner apps, or nvram compressor boot-args.")
    return lines


def read_int_sysctl(name: str) -> int | None:
    result = run(["sysctl", "-n", name])
    if result.returncode != 0:
        return None
    try:
        return int(result.stdout.strip().split()[0])
    except (ValueError, IndexError):
        return None


def read_swap() -> dict[str, float]:
    result = run(["sysctl", "vm.swapusage"])
    return parse_swapusage(result.stdout or result.stderr)


def read_tool_free_percent() -> int | None:
    if not shutil.which("memory_pressure"):
        return None
    result = run(["memory_pressure"])
    if result.returncode != 0:
        return None
    return parse_memory_pressure_tool(result.stdout)


def read_uptime_days() -> float | None:
    result = run(["sysctl", "-n", "kern.boottime"])
    match = BOOT_SEC_RE.search(result.stdout)
    if not match:
        return None
    return max(0.0, (time.time() - int(match.group(1))) / 86400)


def read_disk() -> dict[str, int | str]:
    volume = "/System/Volumes/Data" if Path("/System/Volumes/Data").exists() else "/"
    result = run(["df", "-k", volume])
    lines = result.stdout.strip().splitlines()
    if len(lines) < 2:
        return {"mount": volume, "capacity_percent": 0, "available_bytes": 0}
    fields = lines[-1].split()
    available_bytes = int(fields[3]) * 1024
    capacity_percent = int(fields[4].rstrip("%"))
    return {
        "mount": volume,
        "capacity_percent": capacity_percent,
        "available_bytes": available_bytes,
    }


def read_procs() -> list[Proc]:
    result = run(["ps", "-axo", "pid=,rss=,command="])
    return sorted(parse_ps(result.stdout), key=lambda proc: proc.rss_bytes, reverse=True)


def sample_vm(sample_seconds: float) -> tuple[VmSnapshot, VmSnapshot]:
    first = parse_vm_stat(run(["vm_stat"]).stdout)
    time.sleep(sample_seconds)
    second = parse_vm_stat(run(["vm_stat"]).stdout)
    return first, second


def diagnose(*, sample_seconds: float, top: int) -> Report:
    first, second = sample_vm(sample_seconds)
    kernel = read_int_sysctl("vm.memory_pressure")
    physical = read_int_sysctl("hw.memsize") or 0
    swap = read_swap()
    procs = read_procs()
    disk = read_disk()
    report = Report(
        pressure_band="unknown",
        kernel_pressure=kernel,
        physical_bytes=physical,
        page_size=second.page_size,
        swap_mib=swap,
        swapout_delta=second.pages.get("Swapouts", 0) - first.pages.get("Swapouts", 0),
        swapin_delta=second.pages.get("Swapins", 0) - first.pages.get("Swapins", 0),
        pageout_delta=second.pages.get("Pageouts", 0) - first.pages.get("Pageouts", 0),
        compressor_occupied_bytes=page_bytes(second, "Pages occupied by compressor"),
        compressor_stored_bytes=page_bytes(second, "Pages stored in compressor"),
        tool_free_percent=read_tool_free_percent(),
        disk=disk,
        uptime_days=read_uptime_days(),
        sample_seconds=sample_seconds,
        top_processes=procs[:top],
        families=coalesce_families(procs),
        advice=[],
        warnings=[],
    )
    report.pressure_band = pressure_band(
        kernel=kernel, swapout_delta=report.swapout_delta, swap_used_mib=swap["used"]
    )
    if report.tool_free_percent is not None:
        report.warnings.append(
            f"memory_pressure free%={report.tool_free_percent} is cache headroom, not the pressure graph."
        )
    if kernel is None:
        report.warnings.append("vm.memory_pressure unread; using swapout rate only.")
    report.advice = build_advice(report)
    return report


def format_report(report: Report) -> str:
    stored, occupied = report.compressor_stored_bytes, report.compressor_occupied_bytes
    ratio = f"{stored / occupied:.1f}x" if occupied else "n/a"
    lines = [
        f"pressure_band: {report.pressure_band}  kernel_pressure: {report.kernel_pressure}",
        f"physical: {human_bytes(report.physical_bytes)}  page_size: {report.page_size} B",
        (
            f"swap: used {report.swap_mib['used']:.1f} MiB / total {report.swap_mib['total']:.1f} MiB"
            f"  sample {report.sample_seconds:.1f}s  swapouts={report.swapout_delta} swapins={report.swapin_delta} pageouts={report.pageout_delta}"
        ),
        (
            f"compressor: occupied {human_bytes(occupied)} holding {human_bytes(stored)} ({ratio})"
        ),
        (
            f"disk: {report.disk['mount']} {report.disk['capacity_percent']}% used, "
            f"{human_bytes(int(report.disk['available_bytes']))} free"
        ),
        f"uptime_days: {report.uptime_days:.1f}" if report.uptime_days is not None else "uptime_days: unknown",
        "top RSS:",
    ]
    for proc in report.top_processes[:10]:
        lines.append(f"  {proc.pid:>6} {human_bytes(proc.rss_bytes):>10}  {proc.family}  {proc.command[:60]}")
    lines.append("families:")
    for item in report.families[:8]:
        lines.append(f"  {human_bytes(int(item['rss_bytes'])):>10}  {item['family']}")
    lines.append("advice:")
    lines.extend(f"  - {item}" for item in report.advice)
    lines.extend(f"warning: {item}" for item in report.warnings)
    return "\n".join(lines)


def self_check() -> None:
    fixture = (
        "Mach Virtual Memory Statistics: (page size of 16384 bytes)\n"
        "Pages occupied by compressor:                 544120.\n"
        "Pages stored in compressor:                  1158036.\n"
        "Swapins:                                           0.\n"
        "Swapouts:                                          0.\n"
    )
    snapshot = parse_vm_stat(fixture)
    assert snapshot.page_size == 16384
    assert page_bytes(snapshot, "Pages occupied by compressor") == 544120 * 16384
    swap = parse_swapusage("vm.swapusage: total = 4.00G  used = 3160.25M  free = 935.75M  (encrypted)")
    assert abs(swap["total"] - 4096) < 0.01
    assert parse_memory_pressure_tool("System-wide memory free percentage: 72%\n") == 72
    assert pressure_band(kernel=0, swapout_delta=0, swap_used_mib=2048) == "green"
    assert pressure_band(kernel=0, swapout_delta=12, swap_used_mib=100) == "red"
    assert process_family("Google Chrome Helper (Renderer)") == "Chrome family"
    assert process_family("/Applications/Zen.app/Contents/MacOS/plugin-container") == "Zen/Firefox family"
    assert process_family("/Applications/Notes.app/Contents/MacOS/Notes") == "Notes"
    hog = quittable(
        [Proc(1, 10**9, "kernel_task", "kernel_task"), Proc(9, 10**9, "VMware", "VMware")]
    )
    assert hog is not None and hog.family == "VMware"
    assert "--purge" not in (build_parser().format_help())
    print("self-check ok")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    parser.add_argument("--sample-seconds", type=float, default=2.0, help="vm_stat rate sample window")
    parser.add_argument("--top", type=int, default=15, help="how many RSS rows to keep")
    parser.add_argument("--self-check", action="store_true", help="run parser assertions and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.self_check:
        self_check()
        return 0
    if sys.platform != "darwin":
        raise SystemExit("mac-ram-cleanup only runs on macOS")
    if args.sample_seconds < 0:
        raise SystemExit("--sample-seconds must be >= 0")
    report = diagnose(sample_seconds=args.sample_seconds, top=args.top)
    if args.json:
        payload = asdict(report)
        payload["top_processes"] = [asdict(proc) for proc in report.top_processes]
        print(json.dumps(payload, indent=2))
    else:
        print(format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
