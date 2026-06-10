# Stripe-Inspired Design System

## Visual Theme & Atmosphere

**Philosophy**: Precision engineering meets elegant simplicity. Every pixel serves a purpose. Deterministic behavior over flexibility. Trust through clarity and consistency.

**Density**: High — information-rich without clutter. Generous whitespace around critical actions.

**Personality**: Professional, Trustworthy, Precise, Developer-focused, Minimal

---

## Color Palette & Roles

### Primary Colors

| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| `primary` | #635BFF | rgb(99, 91, 255) | Primary actions, links, brand moments |
| `primary-hover` | #0A2540 | rgb(10, 37, 64) | Hover state for primary elements |
| `primary-pressed` | #001124 | rgb(0, 17, 36) | Active/pressed state |

### Surface Colors

| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| `surface` | #FFFFFF | rgb(255, 255, 255) | Default background |
| `surface-elevated` | #F6F9FC | rgb(246, 249, 252) | Cards, elevated surfaces |
| `surface-sunken` | #E3E8EE | rgb(227, 232, 238) | Input fields, wells |

### Text Colors

| Token | Hex | RGB | Usage | Contrast |
|-------|-----|-----|-------|----------|
| `on-surface` | #0A2540 | rgb(10, 37, 64) | Primary text | 13.5:1 |
| `on-surface-secondary` | #425466 | rgb(66, 84, 102) | Secondary text | 7.2:1 |
| `on-surface-disabled` | #8898AA | rgb(136, 152, 170) | Disabled text | 3.5:1 |
| `on-primary` | #FFFFFF | rgb(255, 255, 255) | Text on primary | 8.2:1 |

### Semantic Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `success` | #00D924 | Success states, confirmations |
| `warning` | #FFC043 | Warnings, caution states |
| `error` | #DF1B41 | Errors, destructive actions |
| `info` | #635BFF | Informational messages |

### Border & Divider

| Token | Hex | Usage |
|-------|-----|-------|
| `border` | #E3E8EE | rgb(227, 232, 238) | Default borders |
| `border-strong` | #C1C9D2 | rgb(193, 201, 210) | Emphasized borders |
| `divider` | #E3E8EE | rgb(227, 232, 238) | Horizontal rules |

---

## Typography Rules

### Font Families

```css
--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-mono: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
```

### Type Scale

| Scale | Size | Weight | Line Height | Letter Spacing | Use Case |
|-------|------|--------|-------------|----------------|----------|
| `display` | 40px | 600 | 1.1 | -0.02em | Hero headlines |
| `h1` | 28px | 600 | 1.2 | -0.01em | Page titles |
| `h2` | 20px | 600 | 1.3 | 0 | Section headers |
| `h3` | 16px | 600 | 1.4 | 0 | Subsection headers |
| `body` | 15px | 400 | 1.5 | 0 | Default text |
| `body-small` | 13px | 400 | 1.4 | 0 | Secondary text |
| `caption` | 12px | 500 | 1.4 | 0.01em | Labels, metadata |

---

## Component Stylings

### Buttons

#### Primary Button
```
Background: #635BFF
Text: #FFFFFF
Padding: 11px 16px
Border-radius: 6px
Font: 15px / 600
Min-height: 40px

States:
- Hover: #0A2540
- Pressed: #001124
- Disabled: #E3E8EE + #8898AA text
- Focus: 0 0 0 3px rgba(99, 91, 255, 0.3)
```

#### Secondary Button
```
Background: transparent
Border: 1px solid #E3E8EE
Text: #0A2540
Padding: 11px 16px
Border-radius: 6px

States:
- Hover: #F6F9FC background
- Pressed: #E3E8EE background
```

### Input Fields

```
Background: #FFFFFF
Border: 1px solid #E3E8EE
Text: #0A2540
Padding: 11px 12px
Border-radius: 6px
Min-height: 40px

States:
- Focus: 1px border #635BFF + 0 0 0 3px rgba(99, 91, 255, 0.1)
- Error: 1px border #DF1B41
- Disabled: #F6F9FC background + #8898AA text

Label: 13px / 500 / #425466
Error text: 13px / #DF1B41
```

### Cards

```
Background: #FFFFFF
Border: 1px solid #E3E8EE
Border-radius: 8px
Padding: 24px
Shadow: 0 1px 3px rgba(50, 50, 93, 0.15), 0 1px 0 rgba(0, 0, 0, 0.02)

States:
- Hover: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08)
```

---

## Layout Principles

### Spacing System (8px base)

| Token | Value | Usage |
|-------|-------|-------|
| `space-xs` | 4px | Tight inline spacing |
| `space-sm` | 8px | Component internal padding |
| `space-md` | 16px | Between related elements |
| `space-lg` | 24px | Between sections |
| `space-xl` | 32px | Major layout gaps |
| `space-2xl` | 48px | Page-level spacing |

### Grid System

**Desktop**: 12 columns, 24px gutter  
**Tablet**: 8 columns, 16px gutter  
**Mobile**: 4 columns, 16px gutter

---

## Depth & Elevation

| Level | Shadow | Usage |
|-------|--------|-------|
| `elevation-0` | none | Flat surfaces |
| `elevation-1` | 0 1px 3px rgba(50, 50, 93, 0.15), 0 1px 0 rgba(0, 0, 0, 0.02) | Cards |
| `elevation-2` | 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08) | Hover states |
| `elevation-3` | 0 13px 27px -5px rgba(50, 50, 93, 0.25), 0 8px 16px -8px rgba(0, 0, 0, 0.3) | Modals |

---

## Do's and Don'ts

### DO
- ✅ Use semantic color tokens
- ✅ Maintain high contrast (4.5:1 minimum)
- ✅ Provide clear focus indicators
- ✅ Use consistent spacing from scale

### DON'T
- ❌ NEVER use pure black (#000000)
- ❌ NEVER use drop shadows on text
- ❌ NEVER mix more than 2 typefaces
- ❌ NEVER use decorative animations on data
- ❌ NEVER hide focus indicators
- ❌ NEVER use color alone for status

---

## Responsive Behavior

### Breakpoints

```css
--breakpoint-sm: 640px;
--breakpoint-md: 768px;
--breakpoint-lg: 1024px;
--breakpoint-xl: 1280px;
```

### Touch Targets

- **Minimum**: 40x40 CSS pixels
- **Spacing**: 8px between targets

---

## Agent Prompt Guide

```
Primary: #635BFF
Background: #FFFFFF
Text: #0A2540
Border: #E3E8EE
Success: #00D924
Error: #DF1B41
```
