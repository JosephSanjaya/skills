# README Structure Reference

## 15-Section Blueprint

### Phase I — Orientation & Identity
1. **Title + Badges** — logo, CI status, version, license badges, one-sentence tagline
2. **Table of Contents** — interactive; skip for <4 sections
3. **About** — the "why": core philosophy and motivation

### Phase II — Capability & Construction
4. **Features** — bulleted scannable list; what it does, not how
5. **Tech Stack** — languages, frameworks, infra (aids discoverability)
6. **Architecture** — Mermaid/diagram for complex systems; skip for simple tools
7. **Project Structure** — key folders/files with one-line purpose

### Phase III — Implementation & Operation
8. **Prerequisites** — versions, system deps, accounts, connectivity (eliminate "silent blockers")
9. **Setup / Quickstart** — clone → install → run; target ≤12 steps; prefer one-liners
10. **Configuration** — env vars, feature flags, database settings (separate from setup)
11. **Usage** — copy-paste examples demonstrating real value; not "Hello World"
12. **Troubleshooting** — common errors with exact messages and fixes; cover the "unhappy path"

### Phase IV — Community & Governance
13. **Security** — standards, vulnerability reporting, known limitations
14. **Contributing** — coding standards, PR process, commit conventions
15. **Roadmap** — active signals and contribution opportunities
16. **License** — always required
17. **Acknowledgements / Authors** — optional; contact info

---

## Section Selection by Doc Type

| Doc Type | Required Sections | Skip |
|----------|------------------|------|
| OSS library | All 15+ | — |
| Internal tool | 1,2,3,5,8,9,10,11,12 | 13,15,17 |
| API service | 1,3,4,5,6,8,9,10,11,12,13 | 15,17 |
| CLI tool | 1,3,4,5,8,9,11,12,16 | 6,15,17 |
| How-to guide | 1,8,9,11,12 | 3,5,6,7,13–17 |

---

## Path-to-Value Rules

- Time to "first working state" must be minimized
- >12 steps → move to separate doc, link from README
- Always test your own instructions from a clean environment
- One-liner preferred: `git clone <url> && cd <repo> && npm install && npm start`
