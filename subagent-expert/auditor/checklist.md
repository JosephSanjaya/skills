# Subagent Definition Audit Checklist

Terse, actionable checklist. Run before deploying any subagent.

## 1. Frontmatter Validation
- `[ ]` Name kebab-case, lowercase (e.g. `auth-security-scanner`).
- `[ ]` Description present. Action-oriented, pushy, details clear triggers.
- `[ ]` Tools list explicit. Least privilege.
- `[ ]` Model specified (e.g. `sonnet` for code, `haiku` for read-only scans).
- `[ ]` `maxTurns` set to 10-15.
- `[ ]` If parallel write risks exist, `isolation: worktree` set.

## 2. Prompt & Boundary Check
- `[ ]` Prompt defines clear role and strict expertise area.
- `[ ]` Prompt defines explicit, structured output format (JSON / Markdown).
- `[ ]` Prompt defines strict task boundaries (what agent MUST NOT do).
- `[ ]` Prompt contains no nested spawning (`Agent` tool omitted from allowed tools).
- `[ ]` Unidirectional input handled: delegation prompt contains all needed context.
- `[ ]` Bounded Prompt Path Absolute-Referencing applied (absolute file/directory paths passed to prevent exploratory turns).

## 3. Verification & Safety
- `[ ]` Automated validation gate configured (e.g. linter, tests, or critic agent).
- `[ ]` No placeholder instructions.
- `[ ]` No conversational fluff in prompt body.
- `[ ]` No uppercase MUST/NEVER without clear engineering "why".
- `[ ]` Timing and token budgets planned.
