---
name: ktor-expert
description: "Expert guide for Ktor client/server. Use when user mentions Ktor, HttpClient, embeddedServer, engine (OkHttp, Darwin, CIO, Netty), token refresh, Mutex, HttpRequestLifecycle, custom Ktor plugins, MockEngine, or testApplication."
---

# Ktor Expert

<instructions>
Delineate Ktor references, enforce client engine selection guidelines, apply token refresh double-check Mutex structures, mandate client disconnect cancellations, and audit with audit_ktor_code.py.
</instructions>

## Index

Use these references for specific Ktor domains:
- Client architecture, engine selection, connection pool tuning, OAuth2 token refresh, certificate pinning: read [client.md](file:///Users/jsanjaya/.gemini/config/skills/ktor-expert/references/client.md)
- Server setup, Netty tuning, first-party DI, HTMX, typed config mapping, request lifecycle cancellation: read [server.md](file:///Users/jsanjaya/.gemini/config/skills/ktor-expert/references/server.md)
- Testing (MockEngine, testApplication, DI overrides, parallel DB isolation): read [testing.md](file:///Users/jsanjaya/.gemini/config/skills/ktor-expert/references/testing.md)

## Core Guidelines (Terse)

### Client Engine Choice
- OkHttp (Android) + Darwin (iOS) for mobile. Handles HTTP/2, system proxy, backgrounding, VPN, ATS.
- CIO for server, CLI, Native (if HTTP/2 not required). Note: CIO client is HTTP/1.x only.

### Client Lifecycle
- Create one HttpClient singleton, reuse it, close at app shutdown. Per-request client leaks threads/connections.

### Token Refresh
- Use `Auth` plugin with `bearer` flow. Single-flight refresh is built-in.
- Wrap refresh calls in a coroutine `Mutex` with double-check lock. Mark refresh request with `markAsRefreshTokenRequest()` to prevent infinite loops.

### Server Lifecycle & Cancellation
- Use `HttpRequestLifecycle` plugin (`cancelCallOnClose = true`) to propagate cancellation on client disconnect (CIO/Netty).
- Keep route tasks cooperative: use `ensureActive()` or check `isActive`.

### Configuration
- Use `environment.config.getAs<T>()` in Ktor 3.5.0+ to deserialize root ApplicationConfig directly into data classes.

### Dependency Injection
- Use first-party `ktor-server-di` via `dependencies { provide<T> { ... } }` to avoid external DI overhead.

## Code Examples
- Client setup: [client_setup.kt](file:///Users/jsanjaya/.gemini/config/skills/ktor-expert/examples/client_setup.kt)
- Server setup: [server_setup.kt](file:///Users/jsanjaya/.gemini/config/skills/ktor-expert/examples/server_setup.kt)

## Static Code Audits
- Run Python validator to inspect codebase for Ktor anti-patterns:
  ```bash
  python3 /Users/jsanjaya/.gemini/config/skills/ktor-expert/scripts/audit_ktor_code.py <path/to/project>
  ```

<constraints>
Always verify Ktor client engine target compatibility and enforce the double-checked lock Mutex pattern for authentication.
</constraints>
