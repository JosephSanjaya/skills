#!/usr/bin/env python3
"""
Analyze Dagger/Hilt modules for common issues and anti-patterns.

Usage:
    python analyze_modules.py <path_to_module_file>
    python analyze_modules.py <path_to_directory>  # Analyzes all .kt files
"""

import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Issue:
    severity: str  # "error", "warning", "info"
    line: int
    message: str
    suggestion: str | None = None


class ModuleAnalyzer:
    def __init__(self, content: str, filename: str):
        self.content = content
        self.filename = filename
        self.lines = content.split("\n")
        self.issues: list[Issue] = []

    def analyze(self) -> list[Issue]:
        """Run all analysis checks."""
        self.check_module_class_vs_object()
        self.check_provides_vs_binds()
        self.check_singleton_usage()
        self.check_module_size()
        self.check_static_provides()
        self.check_scope_consistency()
        return self.issues

    def check_module_class_vs_object(self):
        """Check if module is class instead of object/interface."""
        for i, line in enumerate(self.lines, 1):
            if "@Module" in line:
                # Look ahead for class/object declaration
                for j in range(i, min(i + 3, len(self.lines))):
                    if (
                        "class " in self.lines[j]
                        and "object " not in self.lines[j]
                        and "interface " not in self.lines[j]
                    ):
                        self.issues.append(
                            Issue(
                                severity="warning",
                                line=j + 1,
                                message="Module is a class instead of object/interface",
                                suggestion="Use 'object' for @Provides or 'interface' for @Binds to avoid module instantiation overhead",
                            )
                        )

    def check_provides_vs_binds(self):
        """Check for @Provides that could be @Binds."""
        for i, line in enumerate(self.lines, 1):
            if "@Provides" in line:
                # Look ahead for simple return statement
                for j in range(i, min(i + 5, len(self.lines))):
                    # Pattern: fun provideSomething(impl: SomeImpl): SomeInterface = impl
                    if re.search(
                        r"fun\s+\w+\([^)]+\):\s*\w+\s*=\s*\w+\s*$", self.lines[j]
                    ):
                        self.issues.append(
                            Issue(
                                severity="warning",
                                line=j + 1,
                                message="@Provides method simply returns parameter",
                                suggestion="Consider using @Binds instead for better performance",
                            )
                        )

    def check_singleton_usage(self):
        """Check for potentially inappropriate @Singleton usage."""
        feature_keywords = [
            "onboarding",
            "login",
            "signup",
            "checkout",
            "payment",
            "wizard",
            "tutorial",
        ]

        for i, line in enumerate(self.lines, 1):
            if "@Singleton" in line:
                # Look ahead for the function/class name
                for j in range(i, min(i + 3, len(self.lines))):
                    lower_line = self.lines[j].lower()
                    for keyword in feature_keywords:
                        if keyword in lower_line:
                            self.issues.append(
                                Issue(
                                    severity="warning",
                                    line=i,
                                    message=f"Feature-specific dependency '{keyword}' scoped as @Singleton",
                                    suggestion="Consider using @ActivityScoped or @ActivityRetainedScoped for feature-specific dependencies",
                                )
                            )
                            break

    def check_module_size(self):
        """Check if module has too many @Provides/@Binds methods."""
        provides_count = self.content.count("@Provides")
        binds_count = self.content.count("@Binds")
        total = provides_count + binds_count

        if total > 10:
            self.issues.append(
                Issue(
                    severity="info",
                    line=1,
                    message=f"Module has {total} provider methods (monolithic module)",
                    suggestion="Consider splitting into smaller, single-purpose modules for better maintainability and test isolation",
                )
            )

    def check_static_provides(self):
        """Check for non-static @Provides in object."""
        in_object = False
        for line in self.lines:
            if (
                "object " in line
                and "@Module" in self.content[: self.content.find(line)]
            ):
                in_object = True

            if in_object and "@Provides" in line:
                # Kotlin objects are already static, this is good
                pass

    def check_scope_consistency(self):
        """Check if scope matches component."""
        scope_to_component = {
            "@Singleton": "SingletonComponent",
            "@ActivityScoped": "ActivityComponent",
            "@ActivityRetainedScoped": "ActivityRetainedComponent",
            "@ViewModelScoped": "ViewModelComponent",
            "@FragmentScoped": "FragmentComponent",
        }

        install_in = None
        for line in self.lines:
            if "@InstallIn" in line:
                for component in scope_to_component.values():
                    if component in line:
                        install_in = component
                        break

        if install_in:
            expected_scope = [
                k for k, v in scope_to_component.items() if v == install_in
            ]
            for i, line in enumerate(self.lines, 1):
                for scope in scope_to_component.keys():
                    if scope in line and scope not in expected_scope:
                        self.issues.append(
                            Issue(
                                severity="error",
                                line=i,
                                message=f"Scope {scope} doesn't match @InstallIn({install_in})",
                                suggestion=f"Use {expected_scope[0] if expected_scope else 'appropriate scope'} for {install_in}",
                            )
                        )


def analyze_file(filepath: Path) -> list[Issue]:
    """Analyze a single Kotlin file."""
    try:
        content = filepath.read_text()
        if "@Module" not in content:
            return []

        analyzer = ModuleAnalyzer(content, filepath.name)
        return analyzer.analyze()
    except Exception as e:
        print(f"Error analyzing {filepath}: {e}", file=sys.stderr)
        return []


def print_issues(filepath: Path, issues: list[Issue]):
    """Print issues in a readable format."""
    if not issues:
        return

    print(f"\n📁 {filepath}")
    print("=" * 80)

    for issue in sorted(issues, key=lambda x: x.line):
        icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}[issue.severity]
        print(f"{icon} Line {issue.line}: {issue.message}")
        if issue.suggestion:
            print(f"   💡 {issue.suggestion}")
        print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    path = Path(sys.argv[1])

    if not path.exists():
        print(f"Error: {path} does not exist", file=sys.stderr)
        sys.exit(1)

    files_to_analyze = []
    if path.is_file():
        files_to_analyze = [path]
    else:
        files_to_analyze = list(path.rglob("*.kt"))

    total_issues = 0
    for filepath in files_to_analyze:
        issues = analyze_file(filepath)
        if issues:
            print_issues(filepath, issues)
            total_issues += len(issues)

    print(f"\n{'=' * 80}")
    print(f"Total issues found: {total_issues}")

    if total_issues == 0:
        print("✅ No issues found!")


if __name__ == "__main__":
    main()
