#!/usr/bin/env python3
"""
audit_tests.py — Static scanner for Kotlin test anti-patterns.

Usage:
    python audit_tests.py <path>           # scan directory or file
    python audit_tests.py src/test/        # typical usage
    python audit_tests.py --json src/      # output JSON (for CI)

Exit codes:
    0 — no findings
    1 — findings detected
"""

import re
import sys
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Finding:
    file: str
    line: int
    severity: str  # ERROR | WARNING | INFO
    code: str      # AP1..AP10
    title: str
    detail: str


SEVERITIES = {"ERROR": 0, "WARNING": 1, "INFO": 2}


# ─── Pattern definitions ──────────────────────────────────────────────────────

def check_ap1_private_method_exposed(lines: list[str], filepath: str) -> list[Finding]:
    """AP1: internal modifier on a non-companion member that is likely only for test access."""
    findings = []
    in_test_file = "test" in filepath.lower()
    if in_test_file:
        return findings  # skip test files themselves
    for i, line in enumerate(lines, 1):
        # Look for `internal fun` or `internal val` in non-test production classes
        if re.search(r'\binternal\b\s+(fun|val|var|class)\b', line):
            findings.append(Finding(
                file=filepath, line=i, severity="WARNING", code="AP1",
                title="Internal member may be exposed for test access",
                detail="`internal` visibility is sometimes used only to expose a member to tests. "
                       "Consider testing via the public API or extracting an abstraction.",
            ))
    return findings


def check_ap3_domain_knowledge_leak(lines: list[str], filepath: str) -> list[Finding]:
    """AP3: Expected value computed from inputs inside a test (duplicates production logic)."""
    findings = []
    arithmetic_ops = re.compile(r'val\s+expected\s*=\s*\w+\s*[+\-*/]\s*\w+')
    for i, line in enumerate(lines, 1):
        if arithmetic_ops.search(line):
            findings.append(Finding(
                file=filepath, line=i, severity="ERROR", code="AP3",
                title="Domain knowledge leak: expected value computed from inputs",
                detail="Computing `expected` from the same inputs as the SUT duplicates the "
                       "algorithm. Hard-code the expected value instead.",
            ))
    return findings


def check_ap4_code_pollution(lines: list[str], filepath: str) -> list[Finding]:
    """AP4: isTestEnvironment, isTest, isMock flags in production code."""
    findings = []
    if "test" in filepath.lower():
        return findings
    pollution_pattern = re.compile(
        r'\b(isTest|isTestEnvironment|isMock|testMode|forTesting|testOnly)\b',
        re.IGNORECASE,
    )
    for i, line in enumerate(lines, 1):
        if pollution_pattern.search(line) and not line.strip().startswith("//"):
            findings.append(Finding(
                file=filepath, line=i, severity="ERROR", code="AP4",
                title="Code pollution: test-only flag in production code",
                detail="Production code should not contain test-environment switches. "
                       "Use an interface with separate production and test implementations.",
            ))
    return findings


def check_ap5_mock_concrete_class(lines: list[str], filepath: str) -> list[Finding]:
    """AP5: spyk(ConcreteClass()) — partial mocking of a concrete class."""
    findings = []
    spyk_pattern = re.compile(r'\bspyk\s*\(\s*\w+\(')
    for i, line in enumerate(lines, 1):
        if spyk_pattern.search(line):
            findings.append(Finding(
                file=filepath, line=i, severity="WARNING", code="AP5",
                title="Mocking a concrete class with spyk()",
                detail="Partial mocking of a concrete class signals a Single Responsibility "
                       "violation. Split the class: one for domain logic, one for external "
                       "communication with an interface.",
            ))
    return findings


def check_ap6_stub_verification(lines: list[str], filepath: str) -> list[Finding]:
    """AP6: coVerify/verify on a repository/finder — typically a stub, not a mock."""
    findings = []
    # Heuristic: verify called with a name that looks like a repository or finder (incoming)
    stub_verify = re.compile(
        r'\b(co)?[Vv]erify\b.*\b\w*(repo|repository|finder|store|cache|source|reader|provider)\b',
        re.IGNORECASE,
    )
    for i, line in enumerate(lines, 1):
        if stub_verify.search(line):
            findings.append(Finding(
                file=filepath, line=i, severity="WARNING", code="AP6",
                title="Possible stub interaction assertion",
                detail="Verifying calls on a repository/finder couples the test to internal "
                       "plumbing rather than outcomes. Assert the result instead. Only verify "
                       "mocks (outgoing side effects like email, events, bus).",
            ))
    return findings


def check_ap7_implementation_details(lines: list[str], filepath: str) -> list[Finding]:
    """AP7: Asserting internal structure (subRenderers, size of internal list, etc.)."""
    findings = []
    impl_detail_pattern = re.compile(
        r'\.(subRenderers|internalList|_\w+|handlers|listeners|observers|callbacks)\b'
    )
    for i, line in enumerate(lines, 1):
        if impl_detail_pattern.search(line) and re.search(r'should|assert|verify', line, re.IGNORECASE):
            findings.append(Finding(
                file=filepath, line=i, severity="WARNING", code="AP7",
                title="Asserting internal implementation detail",
                detail="Asserting internal collections or private-like fields couples the test "
                       "to implementation. Verify the observable output instead.",
            ))
    return findings


def check_ap8_ambient_time(lines: list[str], filepath: str) -> list[Finding]:
    """AP8: Direct use of LocalDateTime.now(), Clock.systemUTC(), etc. in production code."""
    findings = []
    if "test" in filepath.lower():
        return findings
    time_pattern = re.compile(
        r'\b(LocalDateTime|LocalDate|Instant|ZonedDateTime|OffsetDateTime|Date)\s*\.\s*(now|systemUTC|systemDefaultZone)\s*\(',
    )
    for i, line in enumerate(lines, 1):
        if time_pattern.search(line) and not line.strip().startswith("//"):
            findings.append(Finding(
                file=filepath, line=i, severity="ERROR", code="AP8",
                title="Ambient time dependency",
                detail="Hidden time dependencies make tests non-deterministic. Inject time as a "
                       "plain value parameter or a Clock interface.",
            ))
    return findings


def check_ap9_multiple_acts(lines: list[str], filepath: str) -> list[Finding]:
    """AP9: More than one call to the SUT in a single test (heuristic: `sut.` appears 2+ times)."""
    findings = []
    # Find test boundaries (Kotest strings or `test(` / `it(` / `fun test`)
    test_start = re.compile(r'^\s*(test\s*\(|it\s*\(|"[^"]+"\s*\{|fun\s+test\w+\s*\()')
    sut_call = re.compile(r'\bsut\.')
    in_test = False
    test_line = 0
    sut_calls = 0
    brace_depth = 0

    for i, line in enumerate(lines, 1):
        if not in_test and test_start.match(line):
            in_test = True
            test_line = i
            sut_calls = 0
            brace_depth = 0

        if in_test:
            brace_depth += line.count('{') - line.count('}')
            if sut_call.search(line):
                sut_calls += 1
            if brace_depth <= 0 and in_test:
                if sut_calls > 1:
                    findings.append(Finding(
                        file=filepath, line=test_line, severity="WARNING", code="AP9",
                        title=f"Multiple SUT calls in one test ({sut_calls} calls to sut.*)",
                        detail="Multiple acts in a single test make it hard to diagnose failures. "
                               "Split into one test per action.",
                    ))
                in_test = False

    return findings


def check_ap10_trivial_test(lines: list[str], filepath: str) -> list[Finding]:
    """AP10: Test with no assertion (assertion-free), or assertion that always passes."""
    findings = []
    # Find test blocks with no shouldBe / shouldNotBe / assert / verify / shouldThrow
    test_start = re.compile(r'^\s*(test\s*\(|it\s*\(|"[^"]+"\s*\{|fun\s+test\w+\s*\()')
    assertion = re.compile(r'(should|assert|verify|expect)', re.IGNORECASE)
    in_test = False
    test_line = 0
    has_assertion = False
    brace_depth = 0

    for i, line in enumerate(lines, 1):
        if not in_test and test_start.match(line):
            in_test = True
            test_line = i
            has_assertion = False
            brace_depth = 0

        if in_test:
            brace_depth += line.count('{') - line.count('}')
            if assertion.search(line):
                has_assertion = True
            if brace_depth <= 0 and in_test:
                if not has_assertion:
                    findings.append(Finding(
                        file=filepath, line=test_line, severity="ERROR", code="AP10",
                        title="Test has no assertion",
                        detail="A test with no assertion always passes and provides zero regression "
                               "protection. Add an assertion or delete the test.",
                    ))
                in_test = False

    return findings


def check_naming_method_in_name(lines: list[str], filepath: str) -> list[Finding]:
    """Naming: test name contains method-under-test pattern like MethodName_Scenario_Result."""
    findings = []
    rigid_name = re.compile(r'"[A-Z]\w+_\w+_\w+"')
    for i, line in enumerate(lines, 1):
        if rigid_name.search(line):
            findings.append(Finding(
                file=filepath, line=i, severity="INFO", code="NAMING",
                title="Rigid test naming pattern detected",
                detail="MethodName_Scenario_Result patterns couple test names to implementation. "
                       "Use plain English: 'blank email is rejected' not 'validateEmail_Blank_ReturnsFalse'.",
            ))
    return findings


# ─── Runner ──────────────────────────────────────────────────────────────────

CHECKERS: tuple = (
    check_ap1_private_method_exposed,
    check_ap3_domain_knowledge_leak,
    check_ap4_code_pollution,
    check_ap5_mock_concrete_class,
    check_ap6_stub_verification,
    check_ap7_implementation_details,
    check_ap8_ambient_time,
    check_ap9_multiple_acts,
    check_ap10_trivial_test,
    check_naming_method_in_name,
)


def scan_file(filepath: str) -> list[Finding]:
    try:
        with open(filepath, encoding="utf-8") as f:
            lines = f.read().splitlines(keepends=True)
    except (OSError, UnicodeDecodeError):
        return []

    findings: list[Finding] = []
    for checker in CHECKERS:
        findings.extend(checker(lines, filepath))

    return sorted(findings, key=lambda f: (SEVERITIES.get(f.severity, 9), f.line))


def scan_path(root: str) -> list[Finding]:
    all_findings: list[Finding] = []
    p = Path(root)
    if p.is_file() and p.suffix == ".kt":
        all_findings.extend(scan_file(str(p)))
    elif p.is_dir():
        for kt_file in p.rglob("*.kt"):
            all_findings.extend(scan_file(str(kt_file)))
    return all_findings


def print_text(findings: list[Finding]) -> None:
    if not findings:
        print("✅  No anti-patterns detected.")
        return

    by_severity: dict = {}
    for f in findings:
        by_severity.setdefault(f.severity, []).append(f)

    for sev in ("ERROR", "WARNING", "INFO"):
        items = by_severity.get(sev, [])
        if not items:
            continue
        match sev:
            case "ERROR":
                icon = "🔴"
            case "WARNING":
                icon = "🟡"
            case _:
                icon = "🔵"
        for f in items:
            print(f"{icon} [{f.code}] {f.severity}  {f.file}:{f.line}")
            print(f"   {f.title}")
            print(f"   {f.detail}")
            print()

    errors = len(by_severity.get("ERROR", []))
    warnings = len(by_severity.get("WARNING", []))
    print(f"Summary: {errors} error(s), {warnings} warning(s), "
          f"{len(by_severity.get('INFO', []))} info(s)  — "
          f"total {len(findings)} finding(s)")


def main() -> int:
    args = sys.argv[1:]
    output_json = "--json" in args
    paths = [a for a in args if not a.startswith("--")]

    if not paths:
        print("Usage: audit_tests.py [--json] <path> [<path> ...]", file=sys.stderr)
        return 2

    all_findings: list[Finding] = []
    for path in paths:
        all_findings.extend(scan_path(path))

    if output_json:
        print(json.dumps(
            [{"file": f.file, "line": f.line, "severity": f.severity,
              "code": f.code, "title": f.title, "detail": f.detail}
             for f in all_findings],
            indent=2,
        ))
    else:
        print_text(all_findings)

    return 1 if any(f.severity == "ERROR" for f in all_findings) else 0


if __name__ == "__main__":
    sys.exit(main())
