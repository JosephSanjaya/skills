# Subagent Token Mitigation & Caching Optimization

Maximize prefix caching (90% discount). Minimize subprocess startup overhead.

## 1. 4-Layer Subprocess Isolation
Spawning Claude CLI as subprocess can inject 50K+ tokens of global overhead (global `CLAUDE.md`, plugins, MCP definitions). Implement 4 layers of containment:

1.  **Scoped CWD**: Set subprocess current working directory (cwd) to dedicated folder (e.g. `.mama/workspace`) to block global `~/CLAUDE.md`.
2.  **Git Tree Boundary**: Write mock `.git/HEAD` file inside the scoped workspace directory to stop Claude Code from walking up to home directory.
3.  **Empty Plugin Directory**: Pass `--plugin-dir` pointing to empty folder.
4.  **Exclude Global Settings**: Pass `--setting-sources project,local` CLI flag.

*Result*: Startup overhead cut from 50K to ~5K tokens (10x savings).

## 2. Persistent Process Streams
Stateless one-shot commands (`claude -p "<prompt>"`) force re-transmission of history and tool schemas. 
*Fix*: Use persistent, live process stream with JSON communication:
```bash
claude --print --input-format stream-json --output-format stream-json --session-id <id>
```
Keep stream alive. Feed messages through stdin. Cache is preserved; schemas sent once on startup.

## 3. Tool Definition Stability
Adding, removing, or reordering tools mid-session breaks prompt cache.
*   **Sort Alphabetically**: Sort tool schemas alphabetically by name before registration.
*   **Locked Tools**: Never alter toolset mid-session. Lock at turn 1.
*   **Lightweight Stubs**: Represent rarely-used tools as stubs with `"defer_loading": true`. Load full schema on-demand via a `ToolSearch` helper message downstream.

## 4. Context Engineering & Loop Caching
*   **`<system-reminder>` Tags**: Changing system prompt (date, git status) breaks cache. Avoid this by freezing system prompt. Inject dynamic updates inside user messages using `<system-reminder>` tags:
    ```json
    {
      "role": "user",
      "content": "<system-reminder>\n# currentDate\nToday is 2026-06-24.\n</system-reminder>\n\nMy prompt text here"
    }
    ```
*   **Dynamic Loop Caching**: Put single `cache_control` checkpoint at very end of latest User message or ToolResult.
*   *Why*: User/ToolResult inputs are deterministic and stable. Assistant messages are streamed and unstable as cache anchors.
*   *Result*: 90% discount on reading history. Input costs cut by 59% (5-turn loops) to 71% (long workflows).
