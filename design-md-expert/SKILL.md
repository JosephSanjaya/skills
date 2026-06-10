---
name: design-md-expert
description: >
  Expert guidance for creating, optimizing, and implementing DESIGN.md files. Make sure to use this skill whenever the user mentions design systems, design-md, UI/UX consistency, visual theme, design handoff to AI, Stripe/Linear/VoltAgent styles, dashboard layouts, WCAG 2.2 AA accessibility, or when coding agents generate inconsistent frontend styles.
---

# DESIGN.MD Expert

Expert for creating machine-readable design systems enabling AI agents to generate brand-consistent, professional UI.

<instructions>
Enforce 9-section DESIGN.md structure. Write negative constraints (Don'ts > Do's). Apply semantic token naming. Align typography and spacing to 4px/8px grids. Conform to WCAG 2.2 AA accessibility standards. Optimize for prefix caching by placing dynamic parameters at the end.
</instructions>

## 1. DESIGN.md Core Structure

Plain-text markdown at project root. Reference in CLAUDE.md/agents.md.

| Section | Spec Target | AI Impact |
|:---|:---|:---|
| **Theme & Atmosphere** | Mood, density, philosophy narrative | Prevents generic styling |
| **Color & Roles** | Semantic names + hex + roles. No descriptions | Direct color mappings |
| **Typography** | Font families, size/weight/line-height table | Brand voice + legibility |
| **Components** | Button, card, input, nav state rules | Standardized interactions |
| **Layout & Spacing** | Spacing scale (4px/8px), grid systems | Mathematical layout rhythm |
| **Depth & Elevation** | Shadows, surface hierarchy, z-index | Layering + cognitive priority |
| **Do's & Don'ts** | Explicit positive & negative constraints | Filters out bad AI outputs |
| **Responsive** | Breakpoints, touch targets, collapsing | Cross-device usability |
| **Agent Prompt Guide** | Quick color refs + prompt snippets | Execution bridge |

## 2. Best Practices & Optimization

### Negatives Over Positives
Don'ts > Do's. Negatives prevent LLM hallucinations.
*   *Do*: Use exact rules.
*   *Don't*: NEVER use drop shadows on text. NEVER mix >2 font families. NEVER use gradients on text. NEVER use `#000000` true black (use dark charcoal/navy).

### Semantic Token Rules
Use functional names, not descriptive.
*   *Bad*: `blue-500`, `dark-gray-800`
*   *Good*: `primary`, `surface-elevated`, `on-surface`, `hairline`

### Layout Rhythm
Strict mathematical scale. Align typography line heights with spacing grid (e.g., 25px → 24px) to preserve visual rhythm.

---

## 3. Brand Design Archetypes

Deep-dive details in [world-class-patterns.md](file:///Users/jsanjaya/.gemini/config/skills/design-md-expert/references/world-class-patterns.md).

### Stripe: Precision Engineering
*   **Philosophy**: Deterministic behavior > flexibility.
*   **Validation**: Runtime parent-child checking (e.g., `AccordionItem` inside `Accordion`).
*   **Views**: ContextView (drawer), FocusView (modal backdrop), SettingsView, SignInView.
*   **Docs**: Technical concept → real-world outcome (e.g., "idempotency prevents double charge").

### Linear: Craft, Taste, Momentum
*   **Philosophy**: Taste > metrics. Keyboard-first (Cmd+K). Speed + focus.
*   **Visuals**: Near-black (`#010102`), lavender accent (`#5e6ad2`). Negative display tracking. 4-step surface ladder. Product screenshots dominate.

### VoltAgent: Developer-Centric Minimalism
*   **Philosophy**: UI as documentation. High density, low decoration.
*   **Visuals**: Dark canvas (`#101010`), electric green accent (`#00d992`), 1px solid hairline borders (`#3d3a39`), dashed dividers, Inter/SF Mono. 6px buttons.

### Salesforce: Enterprise Scale
*   **Philosophy**: Design system as internal product.
*   **Scale**: Design Strike Forces (CCPIs) for pattern alignment; user research drives system roadmap.

---

## 4. Layout & Accessibility

### Dashboard Design
Concise details in [dashboard-design.md](file:///Users/jsanjaya/.gemini/config/skills/design-md-expert/references/dashboard-design.md).
*   **Typography**: Base 16px body. Major Second (1.125) scale. Min 3 weights (400, 500, 700).
*   **Grid**: 12-16 columns on desktop (1440px+), 8 on tablet, 4 on mobile.
*   **Hierarchy**: F-pattern or Z-pattern. Top-left: critical KPIs. Bottom: detailed tables.

### Accessibility (WCAG 2.2 AA)
Concise details in [accessibility-checklist.md](file:///Users/jsanjaya/.gemini/config/skills/design-md-expert/references/accessibility-checklist.md).
*   **Focus Visible**: Focus indicator not obscured by modals/footers.
*   **Dragging**: Single-pointer alternatives for drag/drop.
*   **Touch Targets**: Min 24x24 CSS px (AA), recommended 44x44px / 48x48px (iOS/Android).
*   **Identification**: Same function = same label/icon. Contrast 4.5:1 text, 3:1 UI.

### E-commerce UX (Baymard)
*   **Product List**: Show rating averages. Min 3-5 images. Product videos for complex items.
*   **Checkout**: Pinned cart, unique Add to Cart button, plain language return policy, price per unit.

### DesignOps & Governance
*   **Lifecycle**: Audit -> Token Definition -> Component Build -> Maintenance -> Adoption.
*   **Versioning**: SemVer + migration guides. Automated CI visual regression + a11y testing.

---

## 5. Tooling & Resources

*   `validate_design_md.py`: Lint file completeness, color tokens, and anti-patterns.
*   `generate_design_md.py`: Interactive DESIGN.md generator.

```bash
# Validate DESIGN.md
python3 scripts/validate_design_md.py <path/to/DESIGN.md>
```

### Reference Files
*   [design-md-template.md](file:///Users/jsanjaya/.gemini/config/skills/design-md-expert/references/design-md-template.md) — Base template.
*   [world-class-patterns.md](file:///Users/jsanjaya/.gemini/config/skills/design-md-expert/references/world-class-patterns.md) — Stripe, Linear, Salesforce, VoltAgent.
*   [accessibility-checklist.md](file:///Users/jsanjaya/.gemini/config/skills/design-md-expert/references/accessibility-checklist.md) — WCAG 2.2 AA checklist.
*   [dashboard-design.md](file:///Users/jsanjaya/.gemini/config/skills/design-md-expert/references/dashboard-design.md) — Layouts, grids.

### Example Assets
*   [Stripe](file:///Users/jsanjaya/.gemini/config/skills/design-md-expert/assets/design-md-examples/stripe/DESIGN.md) — High-fidelity Stripe analysis.
*   [Linear](file:///Users/jsanjaya/.gemini/config/skills/design-md-expert/assets/design-md-examples/linear/DESIGN.md) — High-fidelity Linear analysis.
*   [VoltAgent](file:///Users/jsanjaya/.gemini/config/skills/design-md-expert/assets/design-md-examples/voltagent/DESIGN.md) — High-fidelity VoltAgent analysis.

<constraints>
- Outputs must only conform to the 9-section format schema.
- Always wrap components in semantic color tokens.
- These rules require adhering to WCAG 2.2 AA accessibility.
- Spacing should align to the 4px/8px layout grid.
- Dynamic inputs must be appended below to respect prefix caching.
</constraints>

<context>
Target file path: {target_path}
Design intent: {design_intent}
Codebase language: {language}
</context>
