---
name: optimize-prompt
description: Optimize Claude Code and LLM prompts for token efficiency, prefix caching compliance, positional recall, and execution correctness. Use when writing/reviewing prompts, debugging agent errors/failures, managing context windows, selecting effort levels, choosing MCP vs CLI tools, designing subagents, or editing CLAUDE.md. Triggers: "optimize my prompt", "prompt is too expensive", "agent keeps reading wrong files", "how should I structure this prompt", "context window filling up", "how to use Plan Mode", "when to use subagents", "MCP vs CLI", "effort level", "prompt structure", "high-signal prompt", "/clear vs /compact", "CLAUDE.md best practices", "audit prompt", "review prompt", "optimize skill", "check caching", "prompt design check".
---

# Optimize Prompt & Review Skill

This skill provides workflow guidance and automated tooling to audit and optimize LLM prompts, instructions, and Claude Code environments.

<instructions>
Delineate prompts with XML tags, enforce append-only prefix caching alignment, select iterative effort levels, and implement Prism Prompting constraints.
</instructions>

---

## 1. Quick Decision Tree

```
What do you need?
├── Fix a bug → Bug Triage Protocol (references/prompt-framework.md)
├── Add a feature → Incremental First-Step pattern (references/examples.md)
├── Explore large codebase → Subagent delegation (references/subagents-and-scaling.md)
├── Session is getting slow/expensive → Context hygiene (references/context-management.md)
├── Agent ignoring instructions → Context decay recovery (references/edge-cases.md)
└── Run Heuristic Auditor → Run python tool (scripts/audit_prompt.py)
```

---

## 2. Quick Start Workflow

To analyze and optimize a prompt:

1.  **Run Automated Heuristic Audit**:
    Execute the Python auditor on the prompt string, stdin, or file:
    ```bash
    python scripts/audit_prompt.py <path/to/prompt.txt>
    ```
2.  **Apply Automated Corrections**:
    Use the `--fix` parameter to programmatically clean up politeness, persona placebo, and caching order:
    ```bash
    python scripts/audit_prompt.py <path/to/prompt.txt> --fix <path/to/optimized_prompt.txt>
    ```
3.  **Validate Bounded Context**:
    Ensure the prompt uses `@file:line` for targeting and `!command` for diagnostic output instead of prose.

---

## 3. Reference Documentation Index

For details on API configurations, token economics, and LLM constraints, read these references:

*   [knowledge.md](file:///Users/jsanjaya/.gemini/config/skills/optimize-prompt/references/knowledge.md): Attention dilution, lost-in-the-middle positioning bias, prefix caching, and tokenization fertility.
*   [examples.md](file:///Users/jsanjaya/.gemini/config/skills/optimize-prompt/references/examples.md): Copy-pasteable good/bad prompt layouts, Outlines CFGs, Pydantic AI models, Zod schemas, and vLLM/LMCache configurations.
*   [prompt-framework.md](file:///Users/jsanjaya/.gemini/config/skills/optimize-prompt/references/prompt-framework.md): Five-pillar templates, bug triage protocols, XML tags, effort levels, and context operators.
*   [context-management.md](file:///Users/jsanjaya/.gemini/config/skills/optimize-prompt/references/context-management.md): Token budgets, slash commands (`/clear`, `/compact`), CLAUDE.md size rules, and hooks.
*   [subagents-and-scaling.md](file:///Users/jsanjaya/.gemini/config/skills/optimize-prompt/references/subagents-and-scaling.md): Subagent delegation config, horizontal project scaling, and MCP vs CLI token cost benchmarks.
*   [edge-cases.md](file:///Users/jsanjaya/.gemini/config/skills/optimize-prompt/references/edge-cases.md): Context decay symptoms, lossy compaction, and sync conflicts.

<constraints>
Developers must use this schema to verify cache alignments and format outputs before execution.
</constraints>
