# Linear-Inspired Design System

## Visual Theme & Atmosphere

**Philosophy**: Speed, focus, and craft. Built for creators who value momentum. High information density with crystal clarity. Every interaction feels instant. Keyboard-first, mouse-optional.

**Density**: Very High — maximize content, minimize chrome. Tight spacing, efficient use of space.

**Personality**: Fast, Focused, Powerful, Opinionated, Crafted

---

## Color Palette & Roles

### Primary Colors

| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| `primary` | #5E6AD2 | rgb(94, 106, 210) | Primary actions, selection, focus |
| `primary-hover` | #4C5BC7 | rgb(76, 91, 199) | Hover state |
| `primary-pressed` | #3A4AB3 | rgb(58, 74, 179) | Active/pressed |

### Surface Colors (Dark Mode)

| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| `surface` | #1C1C1F | rgb(28, 28, 31) | Default background |
| `surface-elevated` | #27272A | rgb(39, 39, 42) | Cards, panels |
| `surface-sunken` | #18181B | rgb(24, 24, 27) | Input fields |

### Text Colors (Dark Mode)

| Token | Hex | RGB | Usage | Contrast |
|-------|-----|-----|-------|----------|
| `on-surface` | #E4E4E7 | rgb(228, 228, 231) | Primary text | 12.8:1 |
| `on-surface-secondary` | #A1A1AA | rgb(161, 161, 170) | Secondary text | 5.2:1 |
| `on-surface-disabled` | #52525B | rgb(82, 82, 91) | Disabled text | 3.1:1 |

### Semantic Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `success` | #10B981 | Success, completed |
| `warning` | #F59E0B | In progress, warnings |
| `error` | #EF4444 | Errors, blocked |
| `info` | #5E6AD2 | Info, selected |

### Border & Divider

| Token | Hex | Usage |
|-------|-----|-------|
| `border` | #3F3F46 | rgb(63, 63, 70) | Default borders |
| `border-strong` | #52525B | rgb(82, 82, 91) | Emphasized borders |
| `divider` | #27272A | rgb(39, 39, 42) | Subtle dividers |

---

## Typography Rules

### Font Families

```css
--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-mono: 'JetBrains Mono', 'SF Mono', monospace;
```

### Type Scale (Compact)

| Scale | Size | Weight | Line Height | Use Case |
|-------|------|--------|-------------|----------|
| `h1` | 24px | 600 | 1.2 | Page titles |
| `h2` | 18px | 600 | 1.3 | Section headers |
| `h3` | 15px | 600 | 1.4 | Subsection headers |
| `body` | 14px | 400 | 1.5 | Default text |
| `body-small` | 13px | 400 | 1.4 | Secondary text |
| `caption` | 12px | 500 | 1.3 | Labels, metadata |

**Note**: Tight scale for high density. Every pixel counts.

---

## Component Stylings

### Buttons

#### Primary Button
```
Background: #5E6AD2
Text: #FFFFFF
Padding: 6px 12px
Border-radius: 6px
Font: 13px / 500
Min-height: 32px

States:
- Hover: #4C5BC7
- Pressed: #3A4AB3
- Focus: 0 0 0 2px #5E6AD2
```

#### Ghost Button
```
Background: transparent
Text: #E4E4E7
Padding: 6px 12px
Border-radius: 6px

States:
- Hover: #27272A background
- Pressed: #3F3F46 background
```

### Input Fields

```
Background: #18181B
Border: 1px solid #3F3F46
Text: #E4E4E7
Padding: 6px 10px
Border-radius: 6px
Min-height: 32px

States:
- Focus: 1px border #5E6AD2
- Error: 1px border #EF4444

Label: 13px / 500 / #A1A1AA
```

### Cards

```
Background: #27272A
Border: 1px solid #3F3F46
Border-radius: 8px
Padding: 12px
Shadow: none (flat design)

States:
- Hover: #3F3F46 border (if interactive)
```

### Command Palette (Cmd+K)

```
Background: #27272A
Border: 1px solid #52525B
Border-radius: 12px
Padding: 8px
Shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5)
Max-width: 640px

Input:
- Background: transparent
- Border: none
- Padding: 12px 16px
- Font: 15px

Items:
- Padding: 8px 12px
- Border-radius: 6px
- Hover: #3F3F46 background
- Selected: #5E6AD2 background
```

---

## Layout Principles

### Spacing System (4px base)

| Token | Value | Usage |
|-------|-------|-------|
| `space-xs` | 4px | Tight inline spacing |
| `space-sm` | 8px | Component internal padding |
| `space-md` | 12px | Between related elements |
| `space-lg` | 16px | Between sections |
| `space-xl` | 24px | Major layout gaps |

**Note**: Tighter spacing than typical systems. Optimized for density.

### Grid System

**Desktop**: 16 columns, 12px gutter  
**Tablet**: 8 columns, 12px gutter  
**Mobile**: 4 columns, 12px gutter

---

## Depth & Elevation

**Philosophy**: Flat design. Minimal shadows. Depth through borders and backgrounds.

| Level | Shadow | Usage |
|-------|--------|-------|
| `elevation-0` | none | Default |
| `elevation-1` | none | Cards (use border instead) |
| `elevation-2` | 0 4px 6px rgba(0, 0, 0, 0.2) | Dropdowns |
| `elevation-3` | 0 20px 25px -5px rgba(0, 0, 0, 0.5) | Modals, command palette |

---

## Do's and Don'ts

### DO
- ✅ Optimize for keyboard navigation
- ✅ Provide instant feedback
- ✅ Use high information density
- ✅ Implement command palette (Cmd+K)
- ✅ Show keyboard shortcuts

### DON'T
- ❌ NEVER add loading spinners (optimize for speed instead)
- ❌ NEVER use heavy shadows (flat design)
- ❌ NEVER hide keyboard shortcuts
- ❌ NEVER use slow animations (max 150ms)
- ❌ NEVER add unnecessary chrome
- ❌ NEVER use light mode as default (dark-first)

---

## Keyboard Shortcuts

**Essential**:
- `Cmd+K`: Command palette
- `Cmd+/`: Keyboard shortcuts help
- `/`: Quick search
- `C`: Create new item
- `Esc`: Close modal/panel

**Navigation**:
- `↑↓`: Navigate lists
- `Enter`: Select/open
- `Cmd+Enter`: Quick action

---

## Responsive Behavior

### Breakpoints

```css
--breakpoint-sm: 640px;
--breakpoint-md: 768px;
--breakpoint-lg: 1024px;
```

### Mobile Adaptations

- Reduce density slightly (8px base spacing)
- Increase touch targets to 44px
- Hide secondary information
- Simplify navigation

---

## Agent Prompt Guide

```
Primary: #5E6AD2
Background: #1C1C1F
Surface: #27272A
Text: #E4E4E7
Border: #3F3F46
Success: #10B981
Error: #EF4444

Style: Dark mode, high density, flat design, minimal shadows
Spacing: Tight (4px base)
Focus: Speed and keyboard navigation
```
