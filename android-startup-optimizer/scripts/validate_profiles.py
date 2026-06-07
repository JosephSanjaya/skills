#!/usr/bin/env python3
"""
Validate Baseline and Startup Profiles.

Usage:
    python validate_profiles.py <path-to-app-module>

Checks:
- Profile files exist
- Profile syntax is valid
- Profiles are included in APK
- Profile coverage is adequate
"""

import sys
import re
import zipfile
from pathlib import Path
from typing import List, Tuple, Set

class ProfileValidator:
    def __init__(self, app_path: str):
        self.app_path = Path(app_path)
        if not self.app_path.exists():
            raise FileNotFoundError(f"App module not found: {app_path}")
        
        self.baseline_profile = self.app_path / "src/main/baseline-prof.txt"
        self.startup_profile = self.app_path / "src/main/startup-prof.txt"
        self.release_apk = self._find_release_apk()
    
    def _find_release_apk(self) -> Path:
        """Find the release APK."""
        apk_dir = self.app_path / "build/outputs/apk/release"
        if not apk_dir.exists():
            return None
        
        apks = list(apk_dir.glob("*.apk"))
        if not apks:
            return None
        
        return apks[0]
    
    def validate(self):
        """Run all validations."""
        print("=" * 80)
        print("PROFILE VALIDATION")
        print("=" * 80)
        print()
        
        baseline_valid = self._validate_baseline_profile()
        startup_valid = self._validate_startup_profile()
        apk_valid = self._validate_apk_profiles()
        
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        if baseline_valid and startup_valid and apk_valid:
            print("✓ All validations passed!")
        else:
            print("⚠️  Some validations failed. See details above.")
            sys.exit(1)
    
    def _validate_baseline_profile(self) -> bool:
        """Validate Baseline Profile."""
        print("Baseline Profile")
        print("-" * 80)
        
        if not self.baseline_profile.exists():
            print("  ✗ baseline-prof.txt not found")
            print(f"    Expected: {self.baseline_profile}")
            print()
            return False
        
        content = self.baseline_profile.read_text()
        lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#')]
        
        if not lines:
            print("  ✗ Profile is empty")
            print()
            return False
        
        # Validate syntax
        class_pattern = re.compile(r'^L[\w/$]+;$')
        method_pattern = re.compile(r'^L[\w/$]+;->.+$')
        
        invalid_lines = []
        classes = set()
        methods = set()
        
        for i, line in enumerate(lines, 1):
            if class_pattern.match(line):
                classes.add(line)
            elif method_pattern.match(line):
                methods.add(line)
            else:
                invalid_lines.append((i, line))
        
        if invalid_lines:
            print(f"  ✗ Invalid syntax found:")
            for line_num, line in invalid_lines[:5]:
                print(f"    Line {line_num}: {line}")
            if len(invalid_lines) > 5:
                print(f"    ... and {len(invalid_lines) - 5} more")
            print()
            return False
        
        print(f"  ✓ Syntax valid")
        print(f"  ✓ {len(classes)} classes")
        print(f"  ✓ {len(methods)} methods")
        
        # Check for critical classes
        critical_classes = [
            'Application',
            'MainActivity',
            'AppModule',
            'AppComponent'
        ]
        
        found_critical = []
        for cls in critical_classes:
            if any(cls in line for line in classes):
                found_critical.append(cls)
        
        if found_critical:
            print(f"  ✓ Found critical classes: {', '.join(found_critical)}")
        else:
            print(f"  ⚠️  No critical classes found (Application, MainActivity, etc.)")
        
        print()
        return True
    
    def _validate_startup_profile(self) -> bool:
        """Validate Startup Profile."""
        print("Startup Profile")
        print("-" * 80)
        
        if not self.startup_profile.exists():
            print("  ⚠️  startup-prof.txt not found (optional)")
            print(f"    Expected: {self.startup_profile}")
            print("    Startup Profiles provide additional 15-30% improvement")
            print()
            return True  # Optional, so not a failure
        
        content = self.startup_profile.read_text()
        lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#')]
        
        if not lines:
            print("  ✗ Profile is empty")
            print()
            return False
        
        # Validate syntax (should only contain class descriptors)
        class_pattern = re.compile(r'^L[\w/$]+;$')
        
        invalid_lines = []
        classes = set()
        
        for i, line in enumerate(lines, 1):
            if class_pattern.match(line):
                classes.add(line)
            else:
                invalid_lines.append((i, line))
        
        if invalid_lines:
            print(f"  ✗ Invalid syntax found:")
            for line_num, line in invalid_lines[:5]:
                print(f"    Line {line_num}: {line}")
            print()
            return False
        
        print(f"  ✓ Syntax valid")
        print(f"  ✓ {len(classes)} classes")
        
        # Check size
        if len(classes) > 500:
            print(f"  ⚠️  Profile is large ({len(classes)} classes)")
            print("    Consider reducing to only first-screen classes")
            print("    Large profiles may overflow primary DEX file")
        else:
            print(f"  ✓ Profile size is reasonable")
        
        print()
        return True
    
    def _validate_apk_profiles(self) -> bool:
        """Validate profiles in APK."""
        print("APK Profile Validation")
        print("-" * 80)
        
        if not self.release_apk:
            print("  ⚠️  Release APK not found")
            print("    Build release APK first: ./gradlew :app:assembleRelease")
            print()
            return True  # Not a failure if APK doesn't exist yet
        
        print(f"  Checking: {self.release_apk.name}")
        
        try:
            with zipfile.ZipFile(self.release_apk, 'r') as apk:
                files = apk.namelist()
                
                # Check for baseline profile
                baseline_files = [f for f in files if 'baseline' in f.lower()]
                if baseline_files:
                    print(f"  ✓ Baseline profile found:")
                    for f in baseline_files:
                        size = apk.getinfo(f).file_size
                        print(f"    - {f} ({size} bytes)")
                else:
                    print(f"  ✗ Baseline profile not found in APK")
                    print("    Profile may not be applied at runtime")
                    return False
                
                # Check for startup profile
                startup_files = [f for f in files if 'startup' in f.lower()]
                if startup_files:
                    print(f"  ✓ Startup profile found:")
                    for f in startup_files:
                        size = apk.getinfo(f).file_size
                        print(f"    - {f} ({size} bytes)")
                else:
                    print(f"  ⚠️  Startup profile not found in APK (optional)")
                
                # Check DEX files
                dex_files = [f for f in files if f.endswith('.dex')]
                print(f"  ✓ DEX files: {len(dex_files)}")
                for dex in sorted(dex_files):
                    size = apk.getinfo(dex).file_size / (1024 * 1024)
                    print(f"    - {dex} ({size:.2f} MB)")
                
        except Exception as e:
            print(f"  ✗ Error reading APK: {e}")
            return False
        
        print()
        return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_profiles.py <path-to-app-module>")
        print()
        print("Example:")
        print("  python validate_profiles.py app")
        print("  python validate_profiles.py /path/to/project/app")
        sys.exit(1)
    
    app_path = sys.argv[1]
    
    try:
        validator = ProfileValidator(app_path)
        validator.validate()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
