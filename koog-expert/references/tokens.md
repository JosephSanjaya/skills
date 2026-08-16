# Tokens / cost

<instructions>
Compression costs tokens. Trigger when history is large — not every hop.
</instructions>

## When

```kotlin
val historyTooBig: (Prompt) -> Boolean = { p ->
    p.messages.size > 200 ||
        p.messages.sumOf { m ->
            m.parts.filterIsInstance<MessagePart.Text>().sumOf { it.text.length }
        } > 200_000
}
```

Also: `llm.readSession { prompt.latestTokenUsage > threshold }` (docs demo 1000; prod thresholds much higher).

## Strategies (`HistoryCompressionStrategy`)

| API | Keeps | Use |
|---|---|---|
| `WholeHistory` | System + first user + TL;DR | Support chat |
| `WholeHistoryMultipleSystemMessages` | Per system-block TL;DR | Multi-phase prompts |
| `FromLastNMessages(n)` | Last n + TL;DR | Chatty UIs |
| `Chunked(size)` | TL;DR / chunk | Long tool logs |
| `FromTimestamp(t)` | From timestamp | Time-bounded |
| `FactRetrieval(Concept…)` | Structured facts (1 LLM call / concept) | Task/code agents |
| `NoCompression` | All | Tests only |

Prefer companion factories. `Concept(keyword, description, factType=SINGLE|MULTIPLE)` — one topic per concept. `preserveMemory = true` unless intentional. Cheap `retrievalModel` for compress (else = agent model).

## Placement

```kotlin
val compress by nodeLLMCompressHistory<ReceivedToolResults>(
    strategy = HistoryCompressionStrategy.FromLastNMessages(6),
    retrievalModel = OpenAIModels.Chat.GPT4oMini,
    preserveMemory = true,
)
edge(execute forwardTo compress onCondition { llm.readSession { historyTooBig(prompt) } })
edge(execute forwardTo send onCondition { llm.readSession { !historyTooBig(prompt) } })
edge(compress forwardTo send)
```

Between subgraphs: `collect then nodeLLMCompressHistory<String>() then decide`.

Or: `singleRunStrategyWithHistoryCompression(HistoryCompressionConfig(historyTooBig, strategy, cheapModel))`  
Or: `llm.writeSession { replaceHistoryWithTLDR(strategy, preserveMemory = true) }`.

## Prefix cache (Anthropic 1.0+ / similar OpenAI)

Order: **tools → system → messages**. Keep prefix stable. Tool add/remove busts cache. TTL ~5m (or 1h).

## Other levers

- Parallel tools: `nodeExecuteTools(parallel = true)`
- Structured: `nodeLLMRequestStructured<T>()` / `executeStructured<T>()`; `@Serializable` + `@LLMDescription`; pass `examples` if native mode placeholders (#1328)
- Exact cache: `CachedPromptExecutor(InMemory|File|Redis, inner)` — stream hit = one chunk; `moderate` bypasses
- Retry: `RetryingLLMClient(client, RetryConfig.PRODUCTION)` for 5xx/429 only
- Sub-agent-as-tool for smaller contexts
- Metrics: Tokenizer `onTokenUsage`; OTel `gen_ai.client.token.usage`

## Don't

- Compress every iteration
- Huge tool results with no compress
- Swap providers mid-graph without DTO checks (DeepSeek `audioTokens` #755)

<constraints>
Gate compression with onCondition / HistoryCompressionConfig.isHistoryTooBig.
Keep tools+system prefix stable for cache. Prefer structured output over free-text JSON.
</constraints>
