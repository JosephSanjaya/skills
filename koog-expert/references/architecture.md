# Architecture

<instructions>
Smallest surface that ships. Do not install every Koog module.
</instructions>

## Pipeline

```
HTTP/UI/CLI → AIAgent (1 per request/session)
  → Strategy (graph|functional|planner)
  → Pipeline + Feature (trace, persistence, tokenizer, OTel)
  → ToolRegistry → Environment
  → PromptExecutor → LLMClient(s)  [RetryingLLMClient, MultiLLM]
```

| Piece | Role |
|---|---|
| `AIAgent` | Factory → Graph / Functional / Planner |
| `AIAgentConfig` | Prompt, model, `maxAgentIterations` |
| `AIAgentStrategy` | Typed graph: start → nodes → finish |
| `ToolRegistry` | Tools + JSON schema; merge with `+` |
| `AIAgentEnvironment` | Sole tool execution path |
| `PromptExecutor` | Provider seam (Single / Multi) |
| `AIAgentFeature` | `install(Feature) { }` |
| `AIAgentService` | Factory for many agents; still 1 run / session |

## Modules

Umbrella: `ai.koog:koog-agents`. Add only when used:

| Module | When |
|---|---|
| `koog-ktor` | Ktor plugin |
| `agents-test` | Mock LLM + graph asserts |
| `agents-mcp` | MCP client (JVM) |
| `agents-features-snapshot` | Persistence |
| `agents-features-opentelemetry` | GenAI metrics |
| `agents-features-tokenizer` | Token counts |
| `agents-features-trace` / event-handler | Local debug |
| `prompt-cache-*` | Exact-match response cache |
| `a2a-*` | A2A (not in umbrella) |
| `koog-agents-additions` (beta) | Planners, embeddings, LTM |
| Spring starters | Spring Boot / Spring AI |

Gaps: MCP + Bedrock = JVM. OTel excludes WasmJS.

## Shapes

| Shape | API | Use |
|---|---|---|
| Single-run | default `AIAgent` / `singleRunStrategy(parallelTools)` | Most HTTP tool loops |
| ReAct | `reActStrategy(reasoningInterval=1)` | Extra reasoning turns |
| Functional | `AIAgentFunctionalStrategy` | Tiny scripts |
| Graph | `strategy("name") { }` | Stream, compress edges, subgraphs |
| Planner | `PlannerAIAgent` / GOAP (beta) | Plan/execute to goal |

## Layout (Ktor)

```
Application.kt          # install(Koog)
plugins/ agents/ tools/ services/ routes/
```

KMP: graphs + `@Serializable` models in `commonMain`. LLM clients/keys in `jvmMain` or behind HTTP.

## Sessions

- `llm.readSession { }` — concurrent reads
- `llm.writeSession { }` — exclusive; keep fast

Never share one agent across concurrent Ktor calls.

## Features

```kotlin
AIAgent(promptExecutor, llmModel, maxIterations = 20) {
    handleEvents { onToolCallStarting { }; onAgentCompleted { } }
    install(OpenTelemetry) { }
}
```

`install(Persistence)` = crash recovery, not per-request chat memory. Unique node names + unique session id required.

<constraints>
Prefer one module more only when a feature is used.
Share PromptExecutor/ToolRegistry; never a live AIAgent across requests.

Must follow format above. Output only actionable Kotlin/API guidance.
</constraints>
