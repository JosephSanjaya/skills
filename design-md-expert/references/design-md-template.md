# DESIGN.md Template (Unified Web & Mobile)

Official, Google-spec-compliant template for machine-readable design systems across Web and Mobile.

## How to Use

1. Copy this template (starting from the first `---` fence) to your project root as `DESIGN.md`.
2. Replace the placeholder values with your brand's specific design tokens and rationale.
3. Validate your file using the official CLI: `npx @google/design.md lint DESIGN.md`.
4. Export tokens for web and read the DTCG JSON format to generate mobile framework objects (Jetpack Compose, SwiftUI).

---
version: alpha
name: [Brand Name]
colors:
  primary: "#[HEX]"              # Maps to MaterialTheme.colorScheme.primary / Color("Primary")
  on-primary: "#[HEX]"
  secondary: "#[HEX]"
  on-secondary: "#[HEX]"
  tertiary: "#[HEX]"
  on-tertiary: "#[HEX]"
  neutral: "#[HEX]"
  background: "#[HEX]"
  on-background: "#[HEX]"
  surface: "#[HEX]"
  on-surface: "#[HEX]"
  surface-variant: "#[HEX]"
  on-surface-variant: "#[HEX]"
  outline: "#[HEX]"
typography:
  headline-lg:
    fontFamily: [Font Family Name]
    fontSize: 32px
    fontWeight: "700"
    lineHeight: 40px
    letterSpacing: -0.02em
  body-md:
    fontFamily: [Font Family Name]
    fontSize: 16px
    fontWeight: "400"
    lineHeight: 24px
  label-sm:
    fontFamily: [Font Family Name]
    fontSize: 12px
    fontWeight: "600"
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 4px                         # M3 Extra Small / iOS Button
  DEFAULT: 8px                    # M3 Small
  lg: 12px                        # M3 Medium / iOS Card
  full: 9999px
spacing:
  unit: 8px                       # Base 8dp grid unit
  container-padding: 24px
  card-gap: 16px
  safe-area-bottom: 34px          # iOS home indicator safe area / Android nav bar
  touch-target: 48px              # Minimum interactive dimension
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label-sm}"
    rounded: "{rounded.DEFAULT}"
    height: 48px                  # Ensures 48px minimum mobile touch target
    padding: 0 16px
  button-primary-hover:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.on-secondary}"
  input-field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body-md}"
    rounded: "{rounded.sm}"
    padding: 12px
    height: 48px                  # Touch-target compliant height
  card-standard:
    backgroundColor: "{colors.surface-variant}"
    rounded: "{rounded.lg}"
    padding: "{spacing.container-padding}"
---

## Overview

[Holistic description of the product's look and feel. Define the brand personality, target audience, and the emotional response the UI should evoke. Discuss density, spacing philosophy, and how the style adapts between desktop and mobile form factors.]

## Colors

[Explain the color strategy, color roles, and contrast requirements. Provide rationale for the choices. Ensure roles are defined for both web elements and native mobile surfaces.]

- **Primary (#[HEX]):** [Description and role, e.g., Primary actions, active navigation states, brand highlights.]
- **Secondary (#[HEX]):** [Description and role, e.g., Secondary actions, trust indicators.]
- **Neutral (#[HEX]):** [Description and role, e.g., Foundation backgrounds, card surfaces, border lines.]

## Typography

[Describe the typography strategy, font pairings, weights, and hierarchical rules. Detail how text size scales down on smaller viewports and how system scaling (iOS Dynamic Type / Android Auto-scaling) is handled.]

- **Headlines:** [Description of heading font family, weights, and treatments.]
- **Body:** [Description of body copy font family, weights, and line heights for legibility.]
- **Labels:** [Description of metadata, button labels, and caption fonts.]

## Layout

[Describe the layout and spacing model, grid systems, margins, and safe areas.]

- **Rhythm:** [Explain the spacing scale base unit, e.g., 8px base grid.]
- **Web Layout:** [Detail 12-column systems, desktop margins, and gutters.]
- **Mobile Layout:** [Detail 4-column system, top/bottom navigation zones, and Safe Area Insets (notch, status bar, home indicator).]
- **Whitespace:** [Explain density goals and breathing room philosophy across devices.]

## Elevation & Depth

[Describe how visual hierarchy is conveyed (tonal layers, shadows, or flat borders).]

- **Layers:** [Detail how different surfaces stack visually. Focus on web flat surfaces vs. mobile Material 3 / iOS HIG elevation stacks.]
- **Shadows/Borders:** [Provide shadow properties or border requirements for separating layers.]

## Shapes

[Describe the shape language, corner radiuses, and border styles.]

- **Containers:** [Corner radius rules for web cards and mobile profile/detail containers.]
- **Controls:** [Corner radius rules for buttons, inputs, and minor controls.]

## Components

### Buttons

[Component-specific style rules and interactive behavior details. Explicitly address touch targets (min 44px on iOS, 48px on Android) and hover states (web only).]

### Inputs

[Form field state rules, focus borders, error indicators, touch heights, and helper text positioning.]

## Do's and Don'ts

- Do use semantic color tokens (`primary`, not `blue-500`) for all components.
- Don't use hover states as the sole method to trigger interactions on touch screens.
- Do maintain WCAG 2.2 AA contrast ratios (4.5:1 for normal text).
- Don't let interactive elements fall below 48x48px touch targets on mobile.
