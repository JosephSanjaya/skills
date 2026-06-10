# DESIGN.md Template

Production-ready template for machine-readable design systems.

## Usage

1. Copy this template to project root as `DESIGN.md`
2. Replace placeholder values with brand specifics
3. Test with AI agent: generate sample component
4. Iterate on vague sections where AI hallucinates
5. Reference in `CLAUDE.md` or `agents.md`

---

# [Project Name] Design System

## Visual Theme & Atmosphere

**Philosophy**: [Describe the mood, density, and design philosophy. Be specific about what makes this brand unique.]

**Example**: "Professional yet approachable. Information-dense without feeling cluttered. Heritage brand with modern execution. Prioritize clarity over decoration. Inspired by financial services (trust) + developer tools (precision)."

**Density**: [Low/Medium/High] — [Explain whitespace strategy]

**Personality**: [3-5 adjectives that guide aesthetic decisions]

---

## Color Palette & Roles

### Primary Colors

| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| `primary` | #[HEX] | rgb([R], [G], [B]) | Primary actions, brand moments, CTAs |
| `primary-hover` | #[HEX] | rgb([R], [G], [B]) | Hover state for primary elements |
| `primary-pressed` | #[HEX] | rgb([R], [G], [B]) | Active/pressed state |

### Surface Colors

| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| `surface` | #[HEX] | rgb([R], [G], [B]) | Default background |
| `surface-elevated` | #[HEX] | rgb([R], [G], [B]) | Cards, modals, elevated surfaces |
| `surface-sunken` | #[HEX] | rgb([R], [G], [B]) | Input fields, wells |

### Text Colors

| Token | Hex | RGB | Usage | Contrast Ratio |
|-------|-----|-----|-------|----------------|
| `on-surface` | #[HEX] | rgb([R], [G], [B]) | Primary text | [X.X:1] |
| `on-surface-secondary` | #[HEX] | rgb([R], [G], [B]) | Secondary text, labels | [X.X:1] |
| `on-surface-disabled` | #[HEX] | rgb([R], [G], [B]) | Disabled text | [X.X:1] |
| `on-primary` | #[HEX] | rgb([R], [G], [B]) | Text on primary buttons | [X.X:1] |

### Semantic Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `success` | #[HEX] | Success states, confirmations |
| `warning` | #[HEX] | Warnings, caution states |
| `error` | #[HEX] | Errors, destructive actions |
| `info` | #[HEX] | Informational messages |

### Border & Divider

| Token | Hex | Usage |
|-------|-----|-------|
| `border` | #[HEX] | Default borders |
| `border-strong` | #[HEX] | Emphasized borders |
| `divider` | #[HEX] | Horizontal rules, separators |

---

## Typography Rules

### Font Families

```css
--font-primary: '[Font Name]', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-mono: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
```

### Type Scale

| Scale | Size | Weight | Line Height | Letter Spacing | Use Case |
|-------|------|--------|-------------|----------------|----------|
| `display` | [XX]px | [Weight] | [X.X] | [X]em | Hero headlines, landing pages |
| `h1` | [XX]px | [Weight] | [X.X] | [X]em | Page titles |
| `h2` | [XX]px | [Weight] | [X.X] | [X]em | Section headers |
| `h3` | [XX]px | [Weight] | [X.X] | [X]em | Subsection headers |
| `h4` | [XX]px | [Weight] | [X.X] | [X]em | Card titles |
| `body-large` | [XX]px | [Weight] | [X.X] | [X]em | Emphasized body text |
| `body` | [XX]px | [Weight] | [X.X] | [X]em | Default paragraph text |
| `body-small` | [XX]px | [Weight] | [X.X] | [X]em | Secondary text |
| `caption` | [XX]px | [Weight] | [X.X] | [X]em | Metadata, timestamps, labels |
| `overline` | [XX]px | [Weight] | [X.X] | [X]em | Uppercase labels, categories |

### Font Weights

- **Regular**: 400 (body text)
- **Medium**: 500 (emphasis, labels)
- **Semibold**: 600 (subheadings)
- **Bold**: 700 (headings, strong emphasis)

---

## Component Stylings

### Buttons

#### Primary Button
```
Background: [primary]
Text: [on-primary]
Padding: [X]px [Y]px
Border-radius: [X]px
Font: [body] / [Weight]
Min-height: 44px (touch target)

States:
- Hover: [primary-hover]
- Pressed: [primary-pressed]
- Disabled: [surface-sunken] + [on-surface-disabled]
- Focus: 2px outline [primary] + 2px offset
```

#### Secondary Button
```
Background: transparent
Border: 1px solid [border]
Text: [on-surface]
Padding: [X]px [Y]px
Border-radius: [X]px

States:
- Hover: [surface-elevated]
- Pressed: [surface-sunken]
- Disabled: [border] + [on-surface-disabled]
```

#### Tertiary/Ghost Button
```
Background: transparent
Text: [primary]
Padding: [X]px [Y]px

States:
- Hover: [surface-elevated]
- Pressed: [surface-sunken]
```

### Input Fields

```
Background: [surface-sunken]
Border: 1px solid [border]
Text: [on-surface]
Padding: [X]px [Y]px
Border-radius: [X]px
Min-height: 44px

States:
- Focus: 2px border [primary]
- Error: 2px border [error]
- Disabled: [surface-sunken] + [on-surface-disabled]

Label: [body-small] / [Medium] / [on-surface-secondary]
Helper text: [caption] / [on-surface-secondary]
Error text: [caption] / [error]
```

### Cards

```
Background: [surface-elevated]
Border: 1px solid [border] (optional)
Border-radius: [X]px
Padding: [X]px
Shadow: [elevation-1] (see Depth & Elevation)

States:
- Hover: [elevation-2] (if interactive)
- Pressed: [elevation-0]
```

### Navigation

#### Top Navigation
```
Background: [surface]
Border-bottom: 1px solid [divider]
Height: [X]px
Padding: [X]px [Y]px

Links:
- Default: [on-surface-secondary]
- Hover: [on-surface]
- Active: [primary] + 2px bottom border
```

#### Sidebar Navigation
```
Background: [surface-elevated]
Width: [X]px
Padding: [X]px

Items:
- Default: [on-surface-secondary]
- Hover: [surface-sunken]
- Active: [primary] background + [on-primary] text
- Icon + text alignment: [specify]
```

---

## Layout Principles

### Spacing System

**Base**: [4px / 8px]

| Token | Value | Usage |
|-------|-------|-------|
| `space-xs` | [X]px | Tight inline spacing (icon + text) |
| `space-sm` | [X]px | Component internal padding |
| `space-md` | [X]px | Between related elements |
| `space-lg` | [X]px | Between sections |
| `space-xl` | [X]px | Major layout gaps |
| `space-2xl` | [X]px | Page-level spacing |

### Grid System

**Desktop (1024px+)**: [12 / 16] columns  
**Tablet (768-1023px)**: [8 / 12] columns  
**Mobile (<768px)**: [4 / 6] columns

**Gutter**: [X]px  
**Margin**: [X]px

### Container Widths

| Breakpoint | Max Width |
|------------|-----------|
| `sm` | 640px |
| `md` | 768px |
| `lg` | 1024px |
| `xl` | 1280px |
| `2xl` | 1536px |

### Whitespace Philosophy

[Describe approach: generous/minimal, breathing room strategy, content density goals]

---

## Depth & Elevation

### Shadow System

| Level | Shadow | Usage |
|-------|--------|-------|
| `elevation-0` | none | Flat surfaces, pressed states |
| `elevation-1` | [shadow values] | Cards, default elevated surfaces |
| `elevation-2` | [shadow values] | Hover states, dropdowns |
| `elevation-3` | [shadow values] | Modals, popovers |
| `elevation-4` | [shadow values] | Tooltips, highest priority overlays |

**Example**:
```css
elevation-1: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
```

### Z-Index Scale

| Layer | Z-Index | Usage |
|-------|---------|-------|
| `base` | 0 | Default content |
| `dropdown` | 1000 | Dropdowns, popovers |
| `sticky` | 1100 | Sticky headers |
| `modal-backdrop` | 1200 | Modal backgrounds |
| `modal` | 1300 | Modal content |
| `tooltip` | 1400 | Tooltips |
| `notification` | 1500 | Toast notifications |

---

## Do's and Don'ts

### DO
- ✅ Use semantic color tokens (`primary`, not `blue-500`)
- ✅ Maintain 4.5:1 contrast for text, 3:1 for UI components
- ✅ Provide focus indicators for all interactive elements
- ✅ Use consistent spacing from the spacing scale
- ✅ Test on mobile (touch targets ≥44px)
- ✅ [Add brand-specific do's]

### DON'T
- ❌ NEVER use pure black (#000000) for text
- ❌ NEVER use drop shadows on text
- ❌ NEVER mix more than 2 typefaces
- ❌ NEVER use gradients on text
- ❌ NEVER use color alone to convey information
- ❌ NEVER use custom scrollbars (accessibility)
- ❌ [Add brand-specific don'ts]

---

## Responsive Behavior

### Breakpoints

```css
--breakpoint-sm: 640px;
--breakpoint-md: 768px;
--breakpoint-lg: 1024px;
--breakpoint-xl: 1280px;
--breakpoint-2xl: 1536px;
```

### Mobile Adaptations

| Component | Desktop | Mobile |
|-----------|---------|--------|
| Navigation | Horizontal top nav | Hamburger menu |
| Cards | 3-column grid | Single column |
| Typography | Full scale | Reduce display/h1 by [X]% |
| Spacing | Full scale | Reduce xl/2xl by [X]% |
| Tables | Full table | Horizontal scroll or card view |

### Touch Targets

- **Minimum**: 44x44 CSS pixels (iOS/Android standard)
- **Recommended**: 48x48 CSS pixels
- **Spacing**: 8px minimum between targets

---

## Agent Prompt Guide

### Quick Color Reference

When generating UI, use these exact values:

```
Primary action: [primary] (#[HEX])
Background: [surface] (#[HEX])
Text: [on-surface] (#[HEX])
Borders: [border] (#[HEX])
Success: [success] (#[HEX])
Error: [error] (#[HEX])
```

### Sample Prompts

**Button Generation**:
```
Create a primary button using [primary] background, [on-primary] text, 
12px 24px padding, 4px border-radius, and 44px min-height.
```

**Card Generation**:
```
Create a card with [surface-elevated] background, [border] 1px border, 
16px padding, 8px border-radius, and elevation-1 shadow.
```

**Form Generation**:
```
Create an input field with [surface-sunken] background, [border] 1px border,
12px 16px padding, 4px border-radius, and 2px [primary] border on focus.
```

---

## Version History

- **v1.0.0** (YYYY-MM-DD): Initial design system specification
- [Add version updates as system evolves]

---

## Maintenance Notes

- **Owner**: [Name/Team]
- **Last Updated**: [Date]
- **Review Cadence**: [Monthly/Quarterly]
- **Feedback**: [Link to feedback form/issue tracker]
