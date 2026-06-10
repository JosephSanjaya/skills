# Design System Assets

This directory contains example DESIGN.md files and templates that are NOT loaded into context automatically. These are reference materials for users to copy and adapt.

## Contents

### design-md-examples/

Real-world inspired DESIGN.md examples:

- **stripe-inspired.md**: Precision engineering, developer-focused, high trust
- **linear-inspired.md**: Speed, density, keyboard-first, dark mode

## Usage

These files are NOT loaded into Claude's context. They are:

1. **Reference materials** for users to study
2. **Starting templates** to copy and customize
3. **Examples** of different design philosophies

To use:
1. Copy an example file to your project root as `DESIGN.md`
2. Customize colors, typography, components
3. Test with AI agent
4. Validate with `scripts/validate_design_md.py`

## Why Not in Context?

Following caveman skill principles: only load what's needed. These examples are large and specific. Users access them when needed, not loaded by default.
