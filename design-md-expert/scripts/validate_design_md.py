#!/usr/bin/env python3
"""
DESIGN.md Validator

Checks DESIGN.md files for completeness, consistency, and best practices.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict

class DesignMDValidator:
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.content = ""
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        
    def validate(self) -> bool:
        """Run all validation checks. Returns True if valid."""
        if not self.filepath.exists():
            self.errors.append(f"File not found: {self.filepath}")
            return False
            
        self.content = self.filepath.read_text()
        
        # Run checks
        self._check_required_sections()
        self._check_color_palette()
        self._check_typography()
        self._check_spacing_system()
        self._check_component_rules()
        self._check_donts_section()
        self._check_accessibility()
        self._check_responsive_behavior()
        
        return len(self.errors) == 0
    
    def _check_required_sections(self):
        """Check for essential sections."""
        required = [
            ("Visual Theme / Overview", r"##\s*(?:Visual Theme|Overview)"),
            ("Color Palette", r"##\s*Color"),
            ("Typography", r"##\s*Typography"),
            ("Component", r"##\s*Component"),
            ("Layout", r"##\s*Layout|##\s*Spacing"),
            ("Don'ts", r"##\s*Don'?t|###\s*DON'?T|###\s*Don't"),
        ]
        
        for name, pattern in required:
            if not re.search(pattern, self.content, re.IGNORECASE):
                self.errors.append(f"Missing required section: {name}")
    
    def _check_color_palette(self):
        """Validate color definitions."""
        # Check for hex colors
        hex_colors = re.findall(r'#[0-9A-Fa-f]{6}', self.content)
        if len(hex_colors) < 5:
            self.warnings.append(f"Only {len(hex_colors)} hex colors found. Expected at least 5 (primary, surface, text, border, semantic)")
        
        # Check for semantic naming
        if not re.search(r'\bprimary\b', self.content, re.IGNORECASE):
            self.warnings.append("No 'primary' color token found. Use semantic names, not descriptive (e.g., 'primary' not 'blue-500')")
        
        # Check for contrast ratios
        if not re.search(r'\d+\.?\d*:\d+', self.content):
            self.warnings.append("No contrast ratios found. Include contrast ratios for accessibility (e.g., '4.5:1')")
        
        # Check for color roles/usage
        if not re.search(r'usage|role|use case', self.content, re.IGNORECASE):
            self.info.append("Consider adding 'Usage' or 'Role' column to color tables to explain when to use each color")
    
    def _check_typography(self):
        """Validate typography scale."""
        # Check for font sizes
        sizes = re.findall(r'\b(\d+)px\b', self.content)
        if len(sizes) < 4:
            self.warnings.append(f"Only {len(sizes)} font sizes found. Expected at least 4 (display, heading, body, caption)")
        
        # Check for font weights
        weights = re.findall(r'\b(regular|medium|semibold|bold|\d00)\b', self.content, re.IGNORECASE)
        if len(weights) < 3:
            self.warnings.append("Expected at least 3 font weights (Regular, Medium, Bold)")
        
        # Check for line heights
        if not re.search(r'line.?height', self.content, re.IGNORECASE):
            self.warnings.append("No line-height specifications found. Include line-height for each type scale")
        
        # Check for type scale table
        if not re.search(r'\|.*size.*weight.*line', self.content, re.IGNORECASE):
            self.info.append("Consider using a table format for typography scale (Size | Weight | Line Height | Use Case)")
    
    def _check_spacing_system(self):
        """Validate spacing/layout system."""
        # Check for spacing scale
        if not re.search(r'spacing|space-|layout', self.content, re.IGNORECASE):
            self.warnings.append("No spacing system found. Define spacing scale (e.g., 4px/8px base)")
        
        # Check for base unit
        if not re.search(r'\b[48]px\s+base', self.content, re.IGNORECASE):
            self.info.append("Consider specifying base spacing unit (4px or 8px)")
        
        # Check for grid system
        if not re.search(r'grid|column', self.content, re.IGNORECASE):
            self.info.append("Consider adding grid system specification (12-column, 16-column, etc.)")
    
    def _check_component_rules(self):
        """Validate component specifications."""
        components = ['button', 'input', 'card']
        found = sum(1 for c in components if re.search(rf'\b{c}\b', self.content, re.IGNORECASE))
        
        if found < 2:
            self.warnings.append(f"Only {found} common components found. Define at least: buttons, inputs, cards")
        
        # Check for component states
        if not re.search(r'hover|focus|active|disabled', self.content, re.IGNORECASE):
            self.warnings.append("No component states found. Define hover, focus, active, disabled states")
        
        # Check for touch targets
        if not re.search(r'44px|48px.*touch|min.?height.*44', self.content, re.IGNORECASE):
            self.info.append("Consider specifying minimum touch target size (44px or 48px)")
    
    def _check_donts_section(self):
        """Validate Don'ts section (critical for AI)."""
        if not re.search(r"don'?t|never|avoid", self.content, re.IGNORECASE):
            self.errors.append("No 'Don'ts' section found. This is CRITICAL for AI agents to avoid bad patterns")
            return
        
        # Count explicit negative constraint statements
        nevers = len(re.findall(r"\b(?:NEVER|never|don'?t|Don'?t)\b", self.content))
        if nevers < 3:
            self.warnings.append(f"Only {nevers} negative constraint statements found. Add more anti-patterns (e.g., 'NEVER use pure black', 'NEVER mix >2 typefaces')")
    
    def _check_accessibility(self):
        """Check for accessibility considerations."""
        a11y_keywords = ['accessibility', 'wcag', 'contrast', 'aria', 'screen reader', 'keyboard']
        found = sum(1 for kw in a11y_keywords if kw in self.content.lower())
        
        if found == 0:
            self.warnings.append("No accessibility considerations found. Include WCAG 2.2 AA requirements")
        elif found < 2:
            self.info.append("Limited accessibility guidance. Consider adding more (contrast ratios, keyboard nav, ARIA labels)")
    
    def _check_responsive_behavior(self):
        """Check for responsive/mobile specifications."""
        if not re.search(r'responsive|breakpoint|mobile|tablet|desktop', self.content, re.IGNORECASE):
            self.warnings.append("No responsive behavior specified. Define breakpoints and mobile adaptations")
        
        # Check for breakpoint values
        breakpoints = re.findall(r'\b(\d+)px\b.*(?:breakpoint|mobile|tablet|desktop)', self.content, re.IGNORECASE)
        if len(breakpoints) < 2:
            self.info.append("Consider defining specific breakpoint values (e.g., 768px, 1024px)")
    
    def print_report(self):
        """Print validation report."""
        print(f"\n{'='*60}")
        print(f"DESIGN.md Validation Report: {self.filepath.name}")
        print(f"{'='*60}\n")
        
        if self.errors:
            print(f"❌ ERRORS ({len(self.errors)}):")
            for err in self.errors:
                print(f"   • {err}")
            print()
        
        if self.warnings:
            print(f"⚠️  WARNINGS ({len(self.warnings)}):")
            for warn in self.warnings:
                print(f"   • {warn}")
            print()
        
        if self.info:
            print(f"ℹ️  SUGGESTIONS ({len(self.info)}):")
            for inf in self.info:
                print(f"   • {inf}")
            print()
        
        if not self.errors and not self.warnings:
            print("✅ All checks passed! DESIGN.md looks good.\n")
        elif not self.errors:
            print("✅ No critical errors. Address warnings for best practices.\n")
        else:
            print("❌ Validation failed. Fix errors before using with AI agents.\n")
        
        print(f"{'='*60}\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_design_md.py <path-to-DESIGN.md>")
        print("\nExample:")
        print("  python validate_design_md.py ./DESIGN.md")
        print("  python validate_design_md.py /path/to/project/DESIGN.md")
        sys.exit(1)
    
    filepath = sys.argv[1]
    validator = DesignMDValidator(filepath)
    
    is_valid = validator.validate()
    validator.print_report()
    
    sys.exit(0 if is_valid else 1)

if __name__ == "__main__":
    main()
