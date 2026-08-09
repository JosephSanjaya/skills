# Testing Kotlin MCP Servers

## Unit Tests with ChannelTransport

`ChannelTransport.createLinkedPair()` creates an in-memory client/server pair — no network, no process, fully deterministic. Use it for unit and integration tests.

```kotlin
import io.modelcontextprotocol.kotlin.sdk.server.Server
import io.modelcontextprotocol.kotlin.sdk.server.ServerOptions
import io.modelcontextprotocol.kotlin.sdk.client.Client
import io.modelcontextprotocol.kotlin.sdk.testing.ChannelTransport
import io.modelcontextprotocol.kotlin.sdk.types.*
import kotlinx.coroutines.test.runTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse

@OptIn(ExperimentalMcpApi::class)
class GreetToolTest {

    @Test
    fun `greet tool returns correct greeting`() = runTest {
        // Arrange
        val server = buildTestServer()
        val (clientTransport, serverTransport) = ChannelTransport.createLinkedPair()
        val client = Client(clientInfo = Implementation("test-client", "1.0"))

        listOf(
            launch { client.connect(clientTransport) },
            launch { server.createSession(serverTransport) }
        ).joinAll()

        // Act
        val result = client.callTool("greet", mapOf("name" to "Alice"))

        // Assert
        assertFalse(result.isError == true)
        val text = (result.content.first() as TextContent).text
        assertEquals("Hello, Alice!", text)

        // Cleanup
        client.close()
        server.close()
    }

    @Test
    fun `greet tool returns isError when name is missing`() = runTest {
        val server = buildTestServer()
        val (clientTransport, serverTransport) = ChannelTransport.createLinkedPair()
        val client = Client(clientInfo = Implementation("test-client", "1.0"))
        listOf(launch { client.connect(clientTransport) }, launch { server.createSession(serverTransport) }).joinAll()

        val result = client.callTool("greet", emptyMap())

        assertEquals(true, result.isError)
        client.close(); server.close()
    }
}

private fun buildTestServer() = Server(
    serverInfo = Implementation("test-server", "1.0"),
    options = ServerOptions(capabilities = ServerCapabilities(tools = ServerCapabilities.Tools()))
).apply {
    addTool("greet", "Greet by name", ToolSchema(
        properties = buildJsonObject { put("name", buildJsonObject { put("type", "string") }) },
        required = listOf("name")
    )) { request ->
        val name = request.arguments?.get("name")?.jsonPrimitive?.contentOrNull
            ?: return@addTool CallToolResult(content = listOf(TextContent("Missing: name")), isError = true)
        CallToolResult(content = listOf(TextContent("Hello, $name!")))
    }
}
```

## Testing Resource Templates

```kotlin
@Test
fun `resource template extracts path variables correctly`() = runTest {
    val server = Server(
        Implementation("test", "1.0"),
        ServerOptions(capabilities = ServerCapabilities(resources = ServerCapabilities.Resources()))
    ).apply {
        addResourceTemplate("repo://{owner}/{repo}", "Repo", "Get repo info", "application/json") { request ->
            val parts = request.uri.removePrefix("repo://").split("/")
            ReadResourceResult(contents = listOf(
                TextResourceContents("""{"owner":"${parts[0]}","repo":"${parts[1]}"}""", request.uri, "application/json")
            ))
        }
    }

    val (clientT, serverT) = ChannelTransport.createLinkedPair()
    val client = Client(Implementation("c", "1.0"))
    listOf(launch { client.connect(clientT) }, launch { server.createSession(serverT) }).joinAll()

    val result = client.readResource("repo://octocat/hello-world")
    val text = (result.contents.first() as TextResourceContents).text
    assert(text.contains("octocat"))

    client.close(); server.close()
}
```

## Testing Tool List Changed

```kotlin
@Test
fun `sendToolListChanged notifies client`() = runTest {
    val server = Server(
        Implementation("test", "1.0"),
        ServerOptions(capabilities = ServerCapabilities(tools = ServerCapabilities.Tools(listChanged = true)))
    )

    val (clientT, serverT) = ChannelTransport.createLinkedPair()
    val client = Client(Implementation("c", "1.0"), ClientOptions(
        capabilities = ClientCapabilities(tools = ClientCapabilities.Tools())
    ))

    var notificationReceived = false
    client.setNotificationHandler<ToolListChangedNotification>(Method.Defined.NotificationsToolsListChanged) { _ ->
        notificationReceived = true
    }

    listOf(launch { client.connect(clientT) }, launch { server.createSession(serverT) }).joinAll()

    server.sendToolListChanged()
    delay(100)  // let the notification propagate

    assert(notificationReceived)
    client.close(); server.close()
}
```

## Testing Error Handling

```kotlin
@Test
fun `tool returns isError on network failure`() = runTest {
    val mockClient = mockk<ApiClient> {
        coEvery { fetch(any()) } throws IOException("network failure")
    }
    val server = buildServerWithMockClient(mockClient)
    // ... setup transport and client ...
    val result = client.callTool("fetch_data", mapOf("id" to "123"))
    assertEquals(true, result.isError)
    assert((result.content.first() as TextContent).text.contains("network failure"))
}
```

## runTest vs runBlocking

Always use `runTest` from `kotlinx-coroutines-test` for coroutine tests. It uses a `TestCoroutineScheduler` that controls virtual time — `delay()` completes instantly:

```kotlin
@Test
fun `tool respects timeout`() = runTest {
    val server = Server(/* ... */).apply {
        addTool("slow", "...", ToolSchema()) { _ ->
            delay(60_000L)  // this completes instantly in runTest
            CallToolResult(content = listOf(TextContent("done")))
        }
    }
    // ...
}
```

For real timing tests (e.g., testing that a 30s timeout actually cancels), use `runBlocking` with `Dispatchers.IO` and real time.

## CI Assertions Checklist

| What to assert | How |
|---|---|
| Tool returns expected content | `(result.content.first() as TextContent).text` |
| Tool sets `isError = true` on bad input | `assertEquals(true, result.isError)` |
| Tool list contains expected names | `client.listTools().tools.map { it.name }` |
| Resource template returns correct data | `client.readResource(uri).contents` |
| Notification fired on addTool | `setNotificationHandler` + flag |
| Server closes cleanly | `client.close(); server.close()` — no exceptions |

## Dependency

```toml
# gradle/libs.versions.toml
[versions]
kotlin-coroutines = "1.9.0"
mcp-sdk = "0.5.0"    # pin exact version

[libraries]
mcp-sdk-testing = { module = "io.modelcontextprotocol:kotlin-sdk-testing", version.ref = "mcp-sdk" }
coroutines-test = { module = "org.jetbrains.kotlinx:kotlinx-coroutines-test", version.ref = "kotlin-coroutines" }
```
