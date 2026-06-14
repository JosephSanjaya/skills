#!/usr/bin/env python3
"""
Interactive DESIGN.md Generator

Guides user through creating a complete DESIGN.md file.
"""

import sys
from pathlib import Path


class DesignMDGenerator:
    def __init__(self):
        self.data: dict = {}

    def prompt(self, question: str, default: str = "") -> str:
        """Prompt user for input with optional default."""
        if default:
            response = input(f"{question} [{default}]: ").strip()
            return response if response else default
        return input(f"{question}: ").strip()

    def prompt_list(self, question: str, min_items: int = 1) -> list[str]:
        """Prompt for multiple items."""
        print(f"\n{question}")
        print("(Enter items one per line, empty line to finish)")
        items = []
        while True:
            item = input(f"  {len(items) + 1}. ").strip()
            if not item:
                if len(items) >= min_items:
                    break
                print(f"  (Need at least {min_items} item(s))")
                continue
            items.append(item)
        return items

    def generate(self) -> str:
        """Interactive generation process."""
        print("\n" + "=" * 60)
        print("DESIGN.md Interactive Generator")
        print("=" * 60)
        print("\nThis will guide you through creating a complete DESIGN.md file.")
        print("Press Ctrl+C at any time to cancel.\n")

        # Project info
        print("\n--- PROJECT INFO ---")
        self.data["project_name"] = self.prompt("Project name")
        self.data["philosophy"] = self.prompt("Design philosophy (1-2 sentences)")
        self.data["density"] = self.prompt("Density level", "Medium")
        self.data["personality"] = self.prompt(
            "Personality (3-5 adjectives)", "Professional, Modern, Clean"
        )

        # Colors
        print("\n--- COLOR PALETTE ---")
        self.data["primary"] = self.prompt("Primary color (hex)", "#1A73E8")
        self.data["surface"] = self.prompt("Surface/background color (hex)", "#FFFFFF")
        self.data["text"] = self.prompt("Primary text color (hex)", "#1A1C1E")
        self.data["border"] = self.prompt("Border color (hex)", "#DADCE0")
        self.data["success"] = self.prompt("Success color (hex)", "#137333")
        self.data["warning"] = self.prompt("Warning color (hex)", "#B06000")
        self.data["error"] = self.prompt("Error color (hex)", "#C5221F")

        # Typography
        print("\n--- TYPOGRAPHY ---")
        self.data["font_primary"] = self.prompt("Primary font family", "Inter")
        self.data["font_mono"] = self.prompt("Monospace font family", "SF Mono")
        self.data["base_size"] = self.prompt("Base font size (px)", "16")

        # Spacing
        print("\n--- SPACING ---")
        self.data["spacing_base"] = self.prompt("Spacing base unit (4 or 8)", "8")

        # Components
        print("\n--- COMPONENTS ---")
        self.data["button_radius"] = self.prompt("Button border-radius (px)", "4")
        self.data["card_radius"] = self.prompt("Card border-radius (px)", "8")

        # Don'ts
        print("\n--- DON'TS (Critical for AI) ---")
        self.data["donts"] = self.prompt_list("What should AI NEVER do?", min_items=3)

        # Responsive
        print("\n--- RESPONSIVE ---")
        self.data["breakpoint_mobile"] = self.prompt("Mobile breakpoint (px)", "768")
        self.data["breakpoint_tablet"] = self.prompt("Tablet breakpoint (px)", "1024")

        return self._build_markdown()

    def _build_markdown(self) -> str:
        """Build DESIGN.md content from collected data."""
        md = f"""# {self.data["project_name"]} Design System

## Visual Theme & Atmosphere

**Philosophy**: {self.data["philosophy"]}

**Density**: {self.data["density"]}

**Personality**: {self.data["personality"]}

---

## Color Palette & Roles

### Primary Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `primary` | {self.data["primary"]} | Primary actions, brand moments, CTAs |
| `primary-hover` | {self._darken_hex(self.data["primary"], 10)} | Hover state for primary elements |

### Surface Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `surface` | {self.data["surface"]} | Default background |
| `surface-elevated` | {self._lighten_hex(self.data["surface"], 3)} | Cards, modals, elevated surfaces |

### Text Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `on-surface` | {self.data["text"]} | Primary text |
| `on-surface-secondary` | {self._lighten_hex(self.data["text"], 30)} | Secondary text, labels |

### Semantic Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `success` | {self.data["success"]} | Success states, confirmations |
| `warning` | {self.data["warning"]} | Warnings, caution states |
| `error` | {self.data["error"]} | Errors, destructive actions |

### Border & Divider

| Token | Hex | Usage |
|-------|-----|-------|
| `border` | {self.data["border"]} | Default borders |

---

## Typography Rules

### Font Families

```css
--font-primary: '{self.data["font_primary"]}', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-mono: '{self.data["font_mono"]}', 'Monaco', 'Inconsolata', monospace;
```

### Type Scale

| Scale | Size | Weight | Line Height | Use Case |
|-------|------|--------|-------------|----------|
| `display` | 48px | Bold | 1.1 | Hero headlines |
| `h1` | 32px | Bold | 1.2 | Page titles |
| `h2` | 24px | Semibold | 1.3 | Section headers |
| `h3` | 20px | Semibold | 1.4 | Subsection headers |
| `body` | {self.data["base_size"]}px | Regular | 1.5 | Default paragraph text |
| `body-small` | 14px | Regular | 1.4 | Secondary text |
| `caption` | 12px | Regular | 1.4 | Metadata, labels |

---

## Component Stylings

### Buttons

#### Primary Button
```
Background: {self.data["primary"]}
Text: #FFFFFF
Padding: 12px 24px
Border-radius: {self.data["button_radius"]}px
Min-height: 44px (touch target)

States:
- Hover: {self._darken_hex(self.data["primary"], 10)}
- Focus: 2px outline {self.data["primary"]} + 2px offset
```

### Cards

```
Background: {self._lighten_hex(self.data["surface"], 3)}
Border: 1px solid {self.data["border"]}
Border-radius: {self.data["card_radius"]}px
Padding: 16px
```

---

## Layout Principles

### Spacing System

**Base**: {self.data["spacing_base"]}px

| Token | Value | Usage |
|-------|-------|-------|
| `space-xs` | {int(self.data["spacing_base"]) // 2}px | Tight inline spacing |
| `space-sm` | {self.data["spacing_base"]}px | Component internal padding |
| `space-md` | {int(self.data["spacing_base"]) * 2}px | Between related elements |
| `space-lg` | {int(self.data["spacing_base"]) * 3}px | Between sections |
| `space-xl` | {int(self.data["spacing_base"]) * 4}px | Major layout gaps |

---

## Do's and Don'ts

### DON'T
"""
        for dont in self.data["donts"]:
            md += f"- ❌ NEVER {dont}\n"

        md += f"""
---

## Responsive Behavior

### Breakpoints

```css
--breakpoint-mobile: {self.data["breakpoint_mobile"]}px;
--breakpoint-tablet: {self.data["breakpoint_tablet"]}px;
```

### Touch Targets

- **Minimum**: 44x44 CSS pixels
- **Recommended**: 48x48 CSS pixels

---

## Agent Prompt Guide

### Quick Color Reference

```
Primary: {self.data["primary"]}
Background: {self.data["surface"]}
Text: {self.data["text"]}
Border: {self.data["border"]}
Success: {self.data["success"]}
Error: {self.data["error"]}
```

---

## Version History

- **v1.0.0** ({self._get_date()}): Initial design system specification
"""
        return md

    def _darken_hex(self, hex_color: str, percent: int) -> str:
        """Darken hex color by percent (simple approximation)."""
        hex_color = hex_color.lstrip("#")
        r, g, b = (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16),
        )
        factor = 1 - (percent / 100)
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _lighten_hex(self, hex_color: str, percent: int) -> str:
        """Lighten hex color by percent (simple approximation)."""
        hex_color = hex_color.lstrip("#")
        r, g, b = (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16),
        )
        factor = percent / 100
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _get_date(self) -> str:
        """Get current date in YYYY-MM-DD format."""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d")

    def save(self, content: str, output_path: str):
        """Save generated DESIGN.md to file."""
        path = Path(output_path)
        path.write_text(content)
        print("\n✅ DESIGN.md generated successfully!")
        print(f"   Saved to: {path.absolute()}")
        print("\nNext steps:")
        print("  1. Review and customize the generated file")
        print("  2. Add more component specifications")
        print("  3. Test with AI agent: generate a sample component")
        print(f"  4. Validate: python validate_design_md.py {output_path}")
        print()


def main():
    output_path = "DESIGN.md"
    if len(sys.argv) > 1:
        output_path = sys.argv[1]

    generator = DesignMDGenerator()

    try:
        content = generator.generate()
        generator.save(content, output_path)
    except KeyboardInterrupt:
        print("\n\n❌ Generation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
