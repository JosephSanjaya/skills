# Token Efficiency for MCP Kotlin Servers

Tool schemas are injected into the model's system prompt on **every request**. A server with 20 verbose tools can consume 30–50% of the context window before the model does anything. Design responses and schemas for token efficiency from the start.

## Rule 1: Concise descriptions, not essays

```kotlin
// BAD — 47 tokens
description = "This tool searches through all available GitHub repositories " +
    "using the GitHub REST API and returns matching results based on the query " +
    "provided by the user."

// GOOD — 12 tokens
description = "Search GitHub repos. Returns name, description, URL, stars."
```

## Rule 2: Return semantic fields, not raw API payloads

Strip internal IDs, null fields, timestamps the model doesn't need:

```kotlin
// BAD — returns 200+ tokens of GitHub JSON
CallToolResult(content = listOf(TextContent(Json.encodeToString(rawApiResponse))))

// GOOD — project only what the model needs
data class RepoSummary(val name: String, val description: String?, val url: String, val stars: Int)

val summaries = results.map { r ->
    RepoSummary(r.fullName, r.description, r.htmlUrl, r.stargazersCount)
}
CallToolResult(content = listOf(TextContent(Json.encodeToString(summaries))))
```

Anthropic measured a "concise" Slack tool returning ~⅓ the tokens of a "verbose" one, with no loss in model accuracy.

## Rule 3: Pagination for list tools

Always paginate. Return `hasMore` and a `nextCursor` so the model only fetches pages it actually needs:

```kotlin
server.addTool(
    name = "list_issues",
    description = "List open issues in a repo. Returns up to 20 per page. If hasMore is true, call again with cursor.",
    inputSchema = ToolSchema(properties = buildJsonObject {
        put("repo",   buildJsonObject { put("type", "string") })
        put("cursor", buildJsonObject { put("type", "string"); put("description", "Pagination cursor from previous call. Optional.") })
        put("limit",  buildJsonObject { put("type", "integer"); put("default", 20); put("maximum", 50) })
    }, required = listOf("repo"))
) { request ->
    val repo   = request.arguments!!["repo"]!!.jsonPrimitive.content
    val cursor = request.arguments["cursor"]?.jsonPrimitive?.contentOrNull
    val limit  = request.arguments["limit"]?.jsonPrimitive?.intOrNull ?: 20

    val page = issueService.listIssues(repo, cursor, limit + 1)  // fetch limit+1 to detect hasMore
    val hasMore = page.size > limit
    val items = page.take(limit)
    val nextCursor = if (hasMore) items.last().id.toString() else null

    val result = buildJsonObject {
        putJsonArray("issues") { items.forEach { add(it.toJsonSummary()) } }
        put("hasMore", hasMore)
        if (nextCursor != null) put("nextCursor", nextCursor)
        put("count", items.size)
    }
    CallToolResult(content = listOf(TextContent(result.toString())))
}
```

Use keyset pagination (cursor = last seen ID), not `OFFSET` — offsets cause skips/duplicates under concurrent writes.

## Rule 4: ResourceLink for large payloads

Don't inline large documents. Return a `ResourceLink`; the model requests the full content only if it needs it:

```kotlin
server.addTool("find_file", "Locate a file and return a handle", inputSchema) { request ->
    val path = findFile(request.arguments!!["name"]!!.jsonPrimitive.content)
    CallToolResult(
        content = listOf(
            TextContent("Found: ${path.name} (${path.length()} bytes)"),
            ResourceLink(
                uri = "file://$path",
                name = path.name,
                mimeType = guessMimeType(path),
                description = "Full file content"
            )
        )
    )
}
```

Register the companion resource handler so the model can read it:

```kotlin
server.addResourceTemplate("file://{path}", "File", "Read a local file", "text/plain") { request ->
    val path = File(request.uri.removePrefix("file://"))
    ReadResourceResult(contents = listOf(TextResourceContents(path.readText(), request.uri, "text/plain")))
}
```

## Rule 5: Cap large outputs

Never return unbounded results. Apply a hard token cap and steer the model toward narrower queries:

```kotlin
val MAX_CHARS = 50_000  // ~12 500 tokens at 4 chars/token

if (output.length > MAX_CHARS) {
    return@addTool CallToolResult(
        content = listOf(TextContent(
            output.take(MAX_CHARS) + "\n\n[Truncated: ${output.length} chars total. " +
            "Use the cursor parameter to paginate or narrow your query with filters.]"
        ))
    )
}
```

## Rule 6: Toolset gating for large tool counts

If your server exposes >20 tools, group them into toolsets and expose only the default set at startup. Use a `discover_tools`-style meta-tool to activate additional categories on demand:

```kotlin
// Only register tools for categories the client requested
val enabledCategories = config.enabledToolsets  // e.g. ["core", "admin"]

if ("admin" in enabledCategories) {
    registerAdminTools(server)
}
if ("analytics" in enabledCategories) {
    registerAnalyticsTools(server)
}
// Always register the discovery tool
registerDiscoverTool(server, allCategories)
```

## Summary Table

| Problem | Fix |
|---|---|
| Too many tokens in schema | Shorten descriptions, remove optional params from defaults |
| Large API response inlined | Project only needed fields |
| Unbounded list result | Paginate with cursor + `hasMore` |
| Large file/document | Return `ResourceLink`, register resource handler |
| Too many tools in context | Toolset gating + `sendToolListChanged` |
| Noisy result data | Strip nulls, timestamps, internal IDs |
