# Article Structure & Layout

> Select the appropriate structural template in Phase 3.

---

## 1. Blueprint 1: Migration / Upgrade Story (BAB)
*Ideal for library upgrades, refactors, and architectural transitions.*

- **Hook (1 paragraph, ~100 words):** Start with the pain. Name the version, library, or system that broke.
- **Section 1: The Before State:** Explain the original setup and why the upgrade was initiated.
- **Section 2: The Blocker:** Detail the specific technical blocker encountered that was *not* in the documentation. Include exact error messages.
- **Section 3: The Fix:** Show the code snippet. Explain *why* this specific change resolved the issue. Detail trade-offs.
- **Section 4: Verification:** Describe how the fix was validated (unit tests, CI pipeline).
- **Conclusion:** A short paragraph containing a single, memorable takeaway. Not a summary.

---

## 2. Blueprint 2: Architecture / System Design (ACT)
*Ideal for new services, architectures, or custom frameworks.*

- **Hook (1 paragraph):** Define the competing forces or tension (e.g., optimization vs. member fatigue).
- **Section 1: Why Existing Approaches Failed:** Detail 2 specific limitations of the previous setup.
- **Section 2: The Architecture:** Provide a component map, explaining each component in a single sentence.
- **Section 3: The Interesting Choice:** Detail the non-obvious design decision that makes this system unique.
- **Section 4: Impact:** Share metrics or qualitative results (e.g., largest production lift to date).
- **Conclusion:** A forward-looking statement on what this architecture makes possible.

### The ACT Pattern (Per Section)
- **A (Attention):** Bold, specific claim or metric opening the section.
- **C (Context):** 2–3 sentences of technical reasoning.
- **T (Takeaway):** One memorable sentence crystallizing the lesson.

---

## 3. Blueprint 3: Practitioner Playbook / Process Article
*Ideal for team workflows, automation tools, or developer guides.*

- **Hook (1 paragraph):** Identify the organizational pain or inconsistency (e.g., tribal knowledge in PR comments).
- **Section 1: The Foundation:** Outline the baseline tooling (file paths, configurations, conventions).
- **Section 2–N: The Components:** Walk through each component, explaining what it does and showing a usage sample.
- **Section: What We Learned:** Provide 3–5 short, opinionated lessons.
- **Conclusion:** Detail the future bet or long-term value.

---

## 4. Length & Pacing Guidelines

### Targets
| Section Type | Target Word Count |
| :--- | :--- |
| **Hook / Opening** | 100–150 words |
| **Problem / Context** | 150–250 words |
| **Core Technical Fix/Architecture** | 250–400 words |
| **Code Walkthrough** | 50-word intro + code block + 50-word detail |
| **Conclusion** | 75–120 words |
| **Total Article** | **1,200–2,000 words** |

### The Zigzag Pacing Rule (For articles > 1,500 words)
Prevent reader fatigue by alternating between tension and release:
- **Tension:** Problem, error stack, constraint, complexity, incident.
- **Release:** Solution, clean code, metric lift, takeaway.
*Rule: Never write three consecutive tension or release sections. Keep the narrative moving like a heartbeat monitor.*
