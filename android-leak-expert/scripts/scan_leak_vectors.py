#!/usr/bin/env python3
"""
Android Memory Leak Static Analyzer
Scans Java and Kotlin files for common memory leak patterns.
"""

import argparse
import os
import re
import sys

# Colors for output formatting
COLOR_RED = "\033[91m"
COLOR_YELLOW = "\033[93m"
COLOR_GREEN = "\033[92m"
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"

# Regex rules for leak detection
RULES = [
    {
        "id": "STATIC_UI_REF",
        "severity": "CRITICAL",
        "description": "Static reference to UI components or Context (keeps Activity/View alive forever)",
        "patterns": [
            r"companion\s+object[\s\S]*?(?:val|var)\s+\w+\s*:\s*(?:Activity|Context|View|TextView|Button|ImageView|RecyclerView|Binding)\b",
            r"static\s+(?:Activity|Context|View|TextView|Button|ImageView|RecyclerView|\w*Binding)\b",
        ],
    },
    {
        "id": "INNER_CLASS_HANDLER",
        "severity": "WARNING",
        "description": "Non-static inner Handler (implicit outer class reference leaks context if messages delayed)",
        "patterns": [
            r"inner\s+class\s+\w+\s*:\s*(?:Handler|Looper)\b",
            r"class\s+\w+\s+extends\s+Handler\b(?!.*\bstatic\b)",
        ],
    },
    {
        "id": "GLOBAL_SCOPE_LAUNCH",
        "severity": "WARNING",
        "description": "GlobalScope used for coroutines (bypasses structured concurrency, runs indefinitely)",
        "patterns": [r"\bGlobalScope\.(?:launch|async|produce)\b"],
    },
    {
        "id": "FRAGMENT_VIEW_LEAK",
        "severity": "WARNING",
        "description": "Fragment does not nullify view binding in onDestroyView",
        "patterns": [
            r"class\s+\w+\s*:\s*Fragment\(\)[\s\S]*?(?:val|var)\s+_(?:binding|bindingProperty)[\s\S]*?(?!override\s+fun\s+onDestroyView\(\)[\s\S]*?_(?:binding|bindingProperty)\s*=\s*null)"
        ],
    },
    {
        "id": "UNSAFE_COMPOSABLE_LAMBDA",
        "severity": "CRITICAL",
        "description": "Composable function reference stored in ViewModel (leaks Composition hierarchy)",
        "patterns": [
            r"class\s+\w+ViewModel\b[\s\S]*?(?:val|var)\s+\w+\s*:\s*(?:@Composable\s*\(\s*\)\s*->\s*Unit)\b"
        ],
    },
]


def scan_file(file_path):
    issues = []
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()
            lines = content.splitlines()

        for rule in RULES:
            for pat in rule["patterns"]:
                for match in re.finditer(pat, content, re.MULTILINE):
                    # Find line number of the match
                    char_idx = match.start()
                    line_no = content[:char_idx].count("\n") + 1
                    snippet = (
                        lines[line_no - 1].strip() if line_no <= len(lines) else ""
                    )

                    issues.append(
                        {
                            "file": file_path,
                            "line": line_no,
                            "rule_id": rule["id"],
                            "severity": rule["severity"],
                            "description": rule["description"],
                            "snippet": snippet,
                        }
                    )
    except Exception as e:
        print(f"Error scanning file {file_path}: {e}", file=sys.stderr)

    return issues


def scan_directory(dir_path):
    all_issues = []
    for root, _, files in os.walk(dir_path):
        for file in files:
            if file.endswith((".kt", ".java")):
                file_path = os.path.join(root, file)
                all_issues.extend(scan_file(file_path))
    return all_issues


def main():
    parser = argparse.ArgumentParser(
        description="Scan Java/Kotlin files for Android memory leaks."
    )
    parser.add_argument("path", help="File or directory to scan")
    parser.add_argument(
        "--severity", choices=["CRITICAL", "WARNING"], help="Filter by severity"
    )
    args = parser.parse_args()

    target_path = os.path.abspath(args.path)
    if not os.path.exists(target_path):
        print(f"Path does not exist: {target_path}", file=sys.stderr)
        sys.exit(1)

    print(
        f"{COLOR_BOLD}Scanning {target_path} for memory leak vectors...{COLOR_RESET}\n"
    )

    if os.path.isdir(target_path):
        issues = scan_directory(target_path)
    else:
        issues = scan_file(target_path)

    if args.severity:
        issues = [i for i in issues if i["severity"] == args.severity]

    if not issues:
        print(f"{COLOR_GREEN}✅ No memory leak patterns detected!{COLOR_RESET}")
        sys.exit(0)

    # Print results
    criticals = 0
    warnings = 0
    for issue in issues:
        color = COLOR_RED if issue["severity"] == "CRITICAL" else COLOR_YELLOW
        if issue["severity"] == "CRITICAL":
            criticals += 1
        else:
            warnings += 1

        print(
            f"{color}{COLOR_BOLD}[{issue['severity']} - {issue['rule_id']}]{COLOR_RESET}"
        )
        print(f"  File: {issue['file']}:{issue['line']}")
        print(f"  Issue: {issue['description']}")
        print(f"  Code: {issue['snippet']}\n")

    print(f"{COLOR_BOLD}Summary:{COLOR_RESET}")
    print(f"  Critical Issues: {COLOR_RED}{criticals}{COLOR_RESET}")
    print(f"  Warning Issues:  {COLOR_YELLOW}{warnings}{COLOR_RESET}")
    print(f"  Total Found:     {len(issues)}")

    # Exit with code equal to issue count (for CI pipelines)
    sys.exit(len(issues))


if __name__ == "__main__":
    main()
