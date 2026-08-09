# Coroutines in MCP Handlers

MCP handlers are `suspend` lambdas. The SDK calls them from a managed coroutine scope — you get structured concurrency for free, but you need to respect its rules.

## Dispatcher Selection

| Work type | Dispatcher | Notes |
|---|---|---|
| I/O (network, DB, file) | `Dispatchers.IO` | Default for most tool handlers |
| CPU-bound (parsing, crypto) | `Dispatchers.Default` | JSON parsing, sorting large sets |
| Bounded I/O concurrency | `Dispatchers.IO.limitedParallelism(n)` | Rate-limit outbound API calls |
| Handler default | inherited from SDK | Don't switch unless you need to |

Don't switch dispatchers unnecessarily — `withContext` has overhead. Only switch when the work genuinely needs a different thread pool.

## Parallel Fan-out in a Handler

Run independent I/O calls concurrently using `coroutineScope + async`:

```kotlin
server.addTool("get_repo_summary", "Get stats for multiple repos", inputSchema) { request ->
    val repos = request.arguments!!["repos"]!!.jsonArray.map { it.jsonPrimitive.content }

    val results = coroutineScope {
        repos.map { repo ->
            async(Dispatchers.IO) { fetchRepoStats(repo) }
        }.awaitAll()
    }

    CallToolResult(content = listOf(TextContent(results.joinToString("\n") { it.format() })))
}
```

`coroutineScope` propagates cancellation correctly: if the parent (the SDK session) is cancelled, all `async` children cancel too. Never use `GlobalScope.async` — it leaks.

## Bounded Concurrency for Large Fan-outs

Spawning hundreds of coroutines against an external API causes rate-limit errors. Use a Semaphore:

```kotlin
val apiSemaphore = Semaphore(10) // max 10 in-flight requests

server.addTool("batch_process", "Process a list of items", inputSchema) { request ->
    val items = request.arguments!!["items"]!!.jsonArray

    val results = coroutineScope {
        items.map { item ->
            async(Dispatchers.IO) {
                apiSemaphore.withPermit {
                    processItem(item.jsonPrimitive.content)
                }
            }
        }.awaitAll()
    }

    CallToolResult(content = listOf(TextContent(buildReport(results))))
}
```

## Progress Notifications

For long-running tools, send progress notifications via `ClientConnection.sendLoggingMessage`. The `ClientConnection` is the handler's receiver:

```kotlin
server.addTool("index_codebase", "Index all files in a repo", inputSchema) { request ->
    val path = request.arguments!!["path"]!!.jsonPrimitive.content
    val files = collectFiles(path)

    files.forEachIndexed { i, file ->
        if (i % 50 == 0) {
            sendLoggingMessage(LoggingMessageNotification(
                LoggingMessageNotificationParams(
                    level = LoggingLevel.Info,
                    logger = "index_codebase",
                    data = buildJsonObject { put("progress", "$i/${files.size}") }
                )
            ))
        }
        indexFile(file)
    }

    CallToolResult(content = listOf(TextContent("Indexed ${files.size} files.")))
}
```

## The CancellationException Rule

**Never swallow CancellationException.** It signals structured cancellation and must propagate.

```kotlin
// WRONG — breaks cancellation
} catch (e: Exception) {
    CallToolResult(content = listOf(TextContent("Error: ${e.message}")), isError = true)
}

// CORRECT
} catch (e: CancellationException) {
    throw e  // always rethrow
} catch (e: Exception) {
    CallToolResult(content = listOf(TextContent("Error: ${e.message}")), isError = true)
}
```

## Flow in Handlers

If your service layer returns a `Flow`, collect it inside `coroutineScope`:

```kotlin
server.addTool("stream_logs", "Collect log lines matching a pattern", inputSchema) { request ->
    val pattern = request.arguments!!["pattern"]!!.jsonPrimitive.content
    val lines = StringBuilder()

    coroutineScope {
        logService.tailFlow(pattern)
            .take(200)                  // cap collection
            .collect { line -> lines.appendLine(line) }
    }

    CallToolResult(content = listOf(TextContent(lines.toString())))
}
```

## Shared Mutable State Between Handlers

Don't use shared mutable vars in handler closures — multiple sessions run concurrently. Use `StateFlow`, `AtomicReference`, or a serialized `Channel`:

```kotlin
// Safe: atomic read/write
private val cacheVersion = AtomicLong(0)

// Safe: StateFlow.update is concurrent-safe
private val _status = MutableStateFlow<Status>(Status.Idle)

// Handler just reads
server.addTool("get_status", "...", inputSchema) { _ ->
    CallToolResult(content = listOf(TextContent(_status.value.toString())))
}
```

## Timeout per Tool Call

Wrap expensive external calls in `withTimeout` to prevent hanging sessions:

```kotlin
server.addTool("run_analysis", "...", inputSchema) { request ->
    try {
        val result = withTimeout(30_000L) {
            runHeavyAnalysis(request.arguments!!)
        }
        CallToolResult(content = listOf(TextContent(result)))
    } catch (e: TimeoutCancellationException) {
        CallToolResult(
            content = listOf(TextContent("Analysis timed out after 30s. Try a smaller dataset.")),
            isError = true
        )
    }
}
```

Note: `TimeoutCancellationException` is a subtype of `CancellationException` — catch it before the generic CancellationException rethrow block if you want to handle it gracefully.
