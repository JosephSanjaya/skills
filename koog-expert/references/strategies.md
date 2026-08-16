# Strategy graphs

<instructions>
Directed typed graph. Edges fire in definition order; first match wins. All paths → `nodeFinish`. Unique names if Persistence on.
</instructions>

## Built-ins first

```kotlin
singleRunStrategy(parallelTools = false)
singleRunStrategyWithHistoryCompression(config)
reActStrategy(reasoningInterval = 1)
```

Custom graph only for stream / extra nodes / subgraphs / threshold compress.

## Tool loop

```kotlin
val loop = strategy<String, String>("support") {
    val callLLM by nodeLLMRequest()
    val execute by nodeExecuteTools(parallel = true)
    val send by nodeLLMSendToolResults()
    edge(nodeStart forwardTo callLLM)
    edge(callLLM forwardTo execute onToolCalls { true })
    edge(callLLM forwardTo nodeFinish onTextMessage { true })
    edge(execute forwardTo send)
    edge(send forwardTo execute onToolCalls { true })
    edge(send forwardTo nodeFinish onTextMessage { true })
}
```

Multi-tool msgs: `nodeLLMRequestMultiple` / `nodeExecuteMultipleTools(parallelTools=true)` / `nodeLLMSendMultipleToolResults` + `onMultipleToolCalls` / `onAssistantMessage`. Finish often `transformed { it.first() }`.

Streaming: `nodeLLMRequestStreaming` + `nodeLLMSendToolResultsStreaming` (+ `.transform { stream.toMessageResponse() }` if needed).

## Conditions

| Helper | Meaning |
|---|---|
| `onToolCalls { true }` | tools requested |
| `onTextMessage { true }` | plain assistant text |
| `onAssistantMessage { true }` | assistant (multi-call APIs) |
| `onCondition { }` | any; use `llm.readSession` for size |

Specific edges before catch-alls. `historyIsTooLong()` helper on `AIAgentContext` keeps edges readable.

## Subgraphs

```kotlin
val collect by subgraph<String, String>("collect") { }
val decide by subgraphWithTask<In, Out>(/* limited tools */) { }
```

`subgraphWithTask` hides unused schemas (token win). Compress **between** subgraphs.

## Wire agent

```kotlin
AIAgent(
    promptExecutor = executor,
    strategy = loop,
    agentConfig = AIAgentConfig(
        prompt = prompt("support") { system("…") },
        model = OpenAIModels.Chat.GPT4o,
        maxAgentIterations = 20,
    ),
    toolRegistry = registry,
)
// or short: AIAgent(promptExecutor, llmModel, strategy, toolRegistry, systemPrompt, maxIterations = 20)
```

## Persistence

```kotlin
install(Persistence) {
    storage = InMemoryPersistenceStorageProvider()
    enableAutomaticPersistence = true
}
```

Checkpoint after named nodes. `RollbackToolRegistry` for side effects. Non-serializable handles won't restore.

<constraints>
onToolCalls { true } for parallel safety. Unique node names + session ids with Persistence.
Every path must reach nodeFinish; set maxAgentIterations.

Must follow format above. Output only actionable Kotlin/API guidance.
</constraints>
