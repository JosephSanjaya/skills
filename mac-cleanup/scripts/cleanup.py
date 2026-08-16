#!/usr/bin/env python3
"""macOS workspace cleanup. Dry-run by default. File deletes stay inside $HOME allowlist."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

HOME = Path.home()

DELETE_ALLOWLIST = (
    HOME / "Library/Developer/Xcode/DerivedData",
    HOME / "Library/Caches",
    HOME / "Library/Logs/DiagnosticReports",
    HOME / ".Trash",
)

AUDIT_PATHS = (
    HOME / "Library/Caches",
    HOME / "Library/Developer",
    HOME / "Library/Developer/Xcode/DerivedData",
    HOME / "Library/Developer/CoreSimulator",
    HOME / "Library/Containers",
    HOME / "Library/Application Support/MobileSync/Backup",
)

DEFAULT_APPLY_MODULES = ("brew", "xcode", "npm", "pip", "pnpm", "yarn", "go")
OPT_IN_MODULES = ("docker", "snapshots", "trash", "caches", "crash-reports")
ALL_MODULES = ("audit", *DEFAULT_APPLY_MODULES, *OPT_IN_MODULES)


@dataclass(frozen=True)
class Action:
    module: str
    summary: str
    bytes_estimate: int | None = None
    argv: tuple[str, ...] | None = None
    delete_dir: str | None = None
    skip_reason: str | None = None


@dataclass
class Report:
    dry_run: bool
    platform: str
    disk: dict[str, str]
    heavy_paths: list[dict[str, str | int | None]]
    snapshots: list[str]
    actions: list[Action]
    warnings: list[str]


def run(argv: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)


def which(name: str) -> str | None:
    return shutil.which(name)


def human_bytes(size: int | None) -> str:
    if size is None:
        return "unknown"
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def dir_size_bytes(path: Path) -> int | None:
    if not path.exists():
        return 0
    try:
        result = run(["du", "-sk", str(path)], timeout=60)
    except subprocess.TimeoutExpired:
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return int(result.stdout.split()[0]) * 1024


def is_allowed_delete(path: Path) -> bool:
    home = HOME.resolve()
    for candidate in (path.expanduser(), path.expanduser().resolve()):
        try:
            candidate.relative_to(home)
        except ValueError:
            return False
    resolved = path.expanduser().resolve()
    return any(_is_under(resolved, allowed.expanduser().resolve()) for allowed in DELETE_ALLOWLIST)


def _is_under(path: Path, root: Path) -> bool:
    return path == root or path.is_relative_to(root)


def clear_dir_contents(directory: Path) -> list[str]:
    if not is_allowed_delete(directory):
        raise SystemExit(f"refusing delete outside allowlist: {directory}")
    if not directory.is_dir():
        return []
    removed: list[str] = []
    for child in directory.iterdir():
        removed.append(str(child))
        if child.is_symlink() or child.is_file():
            child.unlink(missing_ok=True)
        elif child.is_dir():
            shutil.rmtree(child)
    return removed


def audit_disk() -> dict[str, str]:
    result = run(["df", "-h", "/"])
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    return {"df": lines[-1] if len(lines) >= 2 else result.stdout.strip()}


def audit_snapshots() -> list[str]:
    if not which("tmutil"):
        return []
    result = run(["tmutil", "listlocalsnapshots", "/"])
    return [line.strip() for line in result.stdout.splitlines() if line.strip()][1:]


def audit_heavy_paths() -> list[dict[str, str | int | None]]:
    rows: list[dict[str, str | int | None]] = []
    for path in AUDIT_PATHS:
        size = dir_size_bytes(path) if path.exists() else 0
        rows.append({"path": str(path), "bytes": size, "display": human_bytes(size)})
    return rows


def tool_action(module: str, binary: str, argv: tuple[str, ...], summary: str) -> Action:
    if not which(binary):
        return Action(module, summary, skip_reason=f"{binary} not on PATH")
    return Action(module, summary, argv=argv)


def brew_cache_bytes() -> int | None:
    if not which("brew"):
        return None
    result = run(["brew", "--cache"])
    cache = Path(result.stdout.strip())
    return dir_size_bytes(cache) if result.returncode == 0 and cache.exists() else None


def plan_brew() -> list[Action]:
    cleanup = tool_action("brew", "brew", ("brew", "cleanup", "-s"), "scrub Homebrew download cache")
    if cleanup.skip_reason is None:
        cleanup = Action(
            cleanup.module,
            cleanup.summary,
            bytes_estimate=brew_cache_bytes(),
            argv=cleanup.argv,
        )
    return [
        cleanup,
        tool_action("brew", "brew", ("brew", "autoremove"), "remove unused Homebrew dependencies"),
    ]


def plan_xcode() -> list[Action]:
    derived = HOME / "Library/Developer/Xcode/DerivedData"
    actions = [
        Action(
            "xcode",
            "clear Xcode DerivedData contents",
            bytes_estimate=dir_size_bytes(derived) if derived.exists() else 0,
            delete_dir=str(derived),
            skip_reason=None if derived.exists() else "DerivedData folder missing",
        ),
        tool_action(
            "xcode",
            "xcrun",
            ("xcrun", "simctl", "delete", "unavailable"),
            "delete simulators left behind by Xcode upgrades",
        ),
    ]
    return actions


def plan_docker(*, aggressive: bool) -> list[Action]:
    actions = [
        tool_action("docker", "docker", ("docker", "builder", "prune", "-f"), "prune Docker build cache"),
        tool_action("docker", "docker", ("docker", "system", "prune", "-f"), "prune dangling Docker data"),
    ]
    if aggressive:
        actions.append(
            tool_action(
                "docker",
                "docker",
                ("docker", "system", "prune", "-a", "-f"),
                "prune unused Docker images (not volumes)",
            )
        )
    return actions


def plan_snapshots(thin_bytes: int) -> list[Action]:
    if not which("tmutil"):
        return [Action("snapshots", "thin local Time Machine snapshots", skip_reason="tmutil not on PATH")]
    return [
        Action(
            "snapshots",
            f"thin local snapshots, target {human_bytes(thin_bytes)}",
            argv=("tmutil", "thinlocalsnapshots", "/", str(thin_bytes), "4"),
        )
    ]


def plan_delete_module(module: str, relative: str, summary: str) -> list[Action]:
    path = HOME / relative
    return [
        Action(
            module,
            summary,
            bytes_estimate=dir_size_bytes(path) if path.exists() else 0,
            delete_dir=str(path),
            skip_reason=None if path.exists() else f"{path} missing",
        )
    ]


def collect_actions(modules: set[str], *, aggressive: bool, thin_bytes: int) -> list[Action]:
    actions: list[Action] = []
    if "brew" in modules:
        actions.extend(plan_brew())
    if "xcode" in modules:
        actions.extend(plan_xcode())
    if "docker" in modules:
        actions.extend(plan_docker(aggressive=aggressive))
    if "npm" in modules:
        actions.append(tool_action("npm", "npm", ("npm", "cache", "clean", "--force"), "clean npm cache"))
    if "pip" in modules:
        binary = "pip" if which("pip") else "pip3"
        actions.append(tool_action("pip", binary, (binary, "cache", "purge"), "purge pip cache"))
    if "pnpm" in modules:
        actions.append(tool_action("pnpm", "pnpm", ("pnpm", "store", "prune"), "prune pnpm store"))
    if "yarn" in modules:
        actions.append(tool_action("yarn", "yarn", ("yarn", "cache", "clean"), "clean yarn cache"))
    if "go" in modules:
        actions.append(tool_action("go", "go", ("go", "clean", "-cache"), "clean Go build cache"))
    if "snapshots" in modules:
        actions.extend(plan_snapshots(thin_bytes))
    if "trash" in modules:
        actions.extend(plan_delete_module("trash", ".Trash", "empty user Trash"))
    if "caches" in modules:
        actions.extend(plan_delete_module("caches", "Library/Caches", "clear user cache contents"))
    if "crash-reports" in modules:
        actions.extend(
            plan_delete_module(
                "crash-reports",
                "Library/Logs/DiagnosticReports",
                "clear user DiagnosticReports",
            )
        )
    return actions


def execute(action: Action) -> str:
    if action.skip_reason:
        return f"skipped: {action.skip_reason}"
    if action.argv:
        result = run(list(action.argv), timeout=300)
        if result.returncode != 0:
            return f"failed ({result.returncode}): {result.stderr.strip() or result.stdout.strip()}"
        return "ok"
    if action.delete_dir:
        removed = clear_dir_contents(Path(action.delete_dir))
        return f"removed {len(removed)} entries"
    return "nothing to do"


def parse_modules(raw: str | None) -> set[str]:
    selected = {item.strip() for item in raw.split(",") if item.strip()} if raw else set(DEFAULT_APPLY_MODULES)
    unknown = selected - set(ALL_MODULES)
    if unknown:
        raise SystemExit(f"unknown modules: {', '.join(sorted(unknown))}")
    return selected


def format_report(report: Report) -> str:
    lines = [
        f"{'DRY-RUN' if report.dry_run else 'APPLY'} on {report.platform}",
        f"disk: {report.disk.get('df', 'n/a')}",
        f"snapshots: {len(report.snapshots)}",
        "heavy paths:",
    ]
    for row in report.heavy_paths:
        lines.append(f"  {row['display']:>12}  {row['path']}")
    lines.append("actions:")
    for action in report.actions:
        size = f" ({human_bytes(action.bytes_estimate)})" if action.bytes_estimate is not None else ""
        suffix = f" [skip: {action.skip_reason}]" if action.skip_reason else ""
        lines.append(f"  [{action.module}] {action.summary}{size}{suffix}")
    for warning in report.warnings:
        lines.append(f"warning: {warning}")
    if report.dry_run:
        lines.append("re-run with --apply --modules … to execute. snapshots/trash/caches/docker stay opt-in unless listed.")
    return "\n".join(lines)


def self_check() -> None:
    outside = Path("/tmp/mac-cleanup-should-fail")
    assert not is_allowed_delete(outside), "must reject paths outside $HOME"
    assert not is_allowed_delete(Path("/System/Library")), "must reject /System"
    derived = HOME / "Library/Developer/Xcode/DerivedData"
    assert is_allowed_delete(derived), "must allow DerivedData"
    assert parse_modules("brew,xcode") == {"brew", "xcode"}
    try:
        parse_modules("rm-root")
    except SystemExit:
        pass
    else:
        raise AssertionError("unknown module must fail")
    print("self-check ok")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="execute planned actions (default is dry-run)")
    parser.add_argument("--modules", help="comma-separated module list")
    parser.add_argument("--aggressive", action="store_true", help="Docker unused images; still never prune volumes")
    parser.add_argument("--thin-bytes", type=int, default=100_000_000_000, help="snapshot thin target in bytes")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    parser.add_argument("--self-check", action="store_true", help="run allowlist assertions and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.self_check:
        self_check()
        return 0
    if sys.platform != "darwin":
        raise SystemExit("mac-cleanup only runs on macOS")
    modules = parse_modules(args.modules)
    warnings: list[str] = []
    if args.apply and modules & set(OPT_IN_MODULES):
        warnings.append(f"opt-in modules requested: {', '.join(sorted(modules & set(OPT_IN_MODULES)))}")
    report = Report(
        dry_run=not args.apply,
        platform=sys.platform,
        disk=audit_disk(),
        heavy_paths=audit_heavy_paths(),
        snapshots=audit_snapshots(),
        actions=collect_actions(modules, aggressive=args.aggressive, thin_bytes=args.thin_bytes),
        warnings=warnings,
    )
    results: list[dict[str, object]] = []
    if args.apply:
        for action in report.actions:
            results.append({**asdict(action), "result": execute(action)})
    payload = {**asdict(report), "results": results}
    payload["actions"] = [asdict(action) for action in report.actions]
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(format_report(report))
        for item in results:
            print(f"result [{item['module']}] {item['summary']}: {item['result']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
