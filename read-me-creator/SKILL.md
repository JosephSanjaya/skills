---
name: read-me-creator
description: |
  Creates high-quality README and how-to documentation. Use when user says "create a README",
  "write a README", "make a how-to", "document this project", "create setup guide", "write
  installation guide", "help me document", or provides a project description and asks for docs.
  Produces structured, EPPO-compliant documentation following Google/Microsoft writing standards.
  Adapts output to doc type: OSS library, internal tool, API service, CLI tool, or how-to guide.
  Applies progressive disclosure, short Quickstart first with details linked.
---

<intake_flow>
### Intake Flow
Before writing, infer or ask these 4 parameters:
1. **Doc type** — OSS library / internal tool / API service / CLI tool / how-to guide
2. **Audience** — external users, internal team, contributors, mixed
3. **Complexity** — simple (skip architecture/roadmap) vs. complex (full 15 sections)
4. **What exists** — project description, codebase, partial draft, or nothing

*Rule:* If the user provides a project description or codebase, infer all 4 parameters and proceed directly to execution without asking.
</intake_flow>

<execution_workflow>
### Execution Steps

#### Step 1 — Select Template
Pick the base template from `assets/`:
- `template-oss-library.md` → OSS library or public-facing project
- `template-internal-tool.md` → internal tool, script, or team utility

For API service / CLI tool: start from `template-oss-library.md`, remove Architecture and Roadmap.
For how-to guide: use only Title, Prerequisites, Steps, Usage, Troubleshooting.

#### Step 2 — Populate Sections
Apply the section selection table from `references/readme-structure.md`.

*Always include:*
- One-sentence tagline in the title block
- Prerequisites table (eliminates "silent blockers")
- Copy-paste-ready commands in Setup and Usage
- At least one Troubleshooting entry with exact error message + fix

*Skip if no data:* Architecture diagram, Roadmap, Acknowledgements.

#### Step 3 — Apply Writing Standards
Apply style guidelines from `references/writing-standards.md`:
- One idea per sentence; active voice; present tense for instructions.
- Remove filler words: simply, easily, just, basically.
- Provide real usage examples (avoid "Hello World" placeholders).
- Define all acronyms on first use.

#### Step 4 — Validate Path-to-Value
Count setup steps. If >12: split the overflow to a linked document.
Prefer one-liner setup: `git clone URL && cd REPO && INSTALL && RUN`
</execution_workflow>

<quick_reference>
### Section Quick Reference

| Need | Section | Key Rule |
|------|---------|----------|
| Hook reader in 5 sec | Title + tagline | One sentence, no buzzwords |
| Eliminate env blockers | Prerequisites | Table with exact version numbers |
| First working state | Setup / Quickstart | ≤12 steps; one-liner where possible |
| Show real value | Usage | Copy-paste example of core feature |
| Cover unhappy path | Troubleshooting | Quote exact error messages |
| Legal clarity | License | Always required for OSS |

For full blueprints, refer to:
- `references/readme-structure.md` (15-section blueprint)
- `references/writing-standards.md` (Google/Microsoft style rules)
</quick_reference>

<output_format>
### Output Format Constraints
- Deliver the README as a fenced markdown block for direct copying.
- If multiple files are needed (e.g. `CONTRIBUTING.md`), output them sequentially in their own fenced blocks with filename headers.
- Do not explain what you wrote. Output the document directly.
</output_format>
