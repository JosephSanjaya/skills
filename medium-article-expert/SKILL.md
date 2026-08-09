---
name: medium-article-expert
description: "Expert guidance for writing, structuring, outlining, titling, and publishing high-engagement Medium articles. Use whenever the user mentions Medium, Boost nomination, Medium titles/subtitles/kickers, article outlines, key points from a topic, SEO slugs/canonicals, or drafting/editing a Medium post — even if they only share a rough topic or research notes and do not say \"Medium article.\" Covers topic→angle→3–5 key points→title factory, Zinsser/Halbert prose, Sugarman's Slippery Slide, BAB/PAS/AIDA/ACT/Zigzag spines, Medium formatting, Boost quality bars, and pre-publish SEO."
---

# Medium Article Expert

Draft, outline, title, edit, and publish technical articles for Medium Boost using first-hand specificity and human-authentic prose.

<workflow>
## 1. Decision tree

| Need | Action |
| :--- | :--- |
| Topic, idea, notes, or research dump → outline + titles | Run Topic→Points→Titles ([references/outline-and-titles.md](references/outline-and-titles.md)) **before drafting** |
| Orient tone / audience | Phase 0 ([references/tone-guide.md](references/tone-guide.md)) |
| Extra title variants after outline | ([references/title-patterns.md](references/title-patterns.md)) |
| Section blueprints (migration / architecture / playbook) | ([references/structure-patterns.md](references/structure-patterns.md)) |
| Edit prose / kill AI slop | ([references/writing-rules.md](references/writing-rules.md), [references/humanizing-ai-writing.md](references/humanizing-ai-writing.md)) |
| Mechanical scan | `python3 scripts/validate_draft.py <draft.md>` |
| Pre-publish Boost + SEO check | ([references/validation.md](references/validation.md), [references/boost-strategy.md](references/boost-strategy.md)) |
| Layout shell | ([assets/article-template.md](assets/article-template.md)) |
| Craft / Slippery Slide depth | ([references/crafting-engaging-articles.md](references/crafting-engaging-articles.md)) |
</workflow>

<tools>
## 2. Validate draft

```bash
python3 scripts/validate_draft.py <path_to_draft.md>
```

Detects banned words, qualifiers, semicolons, flat sentence rhythm.
</tools>

<references>
## 3. Progressive disclosure

- **Outline + titles (topic → angle → 3–5 points → 10–20 titles):** [outline-and-titles.md](references/outline-and-titles.md)
- **Title templates (engineering patterns):** [title-patterns.md](references/title-patterns.md)
- **Section blueprints:** [structure-patterns.md](references/structure-patterns.md)
- **Tone:** [tone-guide.md](references/tone-guide.md)
- **Writing rules / blacklist:** [writing-rules.md](references/writing-rules.md)
- **Humanizing AI prose:** [humanizing-ai-writing.md](references/humanizing-ai-writing.md)
- **Engagement craft:** [crafting-engaging-articles.md](references/crafting-engaging-articles.md)
- **Boost + SEO:** [boost-strategy.md](references/boost-strategy.md)
- **Final checklist:** [validation.md](references/validation.md)
- **Template:** [article-template.md](assets/article-template.md)
</references>

<constraints>
- Write section-by-section. Do not dump a full article in one response.
- When the user brings a topic without a locked outline/title, emit the outline-and-titles output contract first.
- No qualifiers. No sentence starting with "However" or "Additionally".
- Self-promotion only at the absolute bottom.
- Run `validate_draft.py` or check [validation.md](references/validation.md) before claiming a draft is publish-ready.
- Avoid banned AI-slop words ([writing-rules.md](references/writing-rules.md)).
- Titles must be accurate + specific: curiosity gap anchored to a true payoff; subtitle extends, never repeats; body delivers the title promise without a first-paragraph caveat.
</constraints>
