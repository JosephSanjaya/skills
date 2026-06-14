#!/usr/bin/env python3
"""Phase 1 static analysis: scans repo, outputs architecture JSON skeleton."""

import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

MANIFEST_PATTERNS = [
    "build.gradle",
    "build.gradle.kts",
    "package.json",
    "Cargo.toml",
    "pom.xml",
    "pyproject.toml",
    "go.mod",
]
ENTRY_POINT_PATTERNS = [
    "main.*",
    "Application.*",
    "AppDelegate.*",
    "MainActivity.*",
    "Program.*",
    "index.*",
    "app.*",
]
CONFIG_PATTERNS = [
    "*.yml",
    "*.yaml",
    "Dockerfile",
    "docker-compose.*",
    "*.env",
    "*.properties",
    "*.toml",
]
IGNORE_DIRS = {
    ".git",
    "node_modules",
    "build",
    ".gradle",
    "__pycache__",
    ".idea",
    "dist",
    "target",
    ".build",
}

LINE_THRESHOLD = 500
FUNCTION_THRESHOLD = 50
FUNCTION_PATTERN = re.compile(
    r"^\s*(fun |def |func |function |public |private |protected |async function )",
    re.MULTILINE,
)

# Android/Kotlin-specific entry points
ANDROID_ENTRY_POINT_PATTERNS = [
    "Application.kt",
    "Application.java",
    "MainActivity.kt",
    "MainActivity.java",
    "MainFragment.kt",
    "MainFragment.java",
    "NavGraph*.kt",
    "NavGraph*.xml",
    "*NavHost*.kt",
    "AppModule.kt",
    "di/*/Module.kt",
]

# Kotlin-specific scary patterns (additional signals)
KOTLIN_SCARY_PATTERNS = [
    re.compile(r"@Composable", re.MULTILINE),  # composable density
    re.compile(r"runBlocking", re.MULTILINE),  # blocking coroutine = smell
    re.compile(r"GlobalScope", re.MULTILINE),  # leaked coroutine scope
]


def detect_project_type(root: Path) -> str:
    indicators = {
        "android": ["AndroidManifest.xml", "app/src/main", "build.gradle"],
        "kotlin": ["build.gradle.kts", "settings.gradle.kts"],
        "node": ["package.json", "node_modules"],
        "python": ["pyproject.toml", "setup.py", "requirements.txt"],
        "rust": ["Cargo.toml"],
        "java": ["pom.xml", "build.gradle"],
        "go": ["go.mod"],
    }
    for project_type, files in indicators.items():
        if any((root / f).exists() for f in files):
            return project_type
    return "unknown"


def find_files_by_pattern(root: Path, pattern: str) -> list[str]:
    results = []
    try:
        for p in root.rglob(pattern):
            if not any(part in IGNORE_DIRS for part in p.parts):
                results.append(str(p.relative_to(root)))
    except Exception:  # noqa: S110
        pass
    return results


def find_entry_points(root: Path, project_type: str) -> list[str]:
    results = []
    for pattern in ENTRY_POINT_PATTERNS:
        results.extend(find_files_by_pattern(root, pattern))

    if project_type == "android":
        for pattern in ANDROID_ENTRY_POINT_PATTERNS:
            results.extend(find_files_by_pattern(root, pattern))
        # NavGraph XML is critical for Android
        for nav in root.rglob("navigation/*.xml"):
            if not any(part in IGNORE_DIRS for part in nav.parts):
                results.append(str(nav.relative_to(root)))

    return sorted(set(results))[:30]


def find_config_files(root: Path) -> list[str]:
    results = []
    for pattern in CONFIG_PATTERNS:
        results.extend(find_files_by_pattern(root, pattern))
    manifests = []
    for m in MANIFEST_PATTERNS:
        found = find_files_by_pattern(root, m)
        manifests.extend(found)
    return sorted(set(results + manifests))[:30]


def count_files_by_extension(root: Path) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for p in root.rglob("*"):
        if p.is_file() and not any(part in IGNORE_DIRS for part in p.parts):
            ext = p.suffix or "(no ext)"
            counts[ext] += 1
    return dict(sorted(counts.items(), key=lambda x: -x[1])[:20])


def detect_module_structure(root: Path) -> dict:
    structure: dict = {"modules": [], "build_system": "unknown"}

    if (root / "settings.gradle").exists() or (root / "settings.gradle.kts").exists():
        structure["build_system"] = "gradle"
        structure["has_settings_gradle"] = True
        settings_file = (
            root / "settings.gradle.kts"
            if (root / "settings.gradle.kts").exists()
            else root / "settings.gradle"
        )
        try:
            content = settings_file.read_text(errors="ignore")
            modules = re.findall(r'include\s*["\']([^"\']+)["\']', content)
            structure["modules"] = [m.lstrip(":") for m in modules]
        except Exception:  # noqa: S110
            pass

    elif (root / "package.json").exists():
        structure["build_system"] = "npm"
        workspace_files = list(root.glob("packages/*/package.json")) + list(
            root.glob("apps/*/package.json")
        )
        structure["modules"] = [
            str(p.parent.relative_to(root)) for p in workspace_files[:20]
        ]

    elif (root / "Cargo.toml").exists():
        structure["build_system"] = "cargo"
        workspace_members = list(root.glob("*/Cargo.toml"))
        structure["modules"] = [
            str(p.parent.relative_to(root)) for p in workspace_members[:20]
        ]

    if not structure["modules"]:
        top_dirs = [
            d.name for d in root.iterdir() if d.is_dir() and d.name not in IGNORE_DIRS
        ]
        structure["modules"] = sorted(top_dirs)[:15]

    return structure


def find_git_hot_files(root: Path, days: int = 90) -> list[dict]:
    """Files changed most in the last N days — highest volatility, most important to understand."""
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "log",
                f"--since={days} days ago",
                "--name-only",
                "--format=",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return []

        file_counts: dict[str, int] = defaultdict(int)
        for line in result.stdout.splitlines():
            line = line.strip()
            if line and not line.startswith("commit") and not line.startswith("Merge"):
                file_counts[line] += 1

        sorted_files = sorted(file_counts.items(), key=lambda x: -x[1])
        return [{"file": f, "commit_count": c} for f, c in sorted_files[:20]]
    except Exception:
        return []


def find_di_wiring(root: Path, project_type: str) -> list[str]:
    """Find DI registration points — critical for understanding object graph."""
    di_files = []

    if project_type in ("android", "kotlin"):
        # Koin modules
        for p in root.rglob("*.kt"):
            if any(part in IGNORE_DIRS for part in p.parts):
                continue
            try:
                content = p.read_text(errors="ignore")
                if "@Module" in content and (
                    "@ComponentScan" in content
                    or "startKoin" in content
                    or "val module = module" in content
                ):
                    di_files.append(str(p.relative_to(root)))
            except Exception:  # noqa: S112
                continue

    elif project_type in ("java",):
        for p in root.rglob("*.java"):
            if any(part in IGNORE_DIRS for part in p.parts):
                continue
            try:
                content = p.read_text(errors="ignore")
                if "@Configuration" in content or "@Bean" in content:
                    di_files.append(str(p.relative_to(root)))
            except Exception:  # noqa: S112
                continue

    return sorted(di_files)[:20]


def find_android_architecture_signals(root: Path) -> dict:
    """Detect Android architecture patterns: Clean Arch layers, navigation, compose usage."""
    signals = {
        "has_compose": False,
        "has_navigation_component": False,
        "has_hilt": False,
        "has_koin": False,
        "has_viewmodel": False,
        "has_room": False,
        "has_realm": False,
        "journey_modules": [],
        "capability_modules": [],
        "layer_structure": [],
    }

    all_gradle = list(root.rglob("*.gradle.kts")) + list(root.rglob("*.gradle"))

    for p in all_gradle:
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        try:
            content = p.read_text(errors="ignore")
            if "compose" in content.lower():
                signals["has_compose"] = True
            if "hilt" in content.lower():
                signals["has_hilt"] = True
            if "koin" in content.lower():
                signals["has_koin"] = True
            if "room" in content.lower():
                signals["has_room"] = True
            if "realm" in content.lower():
                signals["has_realm"] = True
            if "navigation" in content.lower():
                signals["has_navigation_component"] = True
        except Exception:  # noqa: S112
            continue

    # Detect journey/capability module naming convention
    for d in root.rglob("journey"):
        if d.is_dir() and not any(part in IGNORE_DIRS for part in d.parts):
            for sub in d.iterdir():
                if sub.is_dir():
                    signals["journey_modules"].append(sub.name)

    for d in root.rglob("capability"):
        if d.is_dir() and not any(part in IGNORE_DIRS for part in d.parts):
            for sub in d.iterdir():
                if sub.is_dir():
                    signals["capability_modules"].append(sub.name)

    # Detect layer structure from directory naming
    layer_keywords = {
        "domain",
        "data",
        "presentation",
        "ui",
        "remote",
        "bundle",
        "repository",
        "usecase",
        "network",
    }
    found_layers = set()
    for p in root.rglob("*"):
        if p.is_dir() and p.name.lower() in layer_keywords:
            found_layers.add(p.name.lower())
    signals["layer_structure"] = sorted(found_layers)

    return signals


def find_scary_sections(root: Path, project_type: str) -> list[dict]:
    scary = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        if p.suffix not in {
            ".kt",
            ".java",
            ".py",
            ".ts",
            ".tsx",
            ".js",
            ".swift",
            ".go",
            ".rs",
            ".cs",
            ".cpp",
        }:
            continue
        try:
            content = p.read_text(errors="ignore")
            lines = content.count("\n")
            func_count = len(FUNCTION_PATTERN.findall(content))

            entry: dict = {"file": str(p.relative_to(root))}
            reasons = []

            if lines > LINE_THRESHOLD:
                reasons.append(f"lines={lines}")
            if func_count > FUNCTION_THRESHOLD:
                reasons.append(f"functions={func_count}")

            if project_type in ("android", "kotlin"):
                for pattern in KOTLIN_SCARY_PATTERNS:
                    hits = len(pattern.findall(content))
                    if hits > 20:
                        reasons.append(f"{pattern.pattern}={hits}")

            if reasons:
                entry["reasons"] = reasons
                scary.append(entry)
        except Exception:  # noqa: S112
            continue

    return sorted(
        scary,
        key=lambda x: sum(
            int(r.split("=")[1]) for r in x.get("reasons", []) if "=" in r
        ),
        reverse=True,
    )[:20]


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    root = root.resolve()

    if not root.exists():
        print(f"Error: {root} does not exist", file=sys.stderr)
        sys.exit(1)

    project_type = detect_project_type(root)

    result = {
        "project_type": project_type,
        "entry_points": find_entry_points(root, project_type),
        "config_files": find_config_files(root),
        "module_structure": detect_module_structure(root),
        "file_counts": count_files_by_extension(root),
        "scary_sections": find_scary_sections(root, project_type),
        "git_hot_files": find_git_hot_files(root),
        "di_wiring": find_di_wiring(root, project_type),
    }

    if project_type == "android":
        result["android_signals"] = find_android_architecture_signals(root)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
