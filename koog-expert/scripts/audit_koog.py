#!/usr/bin/env python3
"""Static scanner for Koog anti-patterns in Kotlin sources.

Usage:
    python3 audit_koog.py <path> [<path> ...]
    python3 audit_koog.py --json src/

Exit codes: 0 no findings, 1 findings, 2 usage error.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

SKIP_DIRS = {"build", ".gradle", ".git", "node_modules"}


@dataclass(slots=True)
class Finding:
    file: str
    line: int
    severity: str
    code: str
    title: str
    detail: str


def _iter_kotlin(root: Path) -> list[Path]:
    if root.is_file() and root.suffix == ".kt":
        return [root]
    if not root.is_dir():
        return []
    files: list[Path] = []
    for path in root.rglob("*.kt"):
        if SKIP_DIRS.intersection(path.parts):
            continue
        files.append(path)
    return files


def _read(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []


_EXECUTOR_NAMED = re.compile(r"\bAIAgent\s*\([^)]*\bexecutor\s*=")
_PROMPT_EXECUTOR = re.compile(r"\bpromptExecutor\s*=")
_AI_AGENT_CALL = re.compile(r"\bAIAgent\s*\(")
_MAX_ITER = re.compile(r"\bmax(Iterations|AgentIterations)\b")
_ON_TOOL_FILTER = re.compile(r"onToolCalls\s*\{\s*(?!true\b)")
_COMPRESS_NODE = re.compile(r"\bnodeLLMCompressHistory\b")
_ON_CONDITION = re.compile(r"\bonCondition\b")
_WRITE_SESSION = re.compile(r"\bwriteSession\s*\{")
_IO_IN_BLOCK = re.compile(
    r"\b(delay\(|HttpClient\b|jdbc:|exposed\.|\.execute\(|kotlinx\.coroutines\.io)\b"
)
_HARDCODED_KEY = re.compile(
    r"""(?:api[_-]?key|apikey|token)\s*=\s*["'](?!\$\{)(?![A-Z_]+["'])[A-Za-z0-9_\-]{12,}["']""",
    re.IGNORECASE,
)
_SK_LIVE = re.compile(r"sk-(?:ant-)?[A-Za-z0-9]{10,}")
_TOOL_ANN = re.compile(r"@Tool\b")
_LLM_DESC = re.compile(r"@LLMDescription\b")
_MCP = re.compile(r"\b(McpToolRegistryProvider|\bmcp\s*\{)\b")
_NON_JVM = ("jsMain", "wasmJsMain", "iosMain", "androidMain", "commonMain")


def _scan_file(path: Path, lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    text = "\n".join(lines)
    rel = str(path)

    if _EXECUTOR_NAMED.search(text) and not _PROMPT_EXECUTOR.search(text):
        line_no = next(i for i, ln in enumerate(lines, 1) if "executor" in ln and "AIAgent" in text)
        findings.append(
            Finding(
                rel, line_no, "ERROR", "KG1",
                "Stale AIAgent(executor=) parameter",
                "Koog 1.1.1 uses promptExecutor=. Context7/blog snippets are often wrong.",
            )
        )

    if _AI_AGENT_CALL.search(text) and not _MAX_ITER.search(text) and "test" not in rel.lower():
        line_no = next(i for i, ln in enumerate(lines, 1) if "AIAgent(" in ln)
        findings.append(
            Finding(
                rel, line_no, "WARNING", "KG2",
                "AIAgent without explicit iteration cap",
                "Set maxIterations / maxAgentIterations (factory default is 50).",
            )
        )

    for i, ln in enumerate(lines, 1):
        if _ON_TOOL_FILTER.search(ln) and "true" not in ln:
            findings.append(
                Finding(
                    rel, i, "ERROR", "KG3",
                    "Filtered onToolCalls can drop parallel tools",
                    "Use onToolCalls { true } or add a catch-all edge (#2153).",
                )
            )
        if _HARDCODED_KEY.search(ln) or _SK_LIVE.search(ln):
            findings.append(
                Finding(
                    rel, i, "ERROR", "KG4",
                    "Possible hardcoded LLM credential",
                    "Load keys from environment or a secret manager.",
                )
            )

    if _COMPRESS_NODE.search(text) and not _ON_CONDITION.search(text):
        line_no = next(i for i, ln in enumerate(lines, 1) if "nodeLLMCompressHistory" in ln)
        findings.append(
            Finding(
                rel, line_no, "WARNING", "KG5",
                "History compression without onCondition threshold",
                "Compressing every iteration spends extra tokens. Gate on message/token size.",
            )
        )

    in_write = 0
    for i, ln in enumerate(lines, 1):
        if _WRITE_SESSION.search(ln):
            in_write = ln.count("{") - ln.count("}")
            if in_write <= 0:
                in_write = 1
            continue
        if in_write:
            in_write += ln.count("{") - ln.count("}")
            if _IO_IN_BLOCK.search(ln):
                findings.append(
                    Finding(
                        rel, i, "WARNING", "KG6",
                        "I/O inside llm.writeSession",
                        "Write sessions take an exclusive lock. Do heavy I/O first.",
                    )
                )
            if in_write <= 0:
                in_write = 0

    tool_lines = [i for i, ln in enumerate(lines, 1) if _TOOL_ANN.search(ln)]
    for i in tool_lines:
        window = "\n".join(lines[max(0, i - 1) : min(len(lines), i + 6)])
        if not _LLM_DESC.search(window):
            findings.append(
                Finding(
                    rel, i, "WARNING", "KG7",
                    "@Tool without nearby @LLMDescription",
                    "The model only sees @LLMDescription text; missing it wastes tokens and accuracy.",
                )
            )

    if _MCP.search(text) and any(part in path.parts for part in _NON_JVM):
        line_no = next(i for i, ln in enumerate(lines, 1) if "mcp" in ln.lower() or "Mcp" in ln)
        findings.append(
            Finding(
                rel, line_no, "ERROR", "KG8",
                "MCP used outside JVM source set",
                "agents-mcp transports are JVM-only. Call a JVM backend from apps.",
            )
        )

    return findings


def scan(paths: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for raw in paths:
        for kt in _iter_kotlin(Path(raw)):
            lines = _read(kt)
            if lines:
                findings.extend(_scan_file(kt, lines))
    findings.sort(key=lambda f: ({"ERROR": 0, "WARNING": 1, "INFO": 2}[f.severity], f.file, f.line))
    return findings


def _print_text(findings: list[Finding]) -> None:
    if not findings:
        print("No Koog anti-patterns detected.")
        return
    icons = {"ERROR": "E", "WARNING": "W", "INFO": "I"}
    for f in findings:
        print(f"{icons[f.severity]} [{f.code}] {f.severity}  {f.file}:{f.line}")
        print(f"  {f.title}")
        print(f"  {f.detail}")
        print()
    counts = {s: sum(1 for x in findings if x.severity == s) for s in ("ERROR", "WARNING", "INFO")}
    print(
        f"Summary: {counts['ERROR']} error(s), {counts['WARNING']} warning(s), "
        f"{counts['INFO']} info(s) — {len(findings)} total"
    )


def main() -> int:
    args = sys.argv[1:]
    as_json = "--json" in args
    paths = [a for a in args if not a.startswith("--")]
    if not paths:
        print("Usage: audit_koog.py [--json] <path> [<path> ...]", file=sys.stderr)
        return 2
    findings = scan(paths)
    if as_json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        _print_text(findings)
    return 1 if findings else 0


def _selfcheck() -> None:
    """Fails if the stale-executor rule regresses."""
    sample = ["val agent = AIAgent(", "    executor = simpleOpenAIExecutor(key),", ")"]
    hits = _scan_file(Path("synthetic.kt"), sample)
    codes = {h.code for h in hits}
    assert "KG1" in codes, codes


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        _selfcheck()
        print("selfcheck ok")
        raise SystemExit(0)
    raise SystemExit(main())
