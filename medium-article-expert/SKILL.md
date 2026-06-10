---
name: medium-article-expert
description: >-
  Expert guidance for writing, structuring, and publishing high-engagement Medium articles. Use when writing a Medium article from scratch, improving or editing a Medium draft, optimizing for the Medium Boost program, reviewing Medium formatting, structuring a Medium post, checking pre-publish SEO settings, or asking about Medium writing best practices. Covers Zinsser/Halbert prose principles, Sugarman's Slippery Slide, BAB/ACT/Zigzag narrative structures, Medium-specific formatting (kicker, separators, code blocks, image widths), SEO settings (slug, display title, canonical URL), Boost quality guidelines, and publishing strategy.
---

# Medium Article Expert

Draft, edit, and optimize technical articles for the Medium Boost nomination program using minimalist writing principles and human-authentic prose.

<instructions>
Structure narrative flow using BAB or ACT templates, prune qualifiers and AI slop words, enforce sentence length rhythm, and optimize SEO and layout parameters before publishing.
</instructions>

## 1. Quick Decision Tree

- **Orient the article context & tone** → Run Phase 0 Orientation ([references/tone-guide.md](references/tone-guide.md))
- **Generate search-optimized titles** → Run Naming Templates ([references/title-patterns.md](references/title-patterns.md))
- **Select article structure blueprint** → Match Layout Structures ([references/structure-patterns.md](references/structure-patterns.md))
- **Edit prose and remove AI slop** → Apply Writing Rules & Blacklists ([references/writing-rules.md](references/writing-rules.md))
- **Scan draft for mechanical violations** → Run Automated Validation Script ([scripts/validate_draft.py](scripts/validate_draft.py))
- **Run final pre-publish validation** → Execute Final Curation Check ([references/validation.md](references/validation.md))
- **Optimize SEO settings & URL slugs** → Configure Meta & Canonical Links ([references/boost-strategy.md](references/boost-strategy.md))

## 2. Fast Command Tools

Run the automated Python scan to detect banned words, qualifiers, semicolons, and flat sentence rhythm:
```bash
python3 scripts/validate_draft.py <path_to_draft.md>
```

## 3. Reference Assets & Templates

- **Visual Article Layout:** [article-template.md](assets/article-template.md)
- **Draft Validation Rules:** [validation.md](references/validation.md)
- **Pacing & Word Blacklist:** [writing-rules.md](references/writing-rules.md)
- **Crafting Engaging Articles:** [crafting-engaging-articles.md](references/crafting-engaging-articles.md)
- **Humanizing AI-Assisted Writing:** [humanizing-ai-writing.md](references/humanizing-ai-writing.md)

<constraints>
Do NOT generate full article drafts in a single response. You **must** write section-by-section. Ensure no qualifiers are used, no sentence starts with "However" or "Additionally", and all self-promotion is placed **only** at the absolute bottom.
Always run the validate_draft.py script or check references/validation.md before responding. You **must** avoid banned slop words.
</constraints>
