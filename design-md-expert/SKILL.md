---
name: design-md-expert
description: "Expert guidance for creating, optimizing, and implementing unified Web and Mobile DESIGN.md files. Make sure to use this skill whenever the user mentions design systems, design-md, UI/UX consistency, visual theme, design handoff to AI, Stripe/Linear/VoltAgent styles, dashboard layouts, mobile touch targets, safe areas, Jetpack Compose, SwiftUI, WCAG 2.2 AA accessibility, or when coding agents generate inconsistent frontend styles."
---

# DESIGN.md Expert (Unified Web & Mobile)

Expert for creating machine-readable design systems enabling AI agents to generate brand-consistent, professional UI across web and mobile platforms. This skill conforms to the official Google `design.md` format specification (YAML tokens + Markdown prose) and extends it with native mobile (Android Compose, iOS SwiftUI) design paradigms, safe areas, and touch target constraints.

<instructions>
Enforce the official Google `design.md` format while preserving native mobile platform guidelines. Combine YAML front matter (design tokens) with 8 canonical markdown body sections. Enforce semantic token naming, token referencing, and platform-agnostic layouts. Align typography and spacing to 4px/8px grids. Conform to WCAG 2.2 AA accessibility, iOS HIG, and Android Material Design 3 guidelines.
</instructions>

## 1. Unified Token Schema (YAML Front Matter)

Tokens are defined in the YAML front matter. Design tokens must be platform-agnostic so they can be exported to Web (Tailwind, CSS) and mapped to Mobile (Jetpack Compose, SwiftUI).

```yaml
version: alpha
name: Unified Core
colors:
  primary: "#1A1C1E"              # Maps to MaterialTheme.colorScheme.primary / Color("Primary")
  on-primary: "#FFFFFF"
  secondary: "#0058BE"
  on-secondary: "#FFFFFF"
  surface: "#F9F9FF"              # Maps to MaterialTheme.colorScheme.surface
  on-surface: "#151C27"
  surface-container: "#E7EEFE"    # M3 Surface Container / iOS elevated background
  outline: "#867461"              # Borders / dividers
typography:
  headline-lg:
    fontFamily: Plus Jakarta Sans # Web font / mapped to custom font on iOS/Android
    fontSize: 32px
    fontWeight: "700"
    lineHeight: 40px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: "400"
    lineHeight: 24px
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: "600"
    lineHeight: 16px
rounded:
  sm: 4px                         # M3 Extra Small / iOS Button
  DEFAULT: 8px                    # M3 Small
  lg: 12px                        # M3 Medium / iOS Card
  xl: 16px                        # M3 Large
  full: 9999px
spacing:
  unit: 8px                       # Base 8dp grid unit
  safe-area-bottom: 34px          # iOS home indicator safe area / Android system nav bar
  touch-target: 48px              # Minimum interactive dimension
```

## 2. Canonical Markdown Sections (Enriched for Web & Mobile)

Sections must appear in this exact order to satisfy the Google parser while addressing both platforms:

### 1. Overview (or "Brand & Style")
- **Atmosphere**: Define the brand personality, density (high-density desktop dashboard vs. spacious mobile feed), and emotional response.
- **Multi-platform Philosophy**: Explain how the brand theme translates across form factors (e.g., fluid glassmorphism on web, soft containerization on mobile).

### 2. Colors
- **Semantic Roles**: Rationale for `primary`, `secondary`, `tertiary`, and `neutral` palettes.
- **Contrast**: Enforce WCAG 2.2 AA contrast ratios (4.5:1 for normal text, 3:1 for UI components).

### 3. Typography
- **Font Strategy**: Pairing rules (e.g., sans-serif for body, geometric/technical for headers).
- **Scale Adaptation**: Rules for scaling fonts between desktop and mobile (e.g., reducing display text size by 20-30% on mobile screens while maintaining line-height ratios).
- **Dynamic Type**: Address system text scaling on iOS and Android.

### 4. Layout (or "Layout & Spacing")
- **Web Layout**: 12-column grid systems, gutters, max-widths, and desktop margins.
- **Mobile Layout**: Safe Area Insets (status bar, notch, home indicator), column spans (typically 4 columns on mobile), and navigation zones (top app bars, bottom navigation bars).
- **Spacing Scale**: A strict 8px spacing scale governs margins, paddings, and gaps.

### 5. Elevation & Depth (or "Elevation")
- **Layering Stack**: How surfaces sit relative to each other (e.g., Level 1 background, Level 2 cards, Level 3 drawers/sheets).
- **Shadows & Borders**: Diffused ambient shadows for mobile/material depth (blur 20-40px, low opacity) and 1px borders/tonal shifts for web flat design.

### 6. Shapes
- **Corner Radii**: Mapping the `rounded` scale to components.
- **Tactile Vibe**: Approachable curves (rounded cards/buttons) vs. technical sharpness (minimal corner radius).

### 7. Components
- **Web Atoms**: Tooltips, modals, hover states, and inputs.
- **Mobile Atoms**: Touch targets (minimum 44x44pt on iOS, 48x48dp on Android), Floating Action Buttons (FABs), bottom sheets, and navigation rails vs. bottom bars.
- **Interactive States**: Transitions (150ms ease), focused inputs, and touch feedback (ink ripples / highlights).

### 8. Do's and Don'ts
- **Cross-Platform Guardrails**: Combine web and mobile constraints.
  - *Do* maintain 48px touch targets for mobile.
  - *Don't* use hover states as the sole mechanism for revealing mobile interactions.
  - *Do* respect notch and home indicator safe areas.
  - *Don't* use text drop shadows or mix more than two font families.

## 3. Best Practices & Optimization

- **Platform-Agnostic Naming**: Always use semantic functional names (`surface-container`, `on-surface`) instead of descriptive colors (`gray-100`, `blue-500`) or platform-specific terminology (`colorSecondary`).
- **Dynamic Scaling**: Specify rules for viewport transitions (e.g., collapsing a 3-column desktop card layout to a single-column scrollable mobile list).
- **Prefix Caching**: Keep the token front matter structured and stable, appending dynamic parameters at the bottom of sections.

## 4. Multi-Platform Interoperability & CLI

Use the `@google/design.md` CLI to validate the file and generate code tokens for all target platforms:

```bash
# Lint the unified file for errors and contrast compliance
npx @google/design.md lint DESIGN.md

# Export to Web (Tailwind v3/v4 CSS variables)
npx @google/design.md export --format json-tailwind DESIGN.md > tailwind.theme.json
npx @google/design.md export --format css-tailwind DESIGN.md > theme.css

# Map to Android Jetpack Compose (using custom parsers or JSON)
# Read the exported DTCG tokens to generate Kotlin color/typography objects
npx @google/design.md export --format dtcg DESIGN.md > tokens.json
```

## 5. Tooling & Resources

### Reference Files
*   [design-md-template.md](file:///Users/jsanjaya/.gemini/config/skills/design-md-expert/references/design-md-template.md) — Base template supporting both Web and Mobile.
*   [world-class-patterns.md](file:///Users/jsanjaya/.gemini/config/skills/design-md-expert/references/world-class-patterns.md) — Stripe, Linear, Salesforce, VoltAgent.
*   [accessibility-checklist.md](file:///Users/jsanjaya/.gemini/config/skills/design-md-expert/references/accessibility-checklist.md) — WCAG 2.2 AA, iOS HIG, and Material Design 3.

### Unified Design Examples
*   [Atmospheric Glass](file:///Users/jsanjaya/.gemini/config/skills/design-md-expert/assets/design-md-examples/atmospheric-glass/DESIGN.md) — Glassmorphism weather dashboard sample.
*   [Paws & Paths](file:///Users/jsanjaya/.gemini/config/skills/design-md-expert/assets/design-md-examples/paws-and-paths/DESIGN.md) — Friendly Modern Corporate mobile/web pet service sample.
*   [Totality Festival](file:///Users/jsanjaya/.gemini/config/skills/design-md-expert/assets/design-md-examples/totality-festival/DESIGN.md) — Cosmic Premium festival landing page and ticketing sample.

<constraints>
- Outputs must conform to the 8-section format.
- Always include mobile safe-areas, touch targets, and responsive behaviors in layout and component sections.
- Ensure colors map clearly to standard mobile framework schemes (Material Theme, SwiftUI assets).
- Spacing scales must accommodate touch-first and cursor-first layout densities.
</constraints>

<context>
Target file path: {target_path}
Design intent: {design_intent}
Codebase language: {language}
</context>
