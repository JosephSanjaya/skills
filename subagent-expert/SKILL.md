---
name: subagent-expert
description: "Expert guidance for designing, building, orchestrating, and optimizing Claude Code subagents. Make sure to use this skill whenever the user mentions subagents, multi-agent systems, agent delegation, task routing, or the Agent SDK, even if they only ask for a basic agent definition."
---

# Subagent Expert — 2026 High-Performance Agentic Design

<instructions>
Isolate context. Prevent dilution. Keep parent thread clean. Use subagents as ephemeral, role-scoped context boundaries. Drop filler and articles. Express guidelines using compressed smart caveman style.
</instructions>

## 1. Quick Decision Matrix

| Task Nature | Design Choice | Target Topology | Key Reason |
| :--- | :--- | :--- | :--- |
| **Breadth-first read/explore** | Subagents | Fan-out/fan-in | Parallelize reads. Zero parent context bloat. |
| **Sequential dependencies** | Single Agent | Prompt chaining | Actions carry implicit decisions. Avoid split decisions. |
| **Relational data / comparison** | Subagents | Map-reduce-and-manage | Clean inputs, structured aggregation. |
| **Stateful edits / coding** | Single Writer | Code-Review-Loop | Parallel writes cause merge/AST conflicts. |
| **Unpredictable steps** | Subagents | Orchestrator-workers | Lead plans; specialized workers execute. |
| **Strict validation needed** | Subagents | Evaluator-optimizer | Prevent simulated success via adversarial check. |

## 2. Directory Structure

<context>
Specialized guidelines partitioned to prevent token bloat:

* **References**:
  * [architecture.md](references/architecture.md) — Topologies, single-writer rule, concurrency scaling rules.
  * [configuration.md](references/configuration.md) — Frontmatter specs, programmatic SDK (Python/TS), CLI flags, model routing.
  * [failures-mitigations.md](references/failures-mitigations.md) — 14 MAST failures, simulated success fixes, loop detection, worktrees.
  * [token-caching.md](references/token-caching.md) — 4-layer subprocess isolation, persistent streams, caching checkpoints, tool stability.
* **Auditor**:
  * [checklist.md](auditor/checklist.md) — Self-auditing checklists for subagent definitions.
* **Samples**:
  * [custom_subagent.md](samples/custom_subagent.md) — Reference read-only auditor subagent markdown.
  * [sdk_orchestration.py](samples/sdk_orchestration.py) — Python SDK subagent loop implementation.
* **Scripts**:
  * [audit_subagent.py](scripts/audit_subagent.py) — Automated python auditing tool.
</context>

<constraints>
Always read the specific file containing the details required for the task. Maintain strict token efficiency. Never bloat the parent context.
</constraints>
