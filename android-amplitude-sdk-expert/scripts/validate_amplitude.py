#!/usr/bin/env python3
"""
Amplitude SDK validation script for Android codebases.
Scans files for legacy imports, outdated method calls, and common configuration pitfalls.
"""

import argparse
import os
import re
import sys

# Regex patterns for validation
LEGACY_IMPORT = re.compile(r"import\s+com\.amplitude\.api\.")
MODERN_IMPORT = re.compile(r"import\s+com\.amplitude\.android\.")
LEGACY_CALL = re.compile(r"\.logEvent\(")
BLOCKED_THREAD_CALL = re.compile(r"\.fetch\(\)\.get\(\)")
JSON_OBJECT_PROP = re.compile(r"JSONObject\s*\(")
SHORT_ID_ASSIGNMENT = re.compile(r'\.setUserId\(\s*"[^"]{1,4}"\s*\)')


def scan_file(file_path: str) -> list:
    """Scans a single Java/Kotlin file for Amplitude SDK violations."""
    warnings = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                if LEGACY_IMPORT.search(line):
                    warnings.append(
                        f"L{line_num}: Legacy import used (com.amplitude.api). Migrate to modern Kotlin SDK (com.amplitude.android)."
                    )
                if LEGACY_CALL.search(line):
                    warnings.append(
                        f"L{line_num}: Legacy logEvent() call found. Migrate to modern track()."
                    )
                if BLOCKED_THREAD_CALL.search(line):
                    warnings.append(
                        f"L{line_num}: Blocking fetch().get() call found on Experiment. This can cause ANR; run off-main thread."
                    )
                if JSON_OBJECT_PROP.search(line) and (
                    "amplitude" in line.lower() or "event" in line.lower()
                ):
                    warnings.append(
                        f"L{line_num}: JSONObject reference for event properties. Modern Kotlin SDK uses Map<String, Any?>."
                    )
                if SHORT_ID_ASSIGNMENT.search(line):
                    warnings.append(
                        f"L{line_num}: Short userId (< 5 chars) assigned. Modern SDK HTTP V2 requires min 5-char IDs unless minIdLength is overridden."
                    )
    except Exception as e:
        warnings.append(f"Failed to read file: {e}")
    return warnings


def main():
    parser = argparse.ArgumentParser(
        description="Scans Kotlin/Java source files for Amplitude SDK usage issues."
    )
    parser.add_argument(
        "target", help="Absolute or relative path to the directory or file to scan."
    )
    args = parser.parse_args()

    if not os.path.exists(args.target):
        print(f"Error: Target path '{args.target}' does not exist.", file=sys.stderr)
        sys.exit(1)

    total_warnings = 0
    files_scanned = 0

    if os.path.isfile(args.target):
        files_to_scan = [args.target]
    else:
        files_to_scan = []
        for root, _, files in os.walk(args.target):
            for file in files:
                if file.endswith((".kt", ".java")):
                    files_to_scan.append(os.path.join(root, file))

    print(f"Scanning {len(files_to_scan)} files for Amplitude SDK usage patterns...")

    for file_path in files_to_scan:
        file_warnings = scan_file(file_path)
        if file_warnings:
            files_scanned += 1
            total_warnings += len(file_warnings)
            rel_path = os.path.relpath(file_path, os.path.dirname(args.target))
            print(f"\n[!] Issues found in: {rel_path}")
            for warning in file_warnings:
                print(f"  - {warning}")

    print("\n" + "=" * 40)
    print(f"Scan completed. Scanned {len(files_to_scan)} files.")
    print(f"Found {total_warnings} issues across {files_scanned} files.")
    print("=" * 40)

    if total_warnings > 0:
        sys.exit(1)
    else:
        print("[✓] No Amplitude SDK issues found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
