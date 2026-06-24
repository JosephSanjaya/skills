#!/usr/bin/env python3
"""Programmatic auditor for Claude Code subagent Markdown definitions.

Validates frontmatter parameters, naming, descriptions, and prompt structure.
Zero external dependencies. Fully typed.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class AuditResult:
    """Stores the results of a subagent audit."""

    def __init__(self, filepath: Path) -> None:
        self.filepath: Path = filepath
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_error(self, msg: str) -> None:
        """Adds a fatal validation error."""
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        """Adds a non-fatal warning or recommendation."""
        self.warnings.append(msg)

    @property
    def is_valid(self) -> bool:
        """Returns True if no errors were found."""
        return len(self.errors) == 0


def parse_yaml_frontmatter(content: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
    """Extracts and parses YAML frontmatter and body from markdown content.

    Returns:
        Tuple containing parsed dictionary, raw body text, and error message if any.
    """
    # Match the frontmatter block
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not match:
        return None, None, "Missing YAML frontmatter markers (---)"

    frontmatter_text = match.group(1)
    body_text = match.group(2).strip()
    parsed_data: Dict[str, Any] = {}

    # Parse simple YAML key-value pairs
    for line_num, line in enumerate(frontmatter_text.splitlines(), start=2):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Split on first colon
        if ":" not in line:
            return None, None, f"Invalid YAML syntax on line {line_num}: missing colon"

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        # Handle YAML array brackets
        if value.startswith("[") and value.endswith("]"):
            # Parse list of strings
            items = [item.strip().strip('"').strip("'") for item in value[1:-1].split(",")]
            parsed_data[key] = [i for i in items if i]
        elif value.startswith("-"):
            # Handle multi-line list (we assume basic parsing here)
            parsed_data.setdefault(key, [])
            item = value[1:].strip().strip('"').strip("'")
            if item:
                parsed_data[key].append(item)
        else:
            # Clean quotes
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            # Convert numeric values
            if value.isdigit():
                parsed_data[key] = int(value)
            elif value.lower() == "true":
                parsed_data[key] = True
            elif value.lower() == "false":
                parsed_data[key] = False
            else:
                parsed_data[key] = value

    return parsed_data, body_text, None


def audit_subagent(filepath: Path) -> AuditResult:
    """Performs static analysis checks on a subagent markdown definition."""
    result = AuditResult(filepath)

    if not filepath.exists():
        result.add_error(f"File not found: {filepath}")
        return result

    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as err:
        result.add_error(f"Failed to read file: {err}")
        return result

    frontmatter, body, parse_error = parse_yaml_frontmatter(content)
    if parse_error or frontmatter is None or body is None:
        result.add_error(f"Frontmatter parsing failed: {parse_error}")
        return result

    # 1. Validate 'name'
    if "name" not in frontmatter:
        result.add_error("Missing required field 'name' in frontmatter")
    else:
        name = str(frontmatter["name"]).strip()
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
            result.add_error(f"Name '{name}' must be lowercase kebab-case (e.g., 'security-auditor')")

    # 2. Validate 'description'
    if "description" not in frontmatter:
        result.add_error("Missing required field 'description' in frontmatter")
    else:
        desc = str(frontmatter["description"]).strip()
        if len(desc) < 20:
            result.add_error("Description is too short (must be >= 20 characters for accurate routing)")
        
        # Check for pushy trigger action words
        trigger_keywords = ["use", "trigger", "whenever", "agent", "focus", "analyze"]
        has_keywords = any(kw in desc.lower() for kw in trigger_keywords)
        if not has_keywords:
            result.add_warning("Description should be action-oriented and contain trigger keywords.")

    # 3. Validate 'tools'
    if "tools" in frontmatter:
        tools = frontmatter["tools"]
        if isinstance(tools, str):
            # Parse comma-separated string
            tools = [t.strip() for t in tools.split(",")]
        
        if not isinstance(tools, list):
            result.add_error("Field 'tools' must be a list or comma-separated string")
        else:
            # Check for nested spawning anti-pattern
            if "Agent" in tools:
                result.add_warning("Tool 'Agent' is allowed. Subagents cannot spawn nested subagents. Ensure this is intentional.")
            
            # Check for least privilege warnings
            read_only_indicators = ["review", "audit", "scan", "check", "detect", "read"]
            name_lower = filepath.stem.lower()
            is_read_only = any(ind in name_lower for ind in read_only_indicators)
            
            write_tools = ["Write", "Edit", "Bash"]
            has_write_tools = any(wt in tools for wt in write_tools)
            if is_read_only and has_write_tools:
                result.add_warning(
                    f"Read-only auditor agent '{filepath.name}' contains write permissions ({write_tools}). "
                    "Recommend stripping write tools for least-privilege security."
                )

    # 4. Validate 'model'
    if "model" in frontmatter:
        model = str(frontmatter["model"]).strip().lower()
        valid_models = ["opus", "sonnet", "haiku", "inherit"]
        if model not in valid_models:
            result.add_error(f"Invalid model '{model}'. Supported: {valid_models}")
    else:
        result.add_warning("No 'model' field specified. Defaults to parent context model.")

    # 5. Validate 'maxTurns'
    if "maxTurns" in frontmatter:
        try:
            max_turns = int(frontmatter["maxTurns"])
            if max_turns < 1 or max_turns > 30:
                result.add_error(f"maxTurns '{max_turns}' is outside safe bounds (1 to 30)")
            elif max_turns > 15:
                result.add_warning(f"maxTurns '{max_turns}' is high. Recommend 10-15 to prevent runaway token costs.")
        except ValueError:
            result.add_error("Field 'maxTurns' must be a valid integer")
    else:
        result.add_warning("No 'maxTurns' field specified. Recommend setting to 10-15 to prevent infinite loops.")

    # 6. Validate prompt body
    if not body:
        result.add_error("System prompt body is empty")
    else:
        lines = body.splitlines()
        if len(lines) < 3:
            result.add_warning("System prompt is very short. Ensure it defines role, scope, and output formats.")

    return result


def main() -> None:
    """Main CLI execution."""
    parser = argparse.ArgumentParser(description="Static analysis auditor for Claude Code subagent definitions.")
    parser.add_argument("file", type=str, help="Path to the subagent Markdown file to audit.")
    args = parser.parse_args()

    filepath = Path(args.file)
    result = audit_subagent(filepath)

    print(f"\nAuditing Subagent: {result.filepath.name}")
    print("=" * 40)

    if result.is_valid:
        print("\033[92mSUCCESS: Subagent configuration matches specifications.\033[0m")
    else:
        print(f"\033[91mFAILURE: Found {len(result.errors)} configuration errors:\033[0m")
        for idx, err in enumerate(result.errors, 1):
            print(f"  {idx}. [ERROR] {err}")

    if result.warnings:
        print(f"\nFound {len(result.warnings)} optimization recommendations:")
        for idx, warn in enumerate(result.warnings, 1):
            print(f"  {idx}. [WARNING] {warn}")

    print("=" * 40)
    print(f"Status: {'PASSED' if result.is_valid else 'FAILED'}\n")

    sys.exit(0 if result.is_valid else 1)


if __name__ == "__main__":
    main()
