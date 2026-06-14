#!/usr/bin/env python3
import os
import re
import sys


def print_err(text):
    print(f"\033[91m[ERROR] {text}\033[0m")


def print_warn(text):
    print(f"\033[93m[WARN]  {text}\033[0m")


def print_ok(text):
    print(f"\033[92m[OK]    {text}\033[0m")


def check_gradle_file(gradle_path):
    if not os.path.exists(gradle_path):
        print_warn(
            f"build.gradle.kts not found at {gradle_path}. Skipping Gradle validation."
        )
        return True

    with open(gradle_path, encoding="utf-8") as f:
        content = f.read()

    # Search for detekt-api dependency
    api_dep_match = re.search(
        r'(implementation|compileOnly|api)\s*\(\s*["\'](.*detekt-api.*)["\']\s*\)',
        content,
    )
    if not api_dep_match:
        api_dep_match = re.search(r'["\'](.*detekt-api.*)["\']', content)
        if api_dep_match:
            print_warn(
                "Found detekt-api dependency but could not determine scope (e.g., compileOnly)."
            )
        else:
            print_warn("detekt-api dependency not found in build.gradle.kts.")
        return True

    scope, dep = api_dep_match.groups()
    if scope != "compileOnly":
        print_err(
            f"detekt-api dependency is declared as '{scope}' in {gradle_path}. It MUST be 'compileOnly' to avoid runtime classloader conflicts."
        )
        return False

    print_ok("detekt-api is correctly declared as compileOnly.")
    return True


def check_serviceloader(project_root):
    resources_path = os.path.join(
        project_root, "src", "main", "resources", "META-INF", "services"
    )
    if not os.path.exists(resources_path):
        print_err(f"ServiceLoader directory not found at: {resources_path}")
        return False

    v1_service = "io.gitlab.arturbosch.detekt.api.RuleSetProvider"
    v2_service = "dev.detekt.api.RuleSetProvider"

    v1_exists = os.path.exists(os.path.join(resources_path, v1_service))
    v2_exists = os.path.exists(os.path.join(resources_path, v2_service))

    if not v1_exists and not v2_exists:
        print_err(
            f"Missing ServiceLoader provider file. Create either:\n - {os.path.join(resources_path, v1_service)} (for Detekt 1.x)\n - {os.path.join(resources_path, v2_service)} (for Detekt 2.x)"
        )
        return False

    if v1_exists:
        print_ok(f"Found Detekt 1.x ServiceLoader: {v1_service}")
        with open(os.path.join(resources_path, v1_service)) as f:
            content = f.read().strip()
            print_ok(f" Registered provider: {content}")

    if v2_exists:
        print_ok(f"Found Detekt 2.x ServiceLoader: {v2_service}")
        with open(os.path.join(resources_path, v2_service)) as f:
            content = f.read().strip()
            print_ok(f" Registered provider: {content}")

    return True


def check_detekt_yml(yml_path):
    if not os.path.exists(yml_path):
        print_warn(f"detekt.yml not found at {yml_path}. Skipping YAML validation.")
        return True

    with open(yml_path, encoding="utf-8") as f:
        lines = f.readlines()

    validation_enabled = False
    excludes_configured = False
    in_config_block = False

    for line in lines:
        stripped = line.strip()
        if stripped == "config:":
            in_config_block = True
            continue

        if in_config_block:
            # Check indentation to see if we left the config block
            if line.startswith(" ") or line.startswith("\t"):
                if stripped.startswith("validation:"):
                    val = stripped.split(":", 1)[1].strip().lower()
                    if val == "true":
                        validation_enabled = True
                elif stripped.startswith("excludes:"):
                    excludes_configured = True
            else:
                in_config_block = False

    if validation_enabled and not excludes_configured:
        print_warn(
            "config.validation is set to true in detekt.yml but no config.excludes is declared. Custom rule properties will fail build validation unless excluded."
        )
    elif validation_enabled and excludes_configured:
        print_ok(
            "config.validation and config.excludes are both present in detekt.yml."
        )
    else:
        print_ok(
            "config.validation is disabled or default. No exclude validation rules required."
        )

    return True


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python3 check_detekt_setup.py <path_to_rules_project_root> [path_to_detekt_yml]"
        )
        sys.exit(1)

    project_root = sys.argv[1]
    yml_path = (
        sys.argv[2]
        if len(sys.argv) > 2
        else os.path.join(project_root, "config", "detekt.yml")
    )

    print(f"=== Auditing Detekt Setup: {project_root} ===")

    success = True
    success &= check_gradle_file(os.path.join(project_root, "build.gradle.kts"))
    success &= check_serviceloader(project_root)
    success &= check_detekt_yml(yml_path)

    if success:
        print_ok("=== Audit Completed: No critical errors found ===")
        sys.exit(0)
    else:
        print_err("=== Audit Completed: Critical configuration errors found ===")
        sys.exit(1)


if __name__ == "__main__":
    main()
