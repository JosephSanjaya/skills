# Topic → Angle → Key Points → Titles

> Load when the user has a topic, idea, notes, or research dump and needs an outline and/or titles. Skip if outline + title already locked. Run before drafting — Boost rewards first-hand stake and accurate titles.

<instructions>
## Stages

### 1. Compress topic → one angle
Topic ≠ article. Angle = ownable claim + first-hand stake.

1. Interrogate: who / what / when / where / why / how.
2. Name stake: what only this writer lived, measured, or built.
3. One sentence: `This piece shows [claim] using [first-hand evidence].`
4. Fail if stake is "I read about X" (derivative → no Boost).

Example: "TypeScript" → *Etsy's Journey to TypeScript*, not *TypeScript Benefits*.

### 2. Reader job-to-be-done
Pick one. Cut the rest.

| Job | Reader leaves able to… |
| :--- | :--- |
| Understand | Explain the system / decision |
| Do | Run a skill / recipe / migration step |
| See differently | Hold a new mental model |

Boost-shaped value: uses a skill from the piece, or still thinks about it days later.

### 3. Break into 3–5 key points
- One idea per point; name as scannable H2.
- Each point needs ≥1 concrete example, number, or step (empty = fail early).
- Shape: explanatory → inverted pyramid; problem-driven → problem → why → solution; X vs Y → comparison.

### 4. Choose narrative spine

| Spine | Use when | Shape |
| :--- | :--- | :--- |
| **BAB** | Reader feels the pain | Pain → better world → method |
| **PAS** | Hook + problem-aware | Problem → agitate → resolve |
| **AIDA** | Unaware readers | Build case → CTA |
| **Zigzag** | Lessons / war stories | Setbacks ↔ wins |

Stack OK: PAS hook + benefit body + AIDA close. Section blueprints: [structure-patterns.md](structure-patterns.md).

### 5. Title factory — write 10–20, then pick
First title rarely wins. Maximize curiosity without breaking the promise.

| Template | Signal |
| :--- | :--- |
| How-we / How-X-works | *How Figma's multiplayer technology works* |
| Scaling X at/to Y | *Scaling Translations at Spotify* |
| Colon hook: clarifier | *FacetController: How we made infra changes simple* |
| Lessons / Journey | *Lessons from debugging a tricky direct memory leak* |
| Number + true payoff | *How a one line change decreased clone times by 99%* |
| Metaphor / vivid image | *Changing the Wheels on a Moving Bus* |
| Contrarian thesis | *Coding Is No Longer the Constraint* |
| Before → After | *From 40 minutes to 30 seconds: …* |

Independent writers: prefer vivid devices. Big brands can run dry descriptive titles — their name is the hook.

**Accuracy test:** Does the body fully deliver the title? If you need a first-paragraph caveat, fix the title. Misrepresentation / clickbait / generic-mysterious titles fail Medium distribution bars.

**Format:** Title Case, no period, ~60 chars / <12 words. Subtitle = sentence case, extends title (never repeats). Optional kicker (1–3 words). Cover must represent content; no cover beats a bad AI cover.

**Title anti-slop:** Reject bland-generic (*A Guide to Improving Productivity*) and breathless clickbait (*This ONE Trick…*). Name a specific, surprising, true thing.

Extra engineering variants: [title-patterns.md](title-patterns.md).

### 6. Hand off to draft
1. Slippery-slide opening → [crafting-engaging-articles.md](crafting-engaging-articles.md)
2. Section-by-section (skill constraint)
3. Soft ~7-min center (purpose > pad; Sall 2013 peak)
4. `scripts/validate_draft.py` + [validation.md](validation.md)
5. SEO: slug before publish (permanent); canonical if syndicating; AI disclosure in first two paragraphs → [boost-strategy.md](boost-strategy.md)
</instructions>

<output_contract>
Emit this block before any prose draft (same turn as outline only — no full article unless asked):

```
ANGLE: [claim + first-hand evidence]
JTBD: [understand | do | see differently] — [one-line outcome]
SPINE: BAB | PAS | AIDA | Zigzag — [why]
KEY POINTS (3–5):
1. H2: … — evidence: [fact/number/step]
2. …
TITLES (10–20) → SHORTLIST (3) → PICK (1)
SUBTITLE: [sentence case; extends title]
KICKER: [optional]
ACCURACY: [yes — body delivers title without first-paragraph caveat]
```
</output_contract>

<constraints>
- Output contract before drafting when outline/title unlocked.
- Every key point carries checkable evidence.
- Title promise = body delivery; subtitle extends, never repeats.
- Curiosity gap only when anchored to a true payoff.
</constraints>
