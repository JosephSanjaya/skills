---
name: commands-creator
description: Create, rewrite, or audit Claude Code custom slash commands (.claude/commands/*.md) as light, consistent, reusable prompts with systematic steps, argument hints, and routing to the best installed skills. Use whenever the user wants a new /command, says "make a slash command for X", "turn this workflow/prompt into a command", "add a command that runs Y", wants to fix or tighten an existing command file, or asks how to structure command frontmatter (arguments, argument-hint, allowed-tools). Not for creating skills (SKILL.md) — use anthropics-skill-creator for that.
---

<instructions>
Command = thin, repeatable entry point: `/name args` runs same systematic procedure every time. Skills hold depth; commands orchestrate. Target: readable in 20s, two runs behave the same.
Scripts dir: `~/.claude/skills/commands-creator/scripts/`.
</instructions>

<step id="1" label="Capture intent">
Pull answers from conversation; ask only gaps, one batch, ≤3 questions:
- Outcome: what `/name` produces.
- Input: argument shape + default when empty.
- Scope: project `<repo>/.claude/commands/` (default when repo has `.claude/`) or user `~/.claude/commands/`.
- Side effects (push, post, delete, deploy) → `disable-model-invocation: true` + confirm step before acting.
Name: kebab-case verb-noun (`review-mr`, `write-tests`). Check clashes in target dir AND skill/built-in names in your context (`/code-review` exists) → rename on clash.
</step>

<step id="2" label="Route to skills">
Reuse beats re-explaining. Sources:
- Available-skills list in your context: authoritative; only place built-ins appear (`code-review`, `simplify`, `security-review`).
- On-disk user/project/plugin skills: `python3 <scripts>/list_skills.py --filter <kw> [<kw> ...]`
One skill covers whole task (e.g. `code-review` for "review my diff") → thin wrapper: pre-inject context, invoke skill with parsed args, enforce scope + output. Lightest form.
Else pick 1–3 skills for sub-tasks by description fit. Reference inside the step needing it: ``invoke Skill `<exact-name>` for <sub-task>; missing → do inline``. Plugin skills: `plugin:skill`. No good fit → inline; never force weak match.
</step>

<step id="3" label="Write">
Read `references/template.md`; follow skeleton exactly. Fixed block order (frontmatter → `<context>`? → `<instructions>` → `<step>`… → `<output>`) makes a suite consistent + scannable.
- description: verb-first, what + when, ≤200 chars. Doubles as `/` menu label and auto-invoke signal.
- argument-hint whenever body reads an argument placeholder (forms in template); mirror parse rule (`"<file> [--fix]"`).
- 3–6 steps, each labeled, ≤5 imperative lines, one decision/action ending in checkable state.
- Verify step before output: run tests/lint/validator or re-check result vs goal.
- `<output>`: exact reply shape; unspecified output drifts between runs.
- Cheap context (branch, status, diff stat) via `!`cmd`` injection, not a "run git status" step. Needs narrow `allowed-tools`.
- Precondition fails → say why, stop. No guessing.
- No generic advice ("best practices", "be thorough"); every line must change behavior. Step needs >5 lines domain knowledge → route to skill.
- Body ≤60 lines target, 80 ceiling.
</step>

<step id="4" label="Validate">
`python3 <scripts>/validate_command.py <command.md> --project-dir <repo>`
Fix every ERROR. WARN = judgment; fix unless reason. Also confirms each ``Skill `x` `` reference is installed.
</step>

<step id="5" label="Report">
Reply: file path, `/name <argument-hint>` usage, skills routed to, one example invocation. No full file paste unless asked.
</step>

<audit>
Existing command → same contract. Read, validate, rewrite onto skeleton: cut generic bullets, collapse to 3–6 steps, add missing hint/verify/output, swap inline domain checklists for skill calls. Result must have fewer words than original — skeleton overhead pays only by replacing inline checklists. Report before/after `wc -w`.
</audit>

<batch>
Multiple commands → same skeleton, shared naming scheme, optional namespace subdir `.claude/commands/<group>/<name>.md` (still invoked `/<name>`). Validate each.
</batch>
