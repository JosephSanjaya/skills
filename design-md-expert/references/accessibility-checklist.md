# WCAG 2.2 AA Accessibility Checklist

Comprehensive guide for accessibility compliance in design systems.

## Core Principle

Accessibility = strategic foundation, not optional add-on. Shift left: think accessibility during planning/design, not after development.

## WCAG 2.2 AA Critical Criteria

### New in WCAG 2.2

| Criterion | Level | Requirement | Implementation |
|-----------|-------|-------------|----------------|
| **Focus Not Obscured (Minimum)** | AA | Focus indicator not fully hidden by author-created content | Ensure modals, sticky footers don't clip focus outlines |
| **Focus Not Obscured (Enhanced)** | AAA | No part of focus indicator hidden | Higher standard; consider for critical apps |
| **Dragging Movements** | AA | Single-pointer alternative for drag operations | Provide keyboard controls or input fields for sliders |
| **Target Size (Minimum)** | AA | Interactive elements ≥24x24 CSS pixels | Increase touch targets; add spacing |
| **Consistent Help** | A | Help mechanisms in consistent order | Place support links in same location |
| **Redundant Entry** | A | Don't require re-entering info in same session | Auto-fill previously entered data |
| **Accessible Authentication** | AA | No cognitive function test for auth | Provide password managers, email links |

### Existing WCAG 2.1 AA (Still Critical)

| Criterion | Requirement | Common Failures |
|-----------|-------------|-----------------|
| **Contrast (Minimum)** | 4.5:1 text, 3:1 UI components | Light gray text on white, low-contrast buttons |
| **Resize Text** | 200% zoom without loss of content/functionality | Fixed pixel layouts, horizontal scroll |
| **Reflow** | 320px width without 2D scroll | Fixed-width containers, no responsive design |
| **Non-text Contrast** | 3:1 for UI components, graphics | Subtle borders, low-contrast icons |
| **Text Spacing** | Support increased spacing without loss | Clipped text, overlapping elements |
| **Keyboard** | All functionality via keyboard | Dropdown menus, modals without focus trap |
| **Focus Visible** | Visible focus indicator | Removed outlines, invisible focus states |
| **Label in Name** | Accessible name contains visible label | Icon buttons without matching aria-label |
| **Status Messages** | Announced without focus change | Toast notifications without aria-live |

## Design System Implementation

### Color & Contrast

**Text Contrast**:
- Normal text (<18.5px): 4.5:1 minimum
- Large text (≥18.5px or ≥14px bold): 3:0:1 minimum
- UI components (borders, icons): 3:1 minimum

**Tools**:
- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
- Stark plugin (Figma): Real-time contrast checking

**Implementation**:
```css
/* Define contrast-safe color tokens */
--text-primary: #1A1C1E; /* 15.3:1 on white */
--text-secondary: #5F6368; /* 7.0:1 on white */
--text-disabled: #9AA0A6; /* 3.1:1 on white - minimum */

/* UI component contrast */
--border: #DADCE0; /* 3.0:1 on white - minimum */
--border-strong: #5F6368; /* 7.0:1 on white */
```

### Typography & Sizing

**rem-based Sizing**:
- Use `rem` units (responds to user zoom settings)
- Never use `px` for font sizes
- Base: 16px = 1rem

**Text Spacing Support**:
```css
/* Ensure design supports increased spacing */
line-height: ≥1.5 (body text)
paragraph-spacing: ≥2x font-size
letter-spacing: ≥0.12x font-size
word-spacing: ≥0.16x font-size
```

**Minimum Font Sizes**:
- Body text: 16px (1rem) minimum
- Small text: 14px (0.875rem) minimum
- Avoid text <12px (not accessible)

### Focus Indicators

**Requirements**:
- Visible on all interactive elements
- ≥2px outline or border
- High contrast (3:1 minimum)
- Not obscured by other content

**Implementation**:
```css
/* Default focus indicator */
:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}

/* Ensure not obscured by modals */
.modal {
  z-index: 1300;
}
.modal-backdrop {
  z-index: 1200;
}
/* Focused element behind modal should still be visible */
```

### Touch Targets

**Minimum Sizes**:
- WCAG 2.2 AA: 24x24 CSS pixels
- iOS/Android: 44x44 CSS pixels (recommended)
- Best practice: 48x48 CSS pixels

**Spacing**:
- 8px minimum between targets
- Exception: inline text links (sentence context)

**Implementation**:
```css
/* Button minimum size */
.button {
  min-height: 44px;
  min-width: 44px;
  padding: 12px 24px;
}

/* Icon button */
.icon-button {
  width: 48px;
  height: 48px;
  padding: 12px; /* 24px icon inside */
}

/* Spacing between targets */
.button-group > * + * {
  margin-left: 8px;
}
```

### Keyboard Navigation

**Requirements**:
- All interactive elements keyboard-accessible
- Logical tab order (matches visual order)
- Focus trap in modals
- Escape key closes overlays
- Arrow keys for component navigation (optional but recommended)

**Implementation**:
```javascript
// Modal focus trap
const modal = document.querySelector('.modal');
const focusableElements = modal.querySelectorAll(
  'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
);
const firstElement = focusableElements[0];
const lastElement = focusableElements[focusableElements.length - 1];

modal.addEventListener('keydown', (e) => {
  if (e.key === 'Tab') {
    if (e.shiftKey && document.activeElement === firstElement) {
      e.preventDefault();
      lastElement.focus();
    } else if (!e.shiftKey && document.activeElement === lastElement) {
      e.preventDefault();
      firstElement.focus();
    }
  } else if (e.key === 'Escape') {
    closeModal();
  }
});
```

### Screen Reader Support

**Semantic HTML**:
- Use `<button>` for buttons (not `<div>` with click handler)
- Use `<a>` for links
- Use `<nav>`, `<main>`, `<header>`, `<footer>` landmarks
- Use `<h1>`-`<h6>` for headings (logical hierarchy)

**ARIA Labels**:
```html
<!-- Icon button -->
<button aria-label="Close dialog">
  <svg>...</svg>
</button>

<!-- Status message -->
<div role="status" aria-live="polite">
  Item added to cart
</div>

<!-- Loading state -->
<button aria-busy="true" aria-label="Loading...">
  <span aria-hidden="true">Loading...</span>
</button>

<!-- Expanded/collapsed state -->
<button aria-expanded="false" aria-controls="menu">
  Menu
</button>
```

**Live Regions**:
```html
<!-- Polite (waits for pause) -->
<div aria-live="polite" aria-atomic="true">
  <!-- Status messages, notifications -->
</div>

<!-- Assertive (interrupts) -->
<div aria-live="assertive" aria-atomic="true">
  <!-- Errors, urgent alerts -->
</div>
```

### Color & Information

**Never use color alone**:
- Add icons to status indicators
- Use text labels with color
- Provide patterns/textures in charts

**Examples**:
```html
<!-- Bad: Color only -->
<span class="text-red">Error</span>

<!-- Good: Icon + color + text -->
<span class="text-red">
  <svg aria-hidden="true"><!-- error icon --></svg>
  Error: Invalid email address
</span>

<!-- Chart with patterns -->
<svg>
  <rect fill="url(#pattern-success)" />
  <rect fill="url(#pattern-warning)" />
</svg>
```

### Forms

**Requirements**:
- Labels for all inputs
- Error messages associated with inputs
- Required fields indicated (not color alone)
- Clear instructions before form
- Error summary at top (optional but recommended)

**Implementation**:
```html
<!-- Accessible form field -->
<div class="form-field">
  <label for="email">
    Email address
    <span aria-label="required">*</span>
  </label>
  <input
    type="email"
    id="email"
    name="email"
    required
    aria-required="true"
    aria-describedby="email-error email-hint"
  />
  <div id="email-hint" class="hint">
    We'll never share your email
  </div>
  <div id="email-error" class="error" role="alert">
    <!-- Error message inserted here -->
  </div>
</div>
```

## Testing Checklist

### Automated Testing

**Tools**:
- axe DevTools (browser extension)
- Lighthouse (Chrome DevTools)
- WAVE (browser extension)
- Pa11y (CI integration)

**Limitations**: Automated tools catch ~30-40% of issues. Manual testing required.

### Manual Testing

**Keyboard Navigation**:
- [ ] Tab through all interactive elements
- [ ] Shift+Tab reverses order
- [ ] Enter/Space activates buttons
- [ ] Escape closes modals/dropdowns
- [ ] Arrow keys navigate within components
- [ ] Focus visible at all times
- [ ] Focus not trapped (except modals)

**Screen Reader Testing**:
- [ ] VoiceOver (macOS/iOS): Cmd+F5
- [ ] NVDA (Windows): Free download
- [ ] JAWS (Windows): Industry standard
- [ ] TalkBack (Android): Built-in

**Screen Reader Checklist**:
- [ ] All content announced
- [ ] Headings navigable (H key)
- [ ] Landmarks navigable (D key)
- [ ] Forms navigable (F key)
- [ ] Buttons/links identified correctly
- [ ] Images have alt text (or aria-hidden if decorative)
- [ ] Status messages announced
- [ ] Loading states announced

**Zoom & Reflow**:
- [ ] 200% zoom: no horizontal scroll, all content visible
- [ ] 400% zoom: content reflows, no loss of functionality
- [ ] 320px width: no 2D scroll

**Color & Contrast**:
- [ ] All text meets contrast ratios
- [ ] UI components meet 3:1 contrast
- [ ] Information not conveyed by color alone
- [ ] High contrast mode supported (Windows)

## Design System Tokens

### Accessible Color Palette

```yaml
# Light mode
colors:
  text:
    primary: "#1A1C1E"        # 15.3:1 on white
    secondary: "#5F6368"      # 7.0:1 on white
    disabled: "#9AA0A6"       # 3.1:1 on white (minimum)
  
  surface:
    default: "#FFFFFF"
    elevated: "#F8F9FA"
    sunken: "#F1F3F4"
  
  border:
    default: "#DADCE0"        # 3.0:1 on white (minimum)
    strong: "#5F6368"         # 7.0:1 on white
  
  primary:
    default: "#1A73E8"        # 4.5:1 on white
    hover: "#1557B0"          # 7.0:1 on white
    pressed: "#0D47A1"        # 10.0:1 on white
  
  semantic:
    success: "#137333"        # 4.5:1 on white
    warning: "#B06000"        # 4.5:1 on white
    error: "#C5221F"          # 4.5:1 on white
    info: "#1A73E8"           # 4.5:1 on white

# Dark mode
colors-dark:
  text:
    primary: "#E8EAED"        # 13.6:1 on #202124
    secondary: "#9AA0A6"      # 6.4:1 on #202124
    disabled: "#5F6368"       # 3.1:1 on #202124 (minimum)
  
  surface:
    default: "#202124"
    elevated: "#292A2D"
    sunken: "#17181A"
  
  border:
    default: "#3C4043"        # 3.0:1 on #202124 (minimum)
    strong: "#5F6368"         # 4.5:1 on #202124
  
  primary:
    default: "#8AB4F8"        # 4.5:1 on #202124
    hover: "#AECBFA"          # 7.0:1 on #202124
    pressed: "#C2DBFF"        # 10.0:1 on #202124
```

### Accessible Typography Scale

```yaml
typography:
  base-size: 16px  # 1rem
  
  scale:
    display:
      size: 3rem      # 48px
      weight: 700
      line-height: 1.1
    
    h1:
      size: 2rem      # 32px
      weight: 700
      line-height: 1.2
    
    h2:
      size: 1.5rem    # 24px
      weight: 600
      line-height: 1.3
    
    body:
      size: 1rem      # 16px
      weight: 400
      line-height: 1.5
    
    small:
      size: 0.875rem  # 14px (minimum)
      weight: 400
      line-height: 1.4
```

## Common Failures & Fixes

| Failure | Impact | Fix |
|---------|--------|-----|
| Low contrast text | Unreadable for low vision | Use contrast checker; darken text |
| Missing alt text | Images not described | Add descriptive alt or aria-hidden |
| No focus indicator | Keyboard users lost | Add visible outline on :focus-visible |
| Small touch targets | Mobile users can't tap | Increase to 44x44px minimum |
| Color-only status | Colorblind users miss info | Add icons + text labels |
| Keyboard trap | Users stuck in component | Add Escape key handler |
| Missing labels | Screen readers can't identify | Add <label> or aria-label |
| Fixed pixel fonts | Doesn't scale with zoom | Use rem units |
| Removed outlines | Focus invisible | Never remove outlines without replacement |
| Inaccessible modals | Keyboard users can't close | Add focus trap + Escape handler |

## Resources

- **WCAG 2.2**: https://www.w3.org/WAI/WCAG22/quickref/
- **WebAIM**: https://webaim.org/
- **A11y Project**: https://www.a11yproject.com/
- **Deque University**: https://dequeuniversity.com/
- **Inclusive Components**: https://inclusive-components.design/
- **ARIA Authoring Practices**: https://www.w3.org/WAI/ARIA/apg/
