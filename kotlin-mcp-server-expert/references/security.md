# Security for Kotlin MCP Servers

## The Core Threat Model

1. **Tool descriptions are a prompt-injection surface.** External data embedded in tool descriptions, parameter values, or results can hijack the model.
2. **The model doesn't validate inputs.** It sends whatever it believes is correct. You are the last line of defense.
3. **MCP tools can have real side effects.** Treat every tool call as an untrusted external request.

## Input Validation

Validate all arguments at the server boundary before touching any system resource. Use strict schemas (`minLength`, `pattern`, `enum`, `minimum`, `maximum`) to constrain inputs at the model level too.

```kotlin
server.addTool("read_file", "Read a file by path", inputSchema) { request ->
    val rawPath = request.arguments!!["path"]!!.jsonPrimitive.content

    // Canonicalise and sandbox-check
    val requested = File(rawPath).canonicalFile
    val sandbox   = File(config.sandboxRoot).canonicalFile

    if (!requested.absolutePath.startsWith(sandbox.absolutePath + File.separator)) {
        return@addTool CallToolResult(
            content = listOf(TextContent("Access denied: path is outside the allowed directory.")),
            isError = true
        )
    }
    if (!requested.exists() || !requested.isFile) {
        return@addTool CallToolResult(
            content = listOf(TextContent("File not found: ${requested.name}")),
            isError = true
        )
    }
    CallToolResult(content = listOf(TextContent(requested.readText())))
}
```

**Path traversal is the #1 CVE class in MCP servers (82% of vulnerable implementations in a 2025/2026 survey).** Always `canonicalFile` + prefix-check.

## Command Injection Prevention

Never pass model input to a shell. Use `ProcessBuilder` with explicit argument arrays:

```kotlin
// WRONG — shell injection risk
Runtime.getRuntime().exec("git log $branch")

// CORRECT — no shell interpolation
ProcessBuilder("git", "log", "--oneline", "-20", branch)
    .directory(repoDir)
    .redirectErrorStream(true)
    .start()
    .also { process ->
        val output = process.inputStream.bufferedReader().readText()
        process.waitFor()
    }
```

Also: never use `ScriptEngine.eval(userInput)` or Groovy `GroovyShell.evaluate(userInput)`.

## SSRF Prevention

For tools that fetch URLs, allowlist domains or block private IP ranges:

```kotlin
fun validateUrl(rawUrl: String): Result<URL> {
    val url = runCatching { URL(rawUrl) }.getOrElse {
        return Result.failure(IllegalArgumentException("Invalid URL"))
    }
    val host = url.host.lowercase()

    val blockedPatterns = listOf(
        Regex("^localhost$"),
        Regex("^127\\..*"),
        Regex("^10\\..*"),
        Regex("^172\\.(1[6-9]|2[0-9]|3[01])\\..*"),
        Regex("^192\\.168\\..*"),
        Regex("^169\\.254\\..*"),   // link-local / cloud metadata
        Regex("^::1$"),             // IPv6 loopback
        Regex("^fc[0-9a-f]{2}:.*"), // IPv6 private
    )
    if (blockedPatterns.any { it.matches(host) }) {
        return Result.failure(SecurityException("URL targets a private/reserved address"))
    }
    if (url.protocol !in listOf("https", "http")) {
        return Result.failure(SecurityException("Only http/https URLs are allowed"))
    }
    return Result.success(url)
}
```

Don't hand-roll IP parsing for the check — use DNS resolution after your check and pin DNS to prevent TOCTOU rebinding attacks.

## Secret Management

Never hardcode secrets. Pass them via environment variables at runtime, not baked into the Docker image:

```kotlin
object Config {
    val githubToken: String = System.getenv("GITHUB_TOKEN")
        ?: error("GITHUB_TOKEN environment variable is required")

    val dbPassword: String = System.getenv("DB_PASSWORD")
        ?: error("DB_PASSWORD environment variable is required")
}
```

Add `.env*` files to both `.gitignore` and `.dockerignore`. Use a secrets manager (AWS Secrets Manager, HashiCorp Vault) for production credentials.

## Authentication (Streamable HTTP)

For remote servers, implement OAuth 2.1 with PKCE. The Kotlin SDK doesn't bundle an OAuth server — use Ktor's auth plugin or an external IdP (Auth0, Keycloak):

```kotlin
fun Application.module() {
    install(Authentication) {
        bearer("mcp-bearer") {
            authenticate { credential ->
                // Validate JWT issued by your IdP
                val claims = jwtVerifier.verify(credential.token)
                UserIdPrincipal(claims.subject)
            }
        }
    }
    routing {
        authenticate("mcp-bearer") {
            mcpStreamableHttp(path = "/mcp") { buildMyServer() }
        }
    }
}
```

**Token passthrough is forbidden** — never accept a token that was not issued specifically for your MCP server. Per the 2025-06-18 spec, remote MCP servers are OAuth 2.1 Resource Servers.

## Supply Chain

- Pin exact dependency versions in `gradle/libs.versions.toml` (never `latest.release`).
- Scan with Trivy or Snyk in CI.
- Review Kotlin SDK release notes before upgrading — the MCP ecosystem ships fast.

## Audit Logging

Log every tool invocation with at minimum: tool name, argument summary (no secrets), session ID, result status. Never log PII or credential values:

```kotlin
server.addTool("run_query", "...", inputSchema) { request ->
    val query = request.arguments!!["query"]!!.jsonPrimitive.content
    logger.info("tool=run_query session=${sessionId()} query_hash=${query.hashCode()}")
    // ...
}
```

## Approve-Policy Pattern

For destructive or irreversible tools, require explicit confirmation before execution:

```kotlin
server.addTool(
    name = "drop_table",
    description = "Permanently drop a database table. Set _confirmed=true to execute.",
    toolAnnotations = ToolAnnotations(destructiveHint = true),
    inputSchema = ToolSchema(properties = buildJsonObject {
        put("table",      buildJsonObject { put("type", "string") })
        put("_confirmed", buildJsonObject { put("type", "boolean"); put("description", "Set true to confirm irreversible action") })
    }, required = listOf("table"))
) { request ->
    val confirmed = request.arguments?.get("_confirmed")?.jsonPrimitive?.booleanOrNull ?: false
    if (!confirmed) {
        return@addTool CallToolResult(
            content = listOf(TextContent("This will permanently drop the table. Re-call with _confirmed=true to proceed.")),
            isError = false  // not an error — a confirmation prompt
        )
    }
    db.dropTable(request.arguments!!["table"]!!.jsonPrimitive.content)
    CallToolResult(content = listOf(TextContent("Table dropped.")))
}
```
