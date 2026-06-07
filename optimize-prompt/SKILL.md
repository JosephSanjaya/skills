---
name: optimize-prompt
description: "Optimize Claude Code and LLM prompts for token efficiency, prefix caching compliance, positional recall, and execution correctness. Use when writing/reviewing prompts, debugging agent errors/failures, managing context windows, selecting effort levels, choosing MCP vs CLI tools, designing subagents, or editing CLAUDE.md. Triggers: 'optimize my prompt', 'prompt is too expensive', 'agent keeps reading wrong files', 'how should I structure this prompt', 'context window filling up', 'how to use Plan Mode', 'when to use subagents', 'MCP vs CLI', 'effort level', 'prompt structure', 'high-signal prompt', '/clear vs /compact', 'CLAUDE.md best practices', 'audit prompt', 'review prompt', 'optimize skill', 'check caching', 'prompt design check', 'token usage', 'reduce tokens', 'optimize context', 'API costs', 'context window', 'prompt compression', 'token efficiency', 'cache strategy', 'LTL', 'symbolic language', 'caveman mode', 'hybrid caching', 'AtomicRAG', 'Claw Compactor'."
---

# Optimize Prompt & Review Skill

This skill provides workflow guidance and automated tooling to audit, analyze, compress, and optimize LLM prompts, instructions, and Claude Code environments for maximum token efficiency and reasoning accuracy.

<instructions>
Delineate prompts with XML tags, enforce append-only prefix caching alignment, select iterative effort levels, utilize symbolic abbreviations/protocols, and implement Prism Prompting constraints.
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
├── Run Heuristic Auditor → Run python tool (scripts/audit_prompt.py)
├── Analyze Token Usage → Run python tool (scripts/analyze_token_usage.py)
└── Compress Prompt/Code → Run python tool (scripts/compress_prompt.py)
```

---

## 2. Quick Start Workflow

To analyze and optimize a prompt:

1.  **Run Automated Heuristic Audit**:
    Execute the Python auditor on the prompt string, stdin, or file:
    ```bash
    python scripts/audit_prompt.py <path/to/prompt.txt>
    ```
2.  **Analyze Token/Session Cost**:
    Analyze token distribution of files or conversation history files (.json):
    ```bash
    python scripts/analyze_token_usage.py <path/to/prompt.txt_or_history.json>
    ```
3.  **Compress Prompt / Apply Shorthand**:
    Compress prompt text by removing filler words, pleasantries (Caveman Mode), and optionally applying symbolic Less-Token-Language (LTL):
    ```bash
    python scripts/compress_prompt.py <path/to/prompt.txt> --symbolic --caveman
    ```
4.  **Apply Automated Corrections**:
    Use the `--fix` parameter to programmatically clean up politeness, persona placebo, and caching order:
    ```bash
    python scripts/audit_prompt.py <path/to/prompt.txt> --fix <path/to/optimized_prompt.txt>
    ```
5.  **Validate Bounded Context**:
    Ensure the prompt uses `@file:line` for targeting and `!command` for diagnostic output instead of prose.

---

## 3. Reference Documentation Index

For details on API configurations, token economics, and LLM constraints, read these references:

*   [knowledge.md](file:///Users/jsanjaya/Projects/skills/optimize-prompt/references/knowledge.md): Attention dilution, lost-in-the-middle positioning bias, prefix caching, and tokenization fertility.
*   [examples.md](file:///Users/jsanjaya/Projects/skills/optimize-prompt/references/examples.md): Copy-pasteable good/bad prompt layouts, Outlines CFGs, Pydantic AI models, Zod schemas, and vLLM/LMCache configurations.
*   [prompt-framework.md](file:///Users/jsanjaya/Projects/skills/optimize-prompt/references/prompt-framework.md): Five-pillar templates, bug triage protocols, XML tags, effort levels, context operators, and CLAUDE.md/MCP/commands structures.
*   [context-management.md](file:///Users/jsanjaya/Projects/skills/optimize-prompt/references/context-management.md): Token budgets, slash commands (`/clear`, `/compact`), CLAUDE.md size rules, compaction, and session reset guidelines.
*   [subagents-and-scaling.md](file:///Users/jsanjaya/Projects/skills/optimize-prompt/references/subagents-and-scaling.md): Subagent delegation config, horizontal project scaling, and MCP vs CLI token cost benchmarks.
*   [edge-cases.md](file:///Users/jsanjaya/Projects/skills/optimize-prompt/references/edge-cases.md): Context decay symptoms, lossy compaction, and sync conflicts.
*   [symbolic-languages.md](file:///Users/jsanjaya/Projects/skills/optimize-prompt/references/symbolic-languages.md): Mathematical operators, LTL (Less-Token-Language), Hieratic shorthand, Caveman protocol, and Wenyan-lang mode.
*   [algorithmic-compression.md](file:///Users/jsanjaya/Projects/skills/optimize-prompt/references/algorithmic-compression.md): Secondary model prompt compression (LLMLingua), Dynamic Memory Sparsification (DMS), and AST-aware Claw Compactor.
*   [architectural-patterns.md](file:///Users/jsanjaya/Projects/skills/optimize-prompt/references/architectural-patterns.md): Core architectural patterns for token efficiency including AtomicRAG, Spine Architecture, Subagent Forking, and Modular Context Loading.
*   [data-formats.md](file:///Users/jsanjaya/Projects/skills/optimize-prompt/references/data-formats.md): Token density comparison across Markdown, YAML, JSON, XML, and TOON (Token-Oriented Object Notation).
*   [caching-strategies.md](file:///Users/jsanjaya/Projects/skills/optimize-prompt/references/caching-strategies.md): Ephemeral prefix caching, semantic caching with embeddings, VectorQ adaptive thresholds, and hybrid multi-layer caching.

<constraints>
Developers must use this schema to verify cache alignments and format outputs before execution.
</constraints>
