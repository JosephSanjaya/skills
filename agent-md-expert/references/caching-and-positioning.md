# Caching & Positioning Optimization

## Attention Curves & Positioning Bias
- **Lost-in-the-Middle (Liu et al., 2023):** LLMs recall information best when it is placed at the absolute start or absolute end of the prompt context. Information buried in the middle experiences significant attention decay.
- **Attention Sinks (StreamingLLM, Xiao et al., 2023):** Models allocate disproportionate attention to the initial tokens of a sequence. Put load-bearing constraints and high-priority commands at the very top.
- **Context Rot (Modarressi et al., 2025):** At 32K tokens, 11 of 13 models experience accuracy drops below 50% of short-context baseline. Keep context files minimal so they don't consume critical attention budget needed for the active task.

## KV Prefix Caching Mechanics
KV prefix caching (e.g., Anthropic Prompt Caching, vLLM Automatic Prefix Caching) saves state for identical token prefixes.
- **Prefix-Exact & Hash-Based:** The cache match must be identical character-for-character up to the cache breakpoint.
- **Cache Economics:** Anthropic cache writes cost 1.25x-2x of base input; cache reads cost only 0.1x (90% savings). Cache hits yield up to 85% latency reduction.

## Cache-Friendly Layout Rules
1. **Static-First, Dynamic-Last:** Place the unchanging `AGENTS.md` content at the absolute top of the prompt. Place dynamic parameters (session IDs, dates, user request details) below the static block.
2. **Append-Only Modifications:** To update instructions, append to the bottom. Editing the middle or top invalidates the entire cached prefix sequence following the edit.
3. **Eliminate Volatile Tokens:** Never place dynamic variables (e.g. current date, run ID, branch name) near the beginning of the file, as it causes a 100% cache miss.
