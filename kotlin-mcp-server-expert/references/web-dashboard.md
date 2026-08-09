# Web Dashboard & Runtime Config for Kotlin MCP Servers

## MCP Inspector (zero-code dev UI)

Pair with MCP Inspector during development — browser UI for calling tools, browsing resources/prompts, and inspecting raw JSON-RPC:

```bash
npx @modelcontextprotocol/inspector
```

Point at your server:
- Streamable HTTP: `http://127.0.0.1:8080/mcp`
- stdio: `npx @modelcontextprotocol/inspector -- java -jar your-server.jar`

Dev-only — never expose on a public port.

## Live SSE Event Feed

Add a real-time event feed alongside `/mcp` on the same Ktor server:

```kotlin
import kotlinx.coroutines.flow.MutableSharedFlow

val toolEvents = MutableSharedFlow<String>(replay = 0, extraBufferCapacity = 256)

fun Application.module() {
    routing {
        get("/dashboard") { call.respondText(dashboardHtml(), ContentType.Text.Html) }

        get("/events") {
            call.response.cacheControl(CacheControl.NoCache(null))
            call.respondTextWriter(contentType = ContentType.Text.EventStream) {
                toolEvents.collect { event -> write("data: $event\n\n"); flush() }
            }
        }

        mcpStreamableHttp(path = "/mcp") { buildServer(toolEvents) }
    }
}
```

Emit from tool handlers — `tryEmit` is non-blocking, never suspends the handler:

```kotlin
fun buildServer(events: MutableSharedFlow<String>): Server {
    val server = Server(/* ... */)
    server.addTool("my_tool", "...", inputSchema) { request ->
        val start = System.currentTimeMillis()
        try {
            val result = doWork(request)
            events.tryEmit("""{"tool":"my_tool","status":"ok","ms":${System.currentTimeMillis() - start}}""")
            result
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            events.tryEmit("""{"tool":"my_tool","status":"error","ms":${System.currentTimeMillis() - start},"err":${JsonPrimitive(e.message)}}""")
            CallToolResult(content = listOf(TextContent("Error: ${e.message}")), isError = true)
        }
    }
    return server
}
```

Minimal dashboard HTML:

```kotlin
fun dashboardHtml() = """
<!DOCTYPE html><html><head><title>MCP Dashboard</title>
<style>
  body { font-family: monospace; background: #0d1117; color: #c9d1d9; padding: 1rem; }
  #log { height: 80vh; overflow-y: auto; }
  .ok { color: #3fb950; } .err { color: #f85149; }
</style>
</head><body>
<h2>MCP Tool Events</h2><div id="log"></div>
<script>
  const log = document.getElementById('log');
  new EventSource('/events').onmessage = e => {
    const d = JSON.parse(e.data);
    const line = document.createElement('div');
    line.className = d.status === 'ok' ? 'ok' : 'err';
    line.textContent = JSON.stringify(d);
    log.prepend(line);
    if (log.children.length > 500) log.lastChild.remove();
  };
</script>
</body></html>
""".trimIndent()
```

**Security:** expose `/dashboard` and `/events` on loopback only or behind a VPN — they leak tool names and timings. For production replace `MutableSharedFlow` with Micrometer/OTel.

## Runtime Config via Browser

Tool handlers read `MutableStateFlow<ServerConfig>` — browser POSTs update it, changes take effect on next invocation, no restart needed.

```kotlin
@Serializable
data class ServerConfig(
    val maxResults: Int = 20,
    val allowedStatus: List<String> = listOf("active", "inactive", "all"),
    val rateLimitPerMinute: Int = 60,
    val debugMode: Boolean = false,
)

val config = MutableStateFlow(ServerConfig())
```

Expose alongside `/mcp`:

```kotlin
routing {
    get("/config")  { call.respond(config.value) }
    post("/config") {
        config.value = call.receive<ServerConfig>()
        call.respond(HttpStatusCode.OK, config.value)
    }
    get("/dashboard") { call.respondText(dashboardHtml(), ContentType.Text.Html) }
    get("/events")    { /* SSE as above */ }
    mcpStreamableHttp(path = "/mcp") { buildServer(config, toolEvents) }
}
```

Read `config.value` inside handlers:

```kotlin
fun buildServer(config: StateFlow<ServerConfig>, events: MutableSharedFlow<String>): Server {
    val server = Server(/* ... */)
    server.addTool("search_customers", "...", inputSchema) { request ->
        val cfg = config.value
        val limit = (request.arguments?.get("limit")?.jsonPrimitive?.intOrNull ?: cfg.maxResults)
            .coerceIn(1, cfg.maxResults)
        if (cfg.debugMode) events.tryEmit("""{"debug":"search called","limit":$limit}""")
        doSearch(request, limit, cfg)
    }
    return server
}
```

Dashboard HTML with config form + event log:

```kotlin
fun dashboardHtml() = """
<!DOCTYPE html><html><head><title>MCP Dashboard</title>
<style>
  body { font-family: monospace; background: #0d1117; color: #c9d1d9; padding: 1rem; }
  label { display: block; margin: 0.5rem 0; }
  input[type=number], input[type=checkbox] { margin-left: 0.5rem; }
  button { margin-top: 1rem; padding: 0.4rem 1rem; cursor: pointer; }
  #status { color: #3fb950; margin-top: 0.5rem; }
  #log { height: 40vh; overflow-y: auto; margin-top: 1rem; }
  .ok { color: #3fb950; } .err { color: #f85149; }
</style>
</head><body>
<h2>MCP Config</h2>
<form id="cfg">
  <label>Max results <input id="maxResults" type="number" min="1" max="100"></label>
  <label>Rate limit/min <input id="rateLimitPerMinute" type="number" min="1"></label>
  <label>Debug mode <input id="debugMode" type="checkbox"></label>
  <button type="submit">Save</button>
</form>
<div id="status"></div>
<h2>Live Events</h2><div id="log"></div>
<script>
  fetch('/config').then(r => r.json()).then(c => {
    document.getElementById('maxResults').value = c.maxResults;
    document.getElementById('rateLimitPerMinute').value = c.rateLimitPerMinute;
    document.getElementById('debugMode').checked = c.debugMode;
  });
  document.getElementById('cfg').addEventListener('submit', async e => {
    e.preventDefault();
    const r = await fetch('/config', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        maxResults: +document.getElementById('maxResults').value,
        rateLimitPerMinute: +document.getElementById('rateLimitPerMinute').value,
        debugMode: document.getElementById('debugMode').checked,
        allowedStatus: ['active','inactive','all']
      })
    });
    const s = document.getElementById('status');
    s.textContent = r.ok ? 'Saved.' : 'Error: ' + r.status;
    setTimeout(() => s.textContent = '', 2000);
  });
  const log = document.getElementById('log');
  new EventSource('/events').onmessage = e => {
    const d = JSON.parse(e.data);
    const line = document.createElement('div');
    line.className = d.status === 'ok' || d.debug ? 'ok' : 'err';
    line.textContent = JSON.stringify(d);
    log.prepend(line);
    if (log.children.length > 500) log.lastChild.remove();
  };
</script>
</body></html>
""".trimIndent()
```

**Gradle — required for `call.receive<ServerConfig>()`:**

```toml
[libraries]
ktor-server-content-negotiation = { module = "io.ktor:ktor-server-content-negotiation", version.ref = "ktor" }
ktor-serialization-json         = { module = "io.ktor:ktor-serialization-kotlinx-json", version.ref = "ktor" }
```

```kotlin
install(ContentNegotiation) { json() }
```

**What belongs in ServerConfig:** tuning knobs (limits, timeouts, page sizes), feature flags (`debugMode`, `enableAnalyticsTools`), allowlists.

**What does NOT belong:** secrets/API keys (env vars only), tool topology changes (use `sendToolListChanged()` instead).
