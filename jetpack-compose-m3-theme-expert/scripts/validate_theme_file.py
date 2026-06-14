#!/usr/bin/env python3
import os
import re
import sys


def log_error(msg):
    print(f"[\033[91mERROR\033[0m] {msg}")


def log_warn(msg):
    print(f"[\033[93mWARNING\033[0m] {msg}")


def log_ok(msg):
    print(f"[\033[92mOK\033[0m] {msg}")


def validate_design_md(file_path):
    if not os.path.exists(file_path):
        log_error(f"File not found: {file_path}")
        return False

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    errors = 0
    warnings = 0

    # 1. Check core sections
    required_sections = [
        "Theme & Atmosphere",
        "Color & Roles",
        "Typography",
        "Components",
        "Layout & Spacing",
        "Depth & Elevation",
        "Do's & Don'ts",
    ]

    print(f"Analyzing {os.path.basename(file_path)}...")
    for sec in required_sections:
        if not re.search(
            rf"^#+\s+{re.escape(sec)}", content, re.IGNORECASE | re.MULTILINE
        ):
            log_error(f"Missing required section: '{sec}'")
            errors += 1
        else:
            log_ok(f"Found section: '{sec}'")

    # 2. Extract Color tokens
    color_block = re.findall(
        r"(?:^#+\s+Color\s+&\s+Roles.*?)(?=^#+|$)",
        content,
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    if color_block:
        hex_colors = re.findall(r"#[0-9a-fA-F]{6}\b", color_block[0])
        log_ok(f"Parsed {len(hex_colors)} unique color tokens from Color & Roles.")
        # Check for true black (#000000)
        black_colors = [c for c in hex_colors if c.lower() == "#000000"]
        if black_colors:
            log_warn(
                "True black (#000000) found. Avoid true black for premium dark mode aesthetics (prefer dark navy/charcoal)."
            )
            warnings += 1
    else:
        log_warn("Could not isolate 'Color & Roles' content block for token parsing.")
        warnings += 1

    # 3. Check layout spacing grid (4px/8px rules)
    spacing_block = re.findall(
        r"(?:^#+\s+Layout\s+&\s+Spacing.*?)(?=^#+|$)",
        content,
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    if spacing_block:
        numbers = [int(n) for n in re.findall(r"\b\d+px\b", spacing_block[0])]
        off_grid = [n for n in numbers if n % 4 != 0]
        if off_grid:
            log_warn(
                f"Found off-grid spacing values (not multiples of 4px): {off_grid}"
            )
            warnings += 1
        else:
            log_ok("All extracted pixel spacings conform to the 4px/8px grid.")
    else:
        log_warn("Could not isolate 'Layout & Spacing' content block.")
        warnings += 1

    print("\n--- Validation Summary ---")
    if errors > 0:
        print(
            f"\033[91mValidation FAILED\033[0m with {errors} error(s) and {warnings} warning(s)."
        )
        return False
    else:
        print(f"\033[92mValidation PASSED\033[0m with {warnings} warning(s).")
        return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_theme_file.py <path/to/DESIGN.md>")
        sys.exit(1)
    success = validate_design_md(sys.argv[1])
    sys.exit(0 if success else 1)
