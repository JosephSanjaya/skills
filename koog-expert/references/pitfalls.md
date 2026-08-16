# Pitfalls

<instructions>
Fix these before features. Several are real GitHub issues.
</instructions>

## Tool routing (#2153)

`onToolCalls { it.tool == "foo" }` drops unmatched parallel siblings → unanswered tool calls in history. Use `{ true }` + `nodeExecuteTools(parallel = true)`, or add catch-all edge.

## Stale param

Blogs/Context7: `AIAgent(executor=…)`. **1.1.1 = `promptExecutor`.** Playwright MCP docs may still say `executor`.

## Provider switch (#755)

DeepSeek (etc.) can fail JSON on provider-specific usage fields (`audioTokens`). Pin models per client; test failover. `RetryingLLMClient` = 5xx/429 only, not 4xx. Mid-stream failures not transparently retried after bytes sent.

## Write-session lock

`llm.writeSession { }` exclusive. DB/HTTP inside stalls other coroutines on that agent. I/O first; write short result.

## Iteration cap

Factory + Ktor plugin default `maxAgentIterations = 50`. Set lower for HTTP. Unbounded tool loops burn money.

## Persistence

- Unique node names
- Unique session id / user
- Crash recovery ≠ chat history for one request
- Non-serializable state won't restore

## Structured output (#1328)

Native JSON historically skipped example injection → placeholder field text. Pass `examples`; confirm version has fix.

## Prefix cache

Add/remove tool busts Anthropic tools+system+messages cache. Keep tool set stable per session.

## Platform

- MCP / Bedrock: JVM only
- OTel: no WasmJS (KG-846)
- `oshai.kotlin.logging` not transitive from prompt clients (1.0+) — add logger
- `ktor.server.sse` not transitive from tokenizer/trace — add if streaming

## Security

- Env/secrets for keys — never real keys in committed yaml
- Mobile: backend proxy; LiteRT only if you accept model size
- `llm().moderate` untrusted text before agent
- Tool args = model-controlled = untrusted

## Docs vs repo

Context7 `/websites/koog_ai` + `/jetbrains/koog` useful but may be 0.5.x-era. Prefer Koog **1.1.1** source + https://docs.koog.ai/.

<constraints>
promptExecutor only. Catch-all onToolCalls. No shared agent across requests. Threshold compress. Env keys only.
Run !python3 ~/.claude/skills/koog-expert/scripts/audit_koog.py .

Must follow format above. Output only actionable Kotlin/API guidance.
</constraints>
