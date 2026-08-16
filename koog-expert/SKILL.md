---
name: koog-expert
description: "Expert guide for JetBrains Koog (Kotlin AI agents). Use whenever the user mentions Koog, AIAgent, ToolRegistry, strategy graphs, koog-ktor, history compression, MCP tools, structured LLM output, or building agents in a Ktor backend, Spring Boot service, Android/iOS/desktop KMP app, JS, or WasmJS. Also use for token/cost control, prompt caching, Persistence checkpoints, agents-test mocks, and choosing single-run vs ReAct vs custom graphs. Prefer this skill over generic LangChain/Python agent patterns."
---

# Koog Expert

<instructions>
Koog = KMP typed state-machine agents (not prompt chains). Ground truth: **1.1.1** source — `promptExecutor=` (Context7/docs often stale `executor=`).

Load **one** matching reference. Run audit scripts before pasting examples. Never dump full refs into the reply.
</instructions>

## Refs

| Need | File |
|---|---|
| Modules / layout / shapes | [architecture.md](references/architecture.md) |
| Ktor SSE / YAML / DI | [ktor-backend.md](references/ktor-backend.md) |
| Android / iOS / desktop / JS | [apps-kmp.md](references/apps-kmp.md) |
| `@Tool` / MCP / A2A | [tools-mcp.md](references/tools-mcp.md) |
| Cost / compress / cache / structured | [tokens.md](references/tokens.md) |
| Graphs / ReAct / parallel | [strategies.md](references/strategies.md) |
| `getMockExecutor` / graph tests | [testing.md](references/testing.md) |
| Tool drops / locks / providers | [pitfalls.md](references/pitfalls.md) |

Kernels: [examples/](examples/) (`hello_agent`, `ktor_plugin`, `tools`, `graph_compress`).

## Pick smallest agent

1. Chat/tools → `AIAgent(promptExecutor, llmModel, …)` → `singleRunStrategy()`
2. Reasoning between tools → `reActStrategy()`
3. Long/costly → `singleRunStrategyWithHistoryCompression(HistoryCompressionConfig(…))`
4. Branch/stream/compress edges → `strategy { }`
5. Ktor → `install(Koog)` + `aiAgent(input, model)`
6. Mobile/desktop cloud → backend only (no keys in binary)

## Non-negotiables (1.1.1)

- `promptExecutor` only — never `executor`
- Explicit `maxIterations` / `maxAgentIterations` (default 50)
- One `AIAgent` / request; share `PromptExecutor` + `ToolRegistry`
- Compress on threshold — not every LLM call
- Filtered `onToolCalls` drops parallel tools → `{ true }` or `nodeExecuteTools(parallel=true)`
- Heavy I/O outside `llm.writeSession { }`
- Env keys. MCP + Bedrock = JVM-only

## Gradle

```kotlin
dependencies {
    implementation("ai.koog:koog-agents:1.1.1")
    implementation("ai.koog:koog-ktor:1.1.1") // Ktor only
    testImplementation("ai.koog:agents-test:1.1.1")
}
```

Beta: `koog-agents-additions`. JDK 17+, Kotlin 2.3.10+.

## Runtime token playbook

1. Static system+tools first (prefix cache)
2. `subgraphWithTask` hides unused schemas
3. Parallel tools (`parallel=true`)
4. Compress ~200 msgs / 200_000 chars; cheap `retrievalModel`
5. Tasks → `FactRetrieval`; chat → `WholeHistory` / `FromLastNMessages`
6. `nodeLLMRequestStructured<T>()` over free-text JSON
7. Tokenizer / OTel day one → [tokens.md](references/tokens.md)

## Scripts

```bash
!python3 ~/.claude/skills/koog-expert/scripts/audit_koog.py .
!bash ~/.claude/skills/koog-expert/scripts/check_koog_deps.sh .
```

Docs: https://docs.koog.ai/ · https://api.koog.ai/ · Context7 `/websites/koog_ai` (may lag)

<constraints>
Must verify APIs against 1.1.1 only — never invent from LangChain/Python.
Must use one AIAgent per HTTP request; never share write-sessions across users.
Keys only from env; never embed in mobile/desktop binaries.
Compress only on threshold; output must cite the reference used (@file:line) and prefer !command over prose dumps.
After large tasks use /compact or /clear.
</constraints>
