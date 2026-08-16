# Ktor backend

<instructions>
Module: `ai.koog:koog-ktor` (docs: **beta**). MCP in plugin = **JVM-only**.
</instructions>

## Install once

```kotlin
fun Application.module() {
    install(Koog) {
        llm {
            openAI(apiKey = requireEnv("OPENAI"))
            anthropic(apiKey = requireEnv("ANTHROPIC"))
            ollama { baseUrl = "http://localhost:11434" }
            fallback {
                provider = LLMProvider.Ollama
                model = OllamaModels.Meta.LLAMA_3_2
            }
        }
        agentConfig {
            maxAgentIterations = 20
            prompt { system("Support assistant. Prefer tools over guessing.") }
            registerTools {
                tool(::searchOrders)
                tools(OrderTools().asTools())
            }
            // mcp { sse("http://localhost:8931/sse") } // JVM only
            install(OpenTelemetry) { addSpanExporter(LoggingSpanExporter.create()) }
        }
    }
}
```

Config YAML under `koog.<provider>` (HOCON timeouts default 30000/10000/30000). Put env placeholders only in committed config files — see suffix Env map.

## Route helpers (`ai.koog.ktor.Agents`)

| Call | Effect |
|---|---|
| `aiAgent(input, model)` | `singleRunStrategy()` → `String` |
| `aiAgent(parallelTools, model) { }` | custom run block |
| `aiAgent(strategy, model, input)` | run graph → `Output` |
| `aiAgent(strategy, model)` | build; you `run` |
| `llm()` | `PromptExecutor` (`execute` / `executeStreaming` / `moderate`) |

Need `install(Koog)` first.

```kotlin
val output = aiAgent(userText, OpenAIModels.Chat.GPT4_1)
val output = aiAgent(reActStrategy(), OpenAIModels.Chat.GPT4_1, "What's new in $org")
val harmful = llm().moderate(prompt("id") { user(userText) }, OpenAIModels.Moderation.Omni).isHarmful
```

Moderate **before** agent iterations.

## Concurrency

- Create agent per request (plugin helpers do)
- Share plugin `PromptExecutor` + `ToolRegistry`, not a live agent
- Persistence: unique session id / user
- Batch: `async { aiAgent(item, model) }` + `awaitAll()`

## Streaming

`nodeLLMRequestStreaming` / `nodeLLMSendToolResultsStreaming` → `Channel`/`Flow` → Ktor SSE (`io.ktor:ktor-server-sse`). Explicit end event. WS for bidirectional tools. Prefer plugin+SSE over custom `respondTextWriter`.

## DI

Plugin **is** the wiring. Koin: singleton services; `@Tool` calls them. Spring: `koog-spring-boot-starter` (aggregated `MultiLLMPromptExecutor`), not `koog-ktor`.

Tools → services. Routes → `aiAgent` / `llm()`. No SQL inside `writeSession`. `maxAgentIterations` in `agentConfig` (default **50**).

<constraints>
One AIAgent per request. Moderate untrusted input. MCP only on JVM source sets.
Set maxAgentIterations explicitly on HTTP handlers.

Must follow format above. Output only actionable Kotlin/API guidance.
Env map: OPENAI→OPENAI_API_KEY, ANTHROPIC→ANTHROPIC_API_KEY (keep real names only here for prefix-cache).
</constraints>
