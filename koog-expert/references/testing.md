# Testing

<instructions>
`ai.koog:agents-test` — real graph + fake LLM. No keys. Milliseconds.
</instructions>

## Mock executor

```kotlin
val mock = getMockExecutor(toolRegistry, eventHandler) {
    mockLLMAnswer("Hello!") onRequestContains "Hello"
    mockLLMToolCall(CreateTool, CreateTool.Args("solve")) onRequestEquals "Solve task"
    mockLLMAnswer("Default response").asDefaultResponse
}
```

Structured: `mockLLMAnswer` returns a JSON *string* of the target `@Serializable` type — `executeStructured` parses it.

## Mock tools

```kotlin
mockTool(PositiveToneTool) alwaysReturns "positive"
mockTool(SearchTool) returns SearchTool.Result("Found") onArgumentsMatching {
    args.query.contains("important")
}
```

## Graph structure

```kotlin
AIAgent(promptExecutor = mock, llmModel = model, strategy = myStrategy) {
    withTesting()
    testGraph("support") {
        val first = assertSubgraphByName<String, String>("collect")
        assertEdges { startNode() alwaysGoesTo first }
        assertReachable(start, finish)
    }
}
```

## Assert

- Happy: text → assistant, no tools
- Tool: mock call + result + final answer
- Compress edge: over-threshold prompt → compress node runs
- Parallel: two LLM tool calls both execute (`onToolCalls { true }`)

No live providers in unit tests. Integration tests need env keys (`OPEN_AI_API_TEST_KEY`, …) — never commit.

<constraints>
Mock LLM via getMockExecutor. Assert graph structure with withTesting(). Never commit API keys.

Must follow format above. Output only actionable Kotlin/API guidance.
</constraints>
