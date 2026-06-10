# Tone & Voice Guide

> Peer-to-Peer Technical Honesty. Real engineers sharing real experience.

---

## 1. Core Voice: Peer-to-Peer Honesty

Great technical articles sound like a senior engineer discussing a real project with a peer over coffee:

- **Direct:** State the problem or tension in the first paragraph. Skip historical throat-clearing.
- **Specific:** Ground all claims in metrics, code blocks, or names.
- **Honest about Failure:** Name what broke, what was hard, and what went wrong. Failure builds trust.
- **Opinionated:** Take a clear stance. Avoid hedging or "both-sides" framing.
- **Natural Pacing:** Avoid stiff formalisms (e.g., *aforementioned*, *herein*) and corporate jargon (*synergy*, *leverage*).

---

## 2. The Tone Spectrum

Select the appropriate tone in Phase 0 based on the content type:

### Option A: Narrative / Story-Driven
*Best for: Migrations, upgrades, major refactors, or incidents.*
- **Focus:** The journey of resolving a difficult problem.
- **Structure:** Before-After-Bridge (BAB). Problem → unexpected blocker → solution → lesson.
- **Real Excerpt:**
  > *"What began as a simple version upgrade became a comprehensive overhaul of our GraphQL implementation. By switching to Declarative cache IDs, adding `__typename` to all operations, and properly handling cache exceptions, we've significantly improved the cache hit of our Apollo GraphQL integration."*
  *(Medium Engineering, Apollo 4 Migration)*

### Option B: Systems-Thinking / Framework
*Best for: System architectures, mental models, or custom frameworks.*
- **Focus:** Deciphering high-level design decisions and organizational impact.
- **Structure:** Hook → component maps → structural choice → business results.
- **Real Excerpt:**
  > *"At Netflix, our messaging platform faces a similar challenge every day. We send hundreds of millions of personalized notifications... This creates a central tension: optimizing each notification for near-term engagement can conflict with what is best for the member over the long term."*
  *(Netflix TechBlog, Notification System)*

### Option C: Practitioner Playbook
*Best for: Technical tutorials, workflows, custom tooling, or guidelines.*
- **Focus:** "Show, don't tell." Actionable steps, runbooks, and repeatable code patterns.
- **Structure:** Problem → components → lessons → next steps.
- **Real Excerpt:**
  > *"An Agent skill is a Markdown file (stored in `.agents/skills/`) that teaches the AI a specific workflow. It's not a template, it's closer to a runbook: 'here are the files involved, here's the order of operations, here are the patterns to follow, here's the checklist to verify.'"*
  *(Medium Engineering, AI Agent Skills)*

---

## 3. Paragraph Shape

Maintain these visual and pacing targets:

- **Introductory Paragraph:** Keep the first sentence under 15 words. Raise a question or state a surprising tension. No fluff.
- **Body Paragraph:** Include 1-2 concrete code references or metrics. Vary sentence length.
- **Closing Paragraph:** Avoid summarizing the section. End on a forward-leaning hook or the most interesting technical takeaway.
