# Validation Checklist

> Run this audit after drafting each section. Run the full validation before final delivery.
> This is the antidote to LLM context decay.

---

## 1. Mandatory Pre-Write Check
Before writing any prose, answer these three questions:
1. **What is the single most interesting/surprising thing this section reveals?**
   *If you cannot name it, do not write the section yet.*
2. **What concrete detail (metric, code line, error message) proves this section isn't generic?**
   *If you do not have one, request it or dig deeper.*
3. **Which sentence will be the hardest to forget?**
   *Plan that sentence first. Build the section around it.*

---

## 2. Automated Scan (Phase 1 Edit)
Run the script to instantly flag banned words, qualifiers, semicolons, and flat sentence rhythm:
```bash
python3 scripts/validate_draft.py <path_to_draft.md>
```

---

## 3. Post-Write Checklist (Phase 2 Edit)

### 🔴 Instant Fails (Fix before showing user)
- [ ] Section contains any word/phrase from the Banned List (`references/writing-rules.md`).
- [ ] Section ends with a summary sentence restating the content.
- [ ] Section opens with throat-clearing: *"In today's..."*, *"As we know..."*, *"X is one of the most..."*, *"Before we dive in..."*.
- [ ] Rhythmic flattening: Three consecutive sentences have the same approximate length (7-13 words or 22+ words).
- [ ] Uses qualifiers: `a bit, sort of, generally, somewhat, fairly, rather`.
- [ ] Sentence starts with `However`, `Furthermore`, `Moreover`, `Additionally`, or `Consequently`.
- [ ] Paragraph ends with an empty closer: *"Overall..."*, *"Ultimately..."*, *"By understanding these concepts..."*.
- [ ] Code block is displayed without a preceding context sentence explaining what to look for.

### 🟡 Quality Checks (Fix if possible)
- [ ] Has at least one sentence that could only appear in this specific article.
- [ ] First sentence of the section is under 15 words.
- [ ] Section leans forward, posing a question or tension for the next section.
- [ ] Contractions are used naturally (`We didn't expect` vs. `We did not expect`).
- [ ] The heading is concise, benefit-driven, and contains no clickbait or AI jargon.

### 🟢 Tone Verification
Read the prose aloud. Verify that the tone matches:
- **Yes:** A senior engineer explaining what they actually built, what broke, and what they learned to a peer at a conference.
- **No:** A corporate press release, a marketing flyer, a academic textbook, or an encyclopedic Google-search summary ("write-around").

---

## 4. Full Article Final Validation (Phase 3 Edit)

1. **Section Opener Test:** Read *only* the first sentence of each section in sequence. Does it tell a cohesive, logical story?
2. **Structural Pruning:** Identify the longest paragraph. Cut at least 25% of its clutter.
3. **The Friend Test:** If a senior engineer read this on a Sunday morning, would they learn something new or feel like they are reading generic documentation?
4. **Link Check:** All code blocks are native formatting (\`\`\`), not screenshots, and all external citations are properly attributed in the caption.
5. **Metadata Reality Check:** In settings, the Display Title is < 60 characters and the URL slug is customized (keyword-rich) **before** publishing.
