#!/usr/bin/env python3
"""Validate AGENTS.md / CLAUDE.md files against the 10 rules from Gloaguen et al. (2026)."""

import argparse
import sys
import re
from pathlib import Path

# Common generic guidelines that LLMs already know
GENERIC_PATTERNS = [
    (r"clean\s+code", "Generic coding guidelines ('clean code')"),
    (r"error\s+handling", "Generic guidelines ('error handling')"),
    (r"solid\s+principles", "Generic guidelines ('SOLID')"),
    (r"meaningful\s+variable", "Generic guidelines ('meaningful variable names')"),
    (r"camelcase|snake_case|pascalcase", "Generic naming conventions"),
    (r"follow\s+best\s+practices", "Generic guidelines ('best practices')"),
    (r"readable\s+code", "Generic guidelines ('readable code')"),
]

# Structural indicators of directory structure overviews
DIRECTORY_OVERVIEW_PATTERNS = [
    r"^[ \t]*[-*+]\s+`?[a-zA-Z0-9_\-\/]+\/`?\s+[-—]\s+",
    r"^[ \t]*├──|└──",
    r"^[ \t]*│\s+├──|└──",
]

def check_word_count(content: str) -> tuple[int, str | None]:
    words = content.split()
    count = len(words)
    if count > 800:
        return count, f"Word count ({count}) exceeds 800-word target limit. Ruthlessly trim the file."
    return count, None

def check_directory_overview(content: str) -> list[str]:
    issues = []
    lines = content.splitlines()
    for idx, line in enumerate(lines, 1):
        for pattern in DIRECTORY_OVERVIEW_PATTERNS:
            if re.search(pattern, line):
                issues.append(f"Line {idx}: Potential directory tree overview. Agents do not benefit from structure maps.")
                break
    return issues

def check_generic_guidelines(content: str) -> list[str]:
    issues = []
    lines = content.splitlines()
    for idx, line in enumerate(lines, 1):
        for pattern, label in GENERIC_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append(f"Line {idx}: Contains {label}. LLMs already know these default conventions.")
    return issues

def check_imperative_mood(content: str) -> list[str]:
    issues = []
    lines = content.splitlines()
    # Check for passive or overly descriptive project descriptions
    descriptive_keywords = ["is used for", "we are using", "this project contains", "intended to show"]
    for idx, line in enumerate(lines, 1):
        for kw in descriptive_keywords:
            if kw in line.lower():
                issues.append(f"Line {idx}: Descriptive phrasing ('{kw}'). Prefer imperative, direct commands.")
    return issues

def check_redundancy(file_path: Path, content: str) -> list[str]:
    issues = []
    readme_path = file_path.parent / "README.md"
    if not readme_path.exists():
        return issues
    
    readme_content = readme_path.read_text(errors="replace")
    # Simple check for block duplication
    lines = [line.strip() for line in content.splitlines() if len(line.strip()) > 30]
    for line in lines:
        if line in readme_content:
            issues.append(f"Duplicate content found in README.md: '{line[:50]}...'")
    return issues

def main() -> None:
    parser = argparse.ArgumentParser(description="Lint agent context files for size and high-signal constraints.")
    parser.add_argument("file", type=str, help="Path to AGENTS.md, CLAUDE.md or .cursorrules")
    args = parser.parse_args()

    target_path = Path(args.file)
    if not target_path.exists():
        print(f"Error: Target file {target_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    content = target_path.read_text(errors="replace")
    
    word_count, count_issue = check_word_count(content)
    overview_issues = check_directory_overview(content)
    generic_issues = check_generic_guidelines(content)
    imperative_issues = check_imperative_mood(content)
    redundancy_issues = check_redundancy(target_path, content)

    print(f"## agentlint report")
    print(f"**File:** {target_path}")
    print(f"**Word count:** {word_count} (target: <800)")
    
    total_issues = 0
    
    if count_issue:
        print(f"\n### [HIGH] Word Count")
        print(f"- {count_issue}")
        total_issues += 1

    if overview_issues:
        print(f"\n### [HIGH] Rule 1: No codebase overviews")
        for issue in overview_issues[:5]:
            print(f"- {issue}")
        if len(overview_issues) > 5:
            print(f"- ... and {len(overview_issues) - 5} more overview issues.")
        total_issues += 1

    if redundancy_issues:
        print(f"\n### [HIGH] Rule 2: No redundancy with existing docs")
        for issue in redundancy_issues[:5]:
            print(f"- {issue}")
        if len(redundancy_issues) > 5:
            print(f"- ... and {len(redundancy_issues) - 5} more duplicate lines.")
        total_issues += 1

    if generic_issues:
        print(f"\n### [MEDIUM] Rule 7: No generic coding guidelines")
        for issue in generic_issues[:5]:
            print(f"- {issue}")
        if len(generic_issues) > 5:
            print(f"- ... and {len(generic_issues) - 5} more generic guidelines.")
        total_issues += 1

    if imperative_issues:
        print(f"\n### [LOW] Rule 8: Prefer imperative over descriptive")
        for issue in imperative_issues[:5]:
            print(f"- {issue}")
        if len(imperative_issues) > 5:
            print(f"- ... and {len(imperative_issues) - 5} more descriptive phrases.")
        total_issues += 1

    score = max(0, 10 - total_issues * 2)
    print(f"\n### Score: {score}/10")
    if score >= 8:
        print("Success: Context file is clean and high-signal.")
        sys.exit(0)
    else:
        print("Warning: Context file contains significant bloat. Trim redundancy and codebase overviews.")
        sys.exit(1)

if __name__ == "__main__":
    main()
