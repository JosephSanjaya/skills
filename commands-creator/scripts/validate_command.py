#!/usr/bin/env python3
"""Lint a Claude Code command file against the commands-creator contract.

Usage: validate_command.py <command.md> [--project-dir DIR]
Exit 0 = pass (warnings allowed), 1 = errors found.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

KNOWN_FIELDS = {
    "description", "when_to_use", "argument-hint", "arguments", "allowed-tools",
    "disable-model-invocation", "user-invocable", "model", "effort", "context",
    "agent", "hooks",
}
MAX_BODY_LINES = 80
MAX_DESCRIPTION_CHARS = 200
SIDE_EFFECT_PATTERN = re.compile(
    r"\b(git push|git commit|git reset --hard|(gh|glab) (pr|mr) (merge|create)|npm publish|kubectl apply|"
    r"terraform apply|rm -rf|DROP TABLE|send_message|create_merge_request|merge_merge_request)\b",
    re.IGNORECASE,
)
# Built-in skills ship inside Claude Code, so they never appear on disk.
BUILTIN_SKILLS = {"code-review", "simplify", "security-review", "init", "review", "run", "loop", "claude-api"}
SKILL_REFERENCE_PATTERN = re.compile(r"Skill `([\w:.-]+)`")


def split_frontmatter(text: str):
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    if not match:
        return None, text
    fields = {}
    for line in match.group(1).splitlines():
        field_match = re.match(r"^([\w-]+):\s*(.*)$", line)
        if field_match:
            fields[field_match.group(1)] = field_match.group(2).strip()
    return fields, match.group(2)


def installed_skill_names(project_dir: Path) -> set:
    lister = Path(__file__).with_name("list_skills.py")
    output = subprocess.run(
        [sys.executable, str(lister), "--project-dir", str(project_dir)],
        capture_output=True, text=True, check=True,
    ).stdout
    return {line.split("\t")[0] for line in output.splitlines() if line}


def check_frontmatter(fields: dict, body: str, errors: list, warnings: list):
    unknown_fields = set(fields) - KNOWN_FIELDS
    if unknown_fields:
        errors.append(f"unknown frontmatter fields (silently ignored by Claude Code): {sorted(unknown_fields)}")
    description = fields.get("description", "")
    if not description:
        errors.append("missing description")
    elif len(description) > MAX_DESCRIPTION_CHARS:
        warnings.append(f"description {len(description)} chars > {MAX_DESCRIPTION_CHARS}")
    uses_arguments = re.search(r"\$(ARGUMENTS|\d)", body)
    if uses_arguments and "argument-hint" not in fields:
        errors.append("body uses $ARGUMENTS/$N but no argument-hint")
    if "argument-hint" in fields and not uses_arguments:
        warnings.append("argument-hint set but body never reads $ARGUMENTS")
    if re.search(r"!`|```!", body) and "allowed-tools" not in fields:
        errors.append("shell injection (!`cmd`) used without allowed-tools")
    if SIDE_EFFECT_PATTERN.search(body) and fields.get("disable-model-invocation") != "true":
        warnings.append("side-effecting command without disable-model-invocation: true")


def check_body(body: str, errors: list, warnings: list):
    body_lines = body.strip().splitlines()
    if len(body_lines) > MAX_BODY_LINES:
        warnings.append(f"body {len(body_lines)} lines > {MAX_BODY_LINES}; move detail into a skill")
    for tag in ("<instructions>", "<output>"):
        if tag not in body:
            errors.append(f"missing {tag} block")
    if not re.search(r'<step id="1"', body):
        errors.append('missing <step id="1" ...> block')


def check_skill_references(body: str, project_dir: Path, errors: list):
    referenced_skills = set(SKILL_REFERENCE_PATTERN.findall(body))
    if not referenced_skills:
        return
    missing_skills = referenced_skills - installed_skill_names(project_dir) - BUILTIN_SKILLS
    if missing_skills:
        errors.append(f"referenced skills not installed: {sorted(missing_skills)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command_file", type=Path)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()

    fields, body = split_frontmatter(args.command_file.read_text(encoding="utf-8"))
    errors, warnings = [], []
    if fields is None:
        errors.append("frontmatter missing or '---' not on first line")
        fields = {}
    check_frontmatter(fields, body, errors, warnings)
    check_body(body, errors, warnings)
    check_skill_references(body, args.project_dir, errors)

    for message in errors:
        print(f"ERROR: {message}")
    for message in warnings:
        print(f"WARN: {message}")
    print("PASS" if not errors else "FAIL")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
