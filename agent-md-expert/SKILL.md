---
name: agent-md-expert
description: "Expert guidance for creating, auditing, and maintaining minimal, cache-friendly, and structure-decoupled context files (AGENTS.md and CLAUDE.md). Trigger this skill when the user mentions context files, repo rules, agents.md, claude.md, prompt optimization, or wants to check agent instructions."
---

# Agent MD Expert

Expert guide to build, audit, and maintain minimal, cache-aligned repository context files (AGENTS.md / CLAUDE.md). Cut token usage while boosting success rate.

<instructions>
Minimize context files ruthlessly. Place static content at start, dynamic variables at end to preserve prefix caching. Eliminate duplicate files/overviews. Use python validator to check constraints.
</instructions>

## 1. Decision Matrix

| Task / Context | Action | Reference |
| :--- | :--- | :--- |
| **Analyze / Audit context file** | Run Python lint script | [scripts/validate_agent_md.py](file:///Users/jsanjaya/Projects/skills/agent-md-expert/scripts/validate_agent_md.py) |
| **Cache & Alignment optimization** | Static-first layout; append-only | [references/caching-and-positioning.md](file:///Users/jsanjaya/Projects/skills/agent-md-expert/references/caching-and-positioning.md) |
| **Pruning redundancy** | Remove overviews, linters, standard rules | [references/minimization-and-redundancy.md](file:///Users/jsanjaya/Projects/skills/agent-md-expert/references/minimization-and-redundancy.md) |
| **Monorepo setup (Spine + Leaf)** | Root Spine rules + subdir Leaf overrides | [references/monorepo-spine-leaf.md](file:///Users/jsanjaya/Projects/skills/agent-md-expert/references/monorepo-spine-leaf.md) |

---

## 2. Core Rules

<rules>
- **No directory overviews:** Delete all folder trees and architecture lists. Agents discover files automatically via tools.
- **Zero redundancy:** Never duplicate README, CONTRIBUTING, or configs (e.g. package.json). Redundancy reduces success rate by 3% and raises costs 20%+.
- **Keep it short:** Target <800 words (<150 lines). If too long, prune generic advice (e.g. "write clean code").
- **Exact tooling commands:** State exact command strings for testing/formatting/linting (1.6-2.5x compliance increase).
- **Static-first caching:** Place static directives at top. Append updates to bottom. Never put volatile variables (dates, IDs) in first 1000 tokens.
- **Spine & Leaf hierarchy:** Monorepo uses root `AGENTS.md` (Spine) for defaults and subdirectory `AGENTS.md` (Leaf) for package-specific rules.
- **CLAUDE.md Bridge:** Claude Code reads `CLAUDE.md`. Symlink or import via `@AGENTS.md` to avoid duplication.
</rules>

---

## 3. Auditing Workflow

1. Run the Python validator script:
   ```bash
   python3 /Users/jsanjaya/Projects/skills/agent-md-expert/scripts/validate_agent_md.py <path/to/AGENTS.md>
   ```
2. Review issues (HIGH/MEDIUM/LOW) and trim the file.
3. Replace descriptive paragraphs with direct, imperative bullet lists.
4. Ensure no information duplicates the project's existing Markdown files.

---

## 4. Samples

*   [Spine (Root) Template](file:///Users/jsanjaya/Projects/skills/agent-md-expert/samples/spine-agents.md) — Base root configuration.
*   [Leaf (Subdir) Template](file:///Users/jsanjaya/Projects/skills/agent-md-expert/samples/leaf-agents.md) — Directory-specific Electron/IPC constraints.

<constraints>
- Outputs must conform only to the validation rules.
- You should run the python validation script on all edited context files.
- The output format must be minimal and under 800 words.
</constraints>

<context>
Target Path: {target_path}
Dynamic Inputs: {dynamic_inputs}
</context>
