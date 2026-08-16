# Tools / MCP / A2A

<instructions>
Tools = thin validate → service → short result. LLM-visible text is `@LLMDescription` (tokens + accuracy).
</instructions>

## Annotation tools

```kotlin
@LLMDescription("Order lookup and address updates")
class OrderTools(private val orders: OrderRepository) : ToolSet {
    @Tool
    @LLMDescription("Shipping status + tracking for one order")
    fun getOrderStatus(
        @LLMDescription("10-char alphanumeric order id") orderId: String,
    ): String {
        val order = orders.find(orderId) ?: return "Order $orderId not found"
        return "Order $orderId: ${order.status}. Tracking ${order.trackingNumber}"
    }
}

val registry = ToolRegistry {
    tools(OrderTools(orders).asTools())
    tool(::searchInGoogle)
}
```

`asTools()` in `agents-tools`. Every `@Tool` needs `@LLMDescription` on fn + params. Class-based `Tool<Args, Result>` for custom schemas.

```kotlin
ToolRegistry { tool(AskUser); tools(set.asTools()) }
pluginRegistry + requestRegistry
```

Ktor: `registerTools { tool(::fn); tools(set.asTools()) }`.

## Token design

- Few precise tools > many overlapping
- `subgraphWithTask` / limited tools hide unused schemas
- Compact results, not DB dumps
- `ToolCallMetadata` for trace/feature flags without polluting LLM schema

## Parallel calls

```kotlin
val execute by nodeExecuteTools(parallel = true)
// or nodeExecuteMultipleTools(parallelTools = true)
```

Do **not** filter `onToolCalls { it.tool == "one" }` without a catch-all — unmatched parallel calls drop (#2153). Use `{ true }` / `onMultipleToolCalls { true }`.

## MCP (JVM)

```kotlin
val tools = McpToolRegistryProvider.fromTransport(
    transport = McpToolRegistryProvider.defaultSseTransport("http://localhost:8931/sse"),
)
```

Ktor: `agentConfig { mcp { sse(url) /* process / client */ } }`. Auth via configured `HttpClient` → `SseClientTransport`. Model needs `LLMCapability.Tools`. Module beta, JVM-oriented.

## A2A

`a2a-core` / client / server (v0.3.0, beta). `AgentCard`, `message/send`, `message/stream`. Add modules yourself.

## Safety

- Tools only via `AIAgentEnvironment`
- `require` at tool boundary
- Side-effect + Persistence → `RollbackToolRegistry`
- Never log keys/PII from tool args in EventHandler

<constraints>
Catch-all onToolCalls for parallel tools. MCP only on JVM. Treat tool args as untrusted.
</constraints>
