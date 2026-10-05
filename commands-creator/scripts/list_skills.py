#!/usr/bin/env python3
"""List installed skills (user, project, plugin) as `invoke-name<TAB>description` for routing.

Usage: list_skills.py [--project-dir DIR] [--filter WORD ...]
"""
import argparse
import json
import re
from pathlib import Path

HOME_CLAUDE = Path.home() / ".claude"
DESCRIPTION_MAX_CHARS = 160


def read_frontmatter(skill_file: Path) -> dict:
    text = skill_file.read_text(encoding="utf-8", errors="replace")
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    fields = {}
    field_match = re.search(r"^description:\s*(.+)$", match.group(1), re.MULTILINE)
    if field_match:
        fields["description"] = field_match.group(1).strip().strip("\"'")
    return fields


def collect_skills(skills_dir: Path, prefix: str = "") -> list:
    if not skills_dir.is_dir():
        return []
    entries = []
    for skill_file in sorted(skills_dir.glob("*/SKILL.md")):
        # Claude Code invokes skills by directory name; frontmatter `name` can differ.
        fields = read_frontmatter(skill_file)
        entries.append((prefix + skill_file.parent.name, fields.get("description", "")))
    return entries


def plugin_skill_dirs() -> list:
    registry = HOME_CLAUDE / "plugins" / "installed_plugins.json"
    if not registry.exists():
        return []
    plugins = json.loads(registry.read_text()).get("plugins", {})
    dirs = []
    for plugin_key, installs in plugins.items():
        plugin_name = plugin_key.split("@")[0]
        for install in installs:
            dirs.append((Path(install["installPath"]) / "skills", f"{plugin_name}:"))
    return dirs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--filter", nargs="*", default=[])
    args = parser.parse_args()

    entries = collect_skills(args.project_dir / ".claude" / "skills")
    entries += collect_skills(HOME_CLAUDE / "skills")
    for skills_dir, prefix in plugin_skill_dirs():
        entries += collect_skills(skills_dir, prefix)

    filter_words = [word.lower() for word in args.filter]
    seen_names = set()
    for name, description in entries:
        if name in seen_names:
            continue
        seen_names.add(name)
        haystack = f"{name} {description}".lower()
        if filter_words and not any(word in haystack for word in filter_words):
            continue
        print(f"{name}\t{description[:DESCRIPTION_MAX_CHARS]}")


if __name__ == "__main__":
    main()
