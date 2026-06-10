# Writing Rules Reference

> Non-negotiable principles for human-authentic prose. Apply during drafting and editing.

---

## 1. Syntactic Velocity & Sentence Rhythm

Large Language Models (LLMs) suffer from rhythmic flattening, generating consecutive sentences of uniform medium length. Human prose requires pacing:

- **The Rhythm Formula:**
  - **Short and Punchy:** 2–3 consecutive sentences of 3–8 words for high-impact emphasis.
  - **Expansive:** 1 longer sentence of 20–35 words to carry complex, connected clauses.
  - **Maximum Run:** Never write more than two consecutive sentences of the same approximate length.
- **Syntactic Velocity:** Every sentence must push the narrative forward. Never repeat or summarize what was just said.

---

## 2. Vocabulary Blacklist (AI Slop Detection)

Eradicate these probabilistic words and phrases. Replace them with plain, visceral human language:

| Banned term | Category | Preferred Human Equivalent |
| :--- | :--- | :--- |
| **Delve / Delving** | Verb | Explore, dig into, examine, look at, analyze |
| **Leverage / Utilize** | Verb | Use, apply, take advantage of |
| **Facilitate / Elucidate** | Verb | Help, make easier, explain, clear up |
| **Ascertain / Endeavor** | Verb | Find out, try |
| **Commence / Underscore** | Verb | Start, highlight, show |
| **Tapestry / Realm / Landscape** | Noun | Environment, field, network, system, industry |
| **Ecosystem** (metaphorical) | Noun | System, tooling stack, configuration |
| **Testament to / Symphony of** | Noun | Proof of, demonstration of, result of |
| **Transformative / Groundbreaking** | Adjective | Useful, effective, major, significant, practical |
| **Revolutionary / Cutting-edge** | Adjective | New, advanced, modern |
| **Seamless / Robust** | Adjective | Smooth, strong, solid, easy |
| **Nuanced / Holistic / Pivotal** | Adjective | Specific, complete, key, critical |
| **Furthermore / Moreover** | Transition | *Omit connector entirely; start next sentence* |
| **Additionally / Consequently** | Transition | *Omit, or use "But / Yet" for contrast* |
| **Indeed / In conclusion** | Transition | *Delete entirely* |
| **Ultimately / In summary / Overall** | Transition | *Delete entirely* |

### Conversational Throat-Clearing (Delete on sight)
- *“It’s worth noting that...”*
- *“It goes without saying...”*
- *“At the end of the day...”*
- *“Moving forward...”*
- *“In today’s fast-paced world...”*
- *“Honestly? / Here’s the breakdown / Let me be direct / Here’s what nobody tells you”*

---

## 3. Qualifiers & Hedging (Prune on Sight)

Prune qualifiers that dilute narrative authority:
- **Banned list:** `a bit, sort of, generally, probably, somewhat, in a sense, a little bit, kind of, fairly, rather, quite`.
- *Wrong:* "This was generally a pretty good approach to solving the caching issue."
- *Right:* "This solved the caching issue."
- **Rule:** If a state of confusion, fatigue, or error is relevant, state it directly ("be confused", "be tired", "the build failed"). Do not hedge.

---

## 4. Transitions: The Wet Dishrag Rule

- **Contrast:** Start a sentence with **But** or **Yet** to signal contrast. It is immediate and conversational.
- **Stiffness:** Never start a sentence with **However**. It hangs "like a wet dishrag" at the beginning of a clause. If used, place it inside the clause.
- **Logical Juxtaposition:** Let sentences connect logically without heavy-handed transitional glue.

---

## 5. Specificity Over Generality (The Newspaper Test)

Every paragraph must pass the **Newspaper/Friend Test**: *Could this exact paragraph appear in an article written by someone who never worked on this project?* If yes, rewrite with specific, irreplaceable details:

| Generic (Amateur) | Specific (Professional) |
| :--- | :--- |
| "a recent study showed..." | "A 2024 paper from Google showed..." |
| "many engineers struggle with..." | "Every new screen used to take most of a morning..." |
| "this improved performance" | "this reduced our average load time from 1.8s to 340ms" |
| "the migration was complex" | "CacheMissException errors appeared throughout our UI on watch()" |
| "we had 13 skills" | "We've built 13 skills so far. They fall into four categories." |

---

## 6. Technical Layout & Code Standards

- **USA/UK punctuation:** Commas and periods go **inside** quotation marks.
- **No Semicolons:** Break compound clauses into separate, short sentences.
- **Oxford Comma:** Always use it for list items.
- **No spaces before colons:** e.g., use `term: definition` instead of `term : definition`.
- **Code Walkthrough Rule:**
  1. Write 1–2 sentences explaining what to look for **before** the code block.
  2. Limit the snippet to **10–15 lines** of critical code. Never use screenshots.
  3. Write 1 sentence explaining the key line or trade-off **after** the code block.

---

## 7. Contractions

- **Do use:** `I'll, won't, can't, we're, it's, don't, that's, there's, you'll` to maintain warmth.
- **Do NOT use:** `I'd` (ambiguous: had/would) or `could've/would've` (artificial).
