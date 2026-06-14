#!/usr/bin/env python3
import os
import re
import sys

# Regex patterns for common StrictMode violations
PATTERNS = {
    "shared_prefs_commit": {
        "regex": r"\.edit\(\)\..*?\.commit\(\)",
        "message": "[ThreadPolicy:DiskWrite] SharedPreferences .commit() blocks the UI thread immediately. Use Kotlin coroutines + DataStore, or .apply() if temporary.",
        "severity": "HIGH",
    },
    "shared_prefs_apply": {
        "regex": r"\.edit\(\)\..*?\.apply\(\)",
        "message": "[ThreadPolicy:DiskWrite] SharedPreferences .apply() enqueues a background task tracked by QueuedWork. Can freeze UI thread via fsync lock in Activity lifecycle. Migrate to Jetpack DataStore.",
        "severity": "MEDIUM",
    },
    "unbuffered_io": {
        "regex": r"(?:new\s+)(FileInputStream|FileOutputStream|FileReader|FileWriter)\(",
        "message": "[ThreadPolicy:UnbufferedIO] Direct use of unbuffered streams triggers excessive system calls (syscalls). Wrap in BufferedInputStream, BufferedOutputStream, BufferedReader, or BufferedWriter.",
        "severity": "MEDIUM",
    },
    "file_uri_exposure": {
        "regex": r"(Uri\.fromFile\(|file://)",
        "message": "[VmPolicy:FileUriExposure] Exposing raw file:// URIs across app boundaries triggers SecurityException on modern Android. Migrate to FileProvider content:// URIs.",
        "severity": "HIGH",
    },
    "cleartext_http": {
        "regex": r'"http://(?!localhost|127\.0\.0\.1|10\.0\.2\.2)[^"]+"',
        "message": "[VmPolicy:CleartextNetwork] Plaintext HTTP payloads expose user data to MITM sniffing. Enforce HTTPS.",
        "severity": "HIGH",
    },
    "unsafe_intent_sharing": {
        "regex": r"Intent\((Intent\.)?ACTION_SEND\)(?!\.apply\s*\{.*FLAG_GRANT_READ_URI_PERMISSION)",
        "message": "[VmPolicy:ContentUriWithoutPermission] Sharing content URIs without explicit FLAG_GRANT_READ_URI_PERMISSION blocks the target app from reading the file.",
        "severity": "MEDIUM",
    },
    "direct_boot_violation": {
        "regex": r"getSharedPreferences\(|openOrCreateDatabase\(",
        "message": "[VmPolicy:CredentialProtectedWhileLocked] Accessing standard storage during locked boot completed events fails. Use context.createDeviceProtectedStorageContext() inside Direct Boot aware components.",
        "severity": "HIGH",
    },
}


def scan_file(file_path):
    violations = []
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            for idx, line in enumerate(lines):
                # Skip commented lines
                trimmed = line.strip()
                if (
                    trimmed.startswith("//")
                    or trimmed.startswith("*")
                    or trimmed.startswith("/*")
                ):
                    continue

                # Check each violation pattern
                for name, rule in PATTERNS.items():
                    if re.search(rule["regex"], line):
                        # Filter out XML namespaces and schemas
                        if (
                            "schemas.android.com" in line
                            or "schemas.xmlsoap.org" in line
                        ):
                            continue
                        # Direct Boot requires context (skip general storage checks unless boot completion handler)
                        if (
                            name == "direct_boot_violation"
                            and "LOCKED_BOOT_COMPLETED" not in "".join(lines)
                        ):
                            continue

                        violations.append(
                            {
                                "line_num": idx + 1,
                                "line_content": trimmed,
                                "message": rule["message"],
                                "severity": rule["severity"],
                            }
                        )
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
    return violations


def main():
    if len(sys.argv) < 2:
        print("Usage: python scan_strictmode_violations.py <directory_path>")
        sys.exit(1)

    target_dir = sys.argv[1]
    if not os.path.isdir(target_dir):
        print(f"Error: Path '{target_dir}' is not a directory.")
        sys.exit(1)

    total_violations = 0
    print(f"Scanning '{target_dir}' for StrictMode violations...\n")

    for root, _, files in os.walk(target_dir):
        # Skip build and hidden directories
        if any(
            part in root.split(os.sep)
            for part in [".git", "build", "node_modules", ".gradle"]
        ):
            continue

        for file in files:
            if file.endswith((".kt", ".java", ".xml")):
                file_path = os.path.join(root, file)
                violations = scan_file(file_path)
                if violations:
                    print(f"\nFile: {file_path}")
                    for v in violations:
                        print(
                            f"  [{v['severity']}] Line {v['line_num']}: {v['message']}"
                        )
                        print(f"    Code: {v['line_content']}")
                        total_violations += 1

    print(f"\nScan completed. Total potential violations found: {total_violations}")
    if total_violations > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
