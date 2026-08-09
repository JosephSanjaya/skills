# MCP Primitives — Tools, Resources, Prompts

## Tools

### inputSchema with ToolSchema
Use `buildJsonObject` from `kotlinx.serialization.json` for inline schema construction. Always include `required` for mandatory fields.

```kotlin
server.addTool(
    name = "search_repos",
    description = "Search GitHub repositories by query. Returns a list of matching repos with name, description, and URL.",
    inputSchema = ToolSchema(
        properties = buildJsonObject {
            put("query", buildJsonObject {
                put("type", "string")
                put("description", "Search query, e.g. 'kotlin coroutines'")
                put("minLength", 1)
            })
            put("language", buildJsonObject {
                put("type", "string")
                put("description", "Filter by programming language. Optional.")
                put("enum", buildJsonArray { add("kotlin"); add("java"); add("go") })
            })
            put("limit", buildJsonObject {
                put("type", "integer")
                put("description", "Max results (1–50, default 10)")
                put("default", 10)
                put("minimum", 1)
                put("maximum", 50)
            })
        },
        required = listOf("query")
    )
) { request ->
    val query = request.arguments!!["query"]!!.jsonPrimitive.content
    val language = request.arguments["language"]?.jsonPrimitive?.contentOrNull
    val limit = request.arguments["limit"]?.jsonPrimitive?.intOrNull ?: 10
    // ... call API ...
    CallToolResult(content = listOf(TextContent(results)))
}
```

**Tighten schemas to improve model accuracy.** Claude uses `enum`, `minimum`, `maximum`, `minLength`, and `required` to call tools correctly. Fuzzy schemas → hallucinated arguments → wasted turns.

### Structured Output (outputSchema)
When a tool always returns machine-readable JSON, declare `outputSchema` so clients know the shape. Also include a `TextContent` serialisation for backward compat.

```kotlin
server.addTool(
    name = "get_stock_price",
    description = "Returns current stock price and change for a ticker symbol.",
    inputSchema = ToolSchema(properties = buildJsonObject {
        put("ticker", buildJsonObject { put("type", "string") })
    }, required = listOf("ticker")),
    outputSchema = ToolSchema(properties = buildJsonObject {
        put("ticker",  buildJsonObject { put("type", "string") })
        put("price",   buildJsonObject { put("type", "number") })
        put("change",  buildJsonObject { put("type", "number") })
        put("currency",buildJsonObject { put("type", "string") })
    })
) { request ->
    val ticker = request.arguments!!["ticker"]!!.jsonPrimitive.content
    val data = fetchStockData(ticker)
    val json = buildJsonObject {
        put("ticker", ticker)
        put("price",  data.price)
        put("change", data.change)
        put("currency", data.currency)
    }
    CallToolResult(
        content = listOf(TextContent("${ticker}: ${data.price} ${data.currency} (${data.change})")),
        structuredContent = json
    )
}
```

### Tool Annotations
Declare behaviour hints so clients can show confirmation dialogs or skip them.

```kotlin
server.addTool(
    name = "delete_branch",
    description = "Permanently deletes a git branch. Cannot be undone.",
    toolAnnotations = ToolAnnotations(
        readOnlyHint   = false,
        destructiveHint = true,
        idempotentHint = false,
        openWorldHint  = false,   // only touches the specified repo
    ),
    // ...
) { ... }
```

**Important:** annotations are advisory UX hints, not security controls. The model may or may not respect them. Never grant write access because a tool says `readOnlyHint = true`.

### Response Content Types

```kotlin
// Plain text
TextContent("Hello, world!")

// Inline image (PNG/JPEG)
ImageContent(data = base64Bytes, mimeType = "image/png")

// Embedded resource (avoids inlining large payloads)
EmbeddedResource(resource = TextResourceContents(text = markdown, uri = "doc://result", mimeType = "text/markdown"))

// ResourceLink — preferred for large data: returns a handle, not the content
ResourceLink(uri = "repo://owner/repo/file/path", name = "README.md", mimeType = "text/markdown")
```

Use `ResourceLink` for anything that would exceed ~5 000 tokens. The model can request the full content via `resources/read` only if it needs it.

---

## Resources

### Static resource (exact URI)
```kotlin
server.addResource(
    uri = "config://app/settings",
    name = "App Settings",
    description = "Current application configuration as JSON",
    mimeType = "application/json"
) { _ ->
    ReadResourceResult(
        contents = listOf(
            TextResourceContents(
                text = Json.encodeToString(AppConfig.current()),
                uri = "config://app/settings",
                mimeType = "application/json"
            )
        )
    )
}
```

### URI-template resource (RFC 6570 subset)
Use `{variable}` placeholders; the SDK extracts them from the incoming URI and passes them via `request.uri`.

```kotlin
server.addResourceTemplate(
    uriTemplate = "repo://{owner}/{repo}/file/{path}",
    name = "Repository File",
    description = "Read a file from a GitHub repository",
    mimeType = "text/plain"
) { request ->
    // SDK matches template and fills variables; parse them from request.uri
    val (owner, repo, path) = parseRepoUri(request.uri)
    val content = githubClient.getFile(owner, repo, path)
    ReadResourceResult(
        contents = listOf(TextResourceContents(text = content, uri = request.uri, mimeType = "text/plain"))
    )
}
```

**Template scoring:** more-specific (more literal segments) templates score higher than parameterised ones for the same URI, so literal overrides work correctly.

---

## Prompts

Prompts are reusable message templates users invoke explicitly. Use them for standard workflows (code review, summarisation, onboarding).

```kotlin
server.addPrompt(
    name = "review_pr",
    description = "Generate a structured pull request review",
    arguments = listOf(
        PromptArgument(name = "diff",      description = "The unified diff of the PR",       required = true),
        PromptArgument(name = "context",   description = "Additional context or guidelines", required = false),
    )
) { request ->
    val diff    = request.arguments?.get("diff")    ?: ""
    val context = request.arguments?.get("context") ?: ""
    GetPromptResult(
        description = "PR review for the provided diff",
        messages = listOf(
            PromptMessage(
                role = Role.user,
                content = TextContent("""
                    Review the following diff carefully.
                    ${if (context.isNotBlank()) "Context: $context\n" else ""}
                    Diff:
                    ```diff
                    $diff
                    ```
                    Provide: summary of changes, potential bugs, security concerns, style issues.
                """.trimIndent())
            )
        )
    )
}
```

---

## Naming & Description Best Practices

| Principle | Bad | Good |
|---|---|---|
| Namespace by domain | `search` | `github_search_repos` |
| Describe output, not just input | "takes a query" | "returns a list of repos with name, description, URL" |
| Quantify limits | "some results" | "returns up to 50 results" |
| Name parameters clearly | `q` | `query` |
| Describe optional params | (silent) | "Optional. Defaults to 10." |

Small description improvements have outsized impact on tool-call accuracy. Treat descriptions like you're onboarding a new engineer.
