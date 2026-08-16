# Apps / KMP

<instructions>
Targets: JVM, Android, iOS, JS, WasmJS — capabilities unequal.
</instructions>

| Target | Do | Don't |
|---|---|---|
| JVM backend | Full agents, MCP, Bedrock, JDBC Persistence, OTel | Share one agent across requests |
| Android | Graphs in `commonMain`; LiteRT/Gemma offline | Ship cloud API keys in APK |
| iOS | Graphs + call backend | Assume MCP |
| Desktop JVM | Ollama local OK | Skip `maxIterations` |
| JS / WasmJS | In-browser possible | MCP, Bedrock, WasmJS OTel |

Require `android.useAndroidX=true`.

## Production default

**UI → Ktor/Spring Koog backend → LLM.** Keys, compression, retries, moderation, cache, metrics stay server-side. Compose demos with in-app `simpleOpenRouterExecutor(apiKey)` = PoC only.

`commonMain`: strategy graphs, `@Serializable` models, tool interfaces.  
Platform sets: `PromptExecutor` / clients, Persistence, HTTP to backend.

## On-device (Android)

LiteRT client (Koog 1.0+) for local Gemma — no cloud key. Budget 2GB+ artifacts, device tier, battery. Verify artifact on `api.koog.ai` for pinned version. Desktop/dev: Ollama.

## Typed UI

Bind UI to `@Serializable` from `nodeLLMRequestStructured<T>()` / `executeStructured<T>()`. No free-text regex in UI.

```kotlin
@Serializable
@LLMDescription("Goal broken into steps")
data class GoalDecomposition(
    @property:LLMDescription("Top-level goal") val goal: String,
    val subgoals: List<String>,
    val firstStep: String,
)
```

Repo: `examples/demo-compose-app` — copy graph shape (`nodeLLMRequestMultiple` + parallel tools + compress at `messages.size > 100`); do not copy key-in-app wiring.

A2A/ACP: add `a2a-*` / ACP modules explicitly — not in `koog-agents`.

<constraints>
Never embed provider API keys in mobile/desktop binaries.
Prefer structured output models over string parsing in UI.

Must follow format above. Output only actionable Kotlin/API guidance.
</constraints>
