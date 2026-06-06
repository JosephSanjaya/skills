---
name: context-collector
description: Deep architecture recovery, context gathering, and root cause analysis for unfamiliar or undocumented codebases. Use when asked to analyze a codebase, understand its architecture, map dependencies, gather context before a task, do architecture recovery, explore an unknown repo, or investigate a production bug/regression. Triggers on: "analyze this codebase", "understand architecture", "gather context", "map dependencies", "architecture recovery", "unfamiliar codebase", "context gathering", "explore codebase", "what is the architecture", "I inherited this code", "understand this repo", "why did X break", "root cause", "production bug", "incident investigation", "postmortem", "regression", "debug this".
---

# Context Collector

<instructions>
Delineate workflows, use codebase graph queries with required parameters, fallback to Serena symbol analysis with accurate schema signatures, and execute history mining to recovery architecture and resolve root causes.
</instructions>

## Quick Start

```bash
# Single-agent (small repos, <10 modules)
python3 ~/.claude/skills/context-collector/scripts/gather_context.py <repo-root>

# Multi-agent (large/unknown repos, 10+ modules)
# Workflow({ name: 'architecture-recovery', args: { repo_root: '/path/to/repo' } })
# Script: ~/.claude/skills/context-collector/workflows/architecture-recovery.js
```

`gather_context.py` outputs: `project_type`, `entry_points`, `config_files`, `module_structure`, `file_counts`, `scary_sections`, `git_hot_files`, `di_wiring`, `android_signals` (Android repos).

## When to Use Multi-Agent

Use `architecture-recovery` workflow when: 10+ modules, unknown codebase, or need git + static + DI in parallel. Single-agent for small focused tasks.

## Decision: Tool Priority

**Symbol lookup: CBM first → Serena fallback → grep last.** Never open full file if a symbol tool answers.

> [!IMPORTANT]
> All Codebase Memory MCP (CBM) tools (`search_graph`, `query_graph`, `get_code_snippet`, `trace_path`) require the `project` parameter specifying the exact indexed project name (e.g., `"Users-jsanjaya-Projects-skills"`).

<decision_tree>
| Layer | Tool | Use when |
|-------|------|----------|
| **1** | **CBM `search_graph`, `query_graph`, `get_code_snippet`** | **DEFAULT — all code symbol/call/coupling lookup if indexed (requires `project` parameter)** |
| 2 | Serena `find_symbol`, `get_symbols_overview`, `find_implementations`, `find_referencing_symbols`, `find_declaration` | CBM not indexed / stale / incomplete — real-time LSP, always current |
| 3 | `rg`, glob | **Non-code files only**: XML, YAML, Gradle, string literals, configs |
| 4 | `rg` on `.kt`/`.java` | Last resort when CBM + Serena both fail |
| 5 | FAISS/embeddings | Conceptual/fuzzy search only |

**Tool Routing Steps:**
- CBM indexed → **CBM always first**; Serena for precision follow-up (e.g. `find_referencing_symbols` after `search_graph`)
- CBM not indexed → Serena only (skip grep on code files)
- Config / XML / YAML / nav graphs → `rg`/glob only (Serena/CBM do not parse non-code)
</decision_tree>

## CBM Query Patterns (High-Value, Grep-Impossible)

Use these before any grep/Read on code tasks. One CBM query = 200–400 tokens vs 5,000+ tokens of grep context.

<query_patterns>
### Refactor blast radius — who calls X?
```cypher
// Execute using query_graph(project="<project_name>", query="...")
MATCH (caller:Function)-[r:CALLS]->(target:Function)
WHERE target.name = '<function_to_change>'
RETURN caller.name, caller.file_path, caller.start_line, r.confidence, r.strategy
ORDER BY r.confidence DESC
```
Interpret: `confidence ≥ 0.85` = real callers (update); `0.55–0.84` = verify; `< 0.55` = noise.

### PR completeness — what files always change together?
```cypher
// Execute using query_graph(project="<project_name>", query="...")
MATCH (a:File)-[r:FILE_CHANGES_WITH]->(b:File)
WHERE a.file_path IN ['<changed_file>']
  AND r.coupling_score > 0.7
RETURN b.file_path, r.coupling_score, r.co_changes
ORDER BY r.coupling_score DESC
```
**Note**: use `file_path` property, NOT `name` — querying `name` returns 0 rows.

### DRY enforcement — copy-paste across modules?
```cypher
// Execute using query_graph(project="<project_name>", query="...")
MATCH (a:Function)-[r:SIMILAR_TO]->(b:Function)
WHERE r.jaccard > 0.9
  AND r.same_file = false
  AND a.file_path CONTAINS 'src/'
  AND b.file_path CONTAINS 'src/'
RETURN a.name, a.file_path, b.name, b.file_path, r.jaccard
ORDER BY r.jaccard DESC
```

### Onboarding — find entry point by intent
```
search_graph(project="<project_name>", query="<verb noun context>", label="Function", file_pattern="src/")
```
Then follow with CALLS inbound/outbound queries. 3 queries = full subsystem map.

### Module decoupling audit
```cypher
// Execute using query_graph(project="<project_name>", query="...")
MATCH (a:File)-[r:FILE_CHANGES_WITH]->(b:File)
WHERE r.coupling_score > 0.7
  AND a.file_path CONTAINS 'src/'
RETURN a.file_path, b.file_path, r.coupling_score, r.co_changes
ORDER BY r.coupling_score DESC LIMIT 20
```
</query_patterns>

## CBM Anti-Patterns (Never Do)

<anti_patterns>
| Anti-pattern | Why | Fix |
|-------------|-----|-----|
| `get_architecture` cold each session | ~2K token schema dump, same every time | Read cached notes or use `get_graph_schema` once |
| `search_graph` without `file_pattern` | Vendored/generated code dominates results | Always add `file_pattern="src/"` or `CONTAINS 'src/'` |
| `trace_path` in C codebase for function-level chain | Resolves to Module (aggregate), not Function — granularity lost | Use `query_graph` CALLS directly |
| `FILE_CHANGES_WITH` filter on `name` property | File nodes store path in `file_path`, not `name` — 0 rows | Use `a.file_path CONTAINS '...'` |
| `SIMILAR_TO` without vendored filter | 18K+ vendored functions dominate below jaccard=0.95 | Add `NOT a.file_path CONTAINS 'tools/'` for strict src-only |
| Rely on `complexity`, `lines`, `is_entry_point` | Not populated in current index version | Use `end_line - start_line` for length; find entry points via call degree |
| `NOT exists()` / `NOT (n)<-[:CALLS]-()` | Both unsupported in Cypher dialect | Use degree aggregation queries instead |
| Calling tools without `project` | Tool returns a required parameter error | Always pass `project` parameter to CBM tools |
</anti_patterns>

## Serena Tool Map

When CBM is stale/missing, route to Serena using the correct API signatures:

<serena_tool_map>
- `find_symbol(name_path_pattern, relative_path=None, include_body=False, substring_matching=False, include_kinds=None, depth=None, max_matches=None)`
  - Performs global or scoped search for symbols by name path pattern. Replaces noisy grep searches for class names.
- `get_symbols_overview(relative_path, depth=None)`
  - Retrieves a summary of symbol signatures (classes, functions, methods) in a specified file/directory without code bodies.
- `find_implementations(name_path, relative_path=None, include_info=False)`
  - Finds all symbols implementing an interface or abstract method.
- `find_referencing_symbols(name_path, relative_path=None, include_kinds=None)`
  - Locates all symbols referencing a target symbol with context lines.
- `find_declaration(relative_path, regex, containing_symbol_name_path=None, include_body=False, include_info=False)`
  - Jumps directly to a symbol's definition using regex context to locate the call site.
</serena_tool_map>

## Mode Selection

| Mode | When | Entry Point |
|------|------|-------------|
| **Architecture Recovery** | Unknown codebase, pre-task context | Phase 1 → 2 → 3 below |
| **RCA** | Production bug, regression, incident | RCA Phase 0 → history mining → 5 Whys |
| **Combined** | Bug in unfamiliar codebase | Architecture Recovery first, switch to RCA at anomaly |

## Three-Phase Architecture Recovery Protocol

### Phase 1: Static Recovery

1. Run `gather_context.py` → JSON skeleton
2. If CBM indexed: `search_graph(project="...", name_pattern="...")` for top-ranked components; else `find_symbol(name_path_pattern="...")` via Serena
3. Trace entry points 2-3 levels deep — use `get_symbols_overview(relative_path="...")` for signatures only
4. Group by business noun → bounded contexts
5. Find ACLs: CBM `search_graph(project="...", name_pattern=".*Adapter|.*Mapper")` or Serena `find_symbol(name_path_pattern=".*Adapter|.*Mapper", substring_matching=true)` — only fall back to `rg` if both unavailable
6. Find dynamic wiring: `rg "ServiceLoader\|importlib\|AutoService\|startKoin"` in Gradle/config files + CBM `search_graph(project="...", name_pattern=".*ModuleContributor.*")` → Serena `find_implementations(name_path="ModuleContributor", relative_path="...")` for Koin modules

**Output:** `architecture.json` skeleton — update after EVERY file access

### Phase 2: Dynamic Tracing

1. Pick one user-visible flow → find unique UI string
2. Set breakpoint → execute → read call stack backward
3. Alternate bottom-up (call stack) with top-down (who owns state)
4. Map exception handling: per-module failure classes vs centralized recovery strategies
5. If anomaly found: switch to **RCA Protocol** for that component before continuing

### Phase 3: Hybrid Agent Exploration

- `LIST` → `SEARCH` → `INSPECT` → `OPEN` (never skip)
- Registry wires: read config file + registry loader TOGETHER — no static import exists
- Validation: break component → run tests → verify failure cascade matches `architecture.json`

## RCA Protocol (Root Cause Analysis)

### Bias-Check First

State hypothesis explicitly before touching code: `HYPOTHESIS: [component] fails because [mechanism]`

Force ≥2 alternative hypotheses. Common bias traps:
- **Anchoring** — first error = root cause. Counter: list 2+ failure vectors
- **Confirmation** — only read supporting logs. Counter: search for disconfirming evidence
- **Hyperbolic discounting** — quick fix to unblock. Counter: ask "does this fix root cause or defer?"

### History Mining (No Bisect)

```bash
# Find when literal string count changed (add/remove)
git log -S "symbolName" --oneline -- path/to/dir

# Find commits where diff matches pattern (use when name preserved, internals changed)
git log -G "pattern|regex" --oneline -p -- src/

# Find commits by message keyword (ticket/refactor)
git log --grep="TICKET-123" --oneline

# Blame a function range
git blame -L <start>,<end> path/to/file
```

Rule: `-S` first (faster). Switch to `-G` when refactor preserves name but changes internal structure.

### 5 Whys

Each answer requires **verifiable evidence** (log line, test, code reference).

| Level | Question | Answer | Evidence |
|-------|----------|--------|----------|
| Why 1 | Why did symptom occur? | | log/metric |
| Why 2 | Why did cause 1 happen? | | code ref |
| Why 3 | Why did cause 2 happen? | | test/config |
| Why 4 | Why did cause 3 happen? | | PR/commit |
| Why 5 | What process gap enabled this? | | process doc |

Stop at the **process gap** — that's the systemic fix target.

### Structural Pattern Matching

| Pattern | Signal | How to Find |
|---------|--------|-------------|
| Tribal knowledge erosion | Works for senior, fails after handoff | Check ADRs — does rule exist anywhere? |
| Architectural drift | Works isolated, fails integrated | Serena `find_symbol(name_path_pattern="Adapter")` / `find_symbol(name_path_pattern="Mapper")` or `rg` at boundaries |
| Cargo cult guard | Code checks constraint that no longer applies | `git log -S "condition"` → verify constraint still valid |
| State mutation race | Flaky under load | Find dirty-row flags + transactional boundaries |
| Regression from refactor | Broke after rename/move | `-G "old_pattern"` across affected paths |

### Fix Classification

| Class | Definition | Action |
|-------|-----------|--------|
| Symptomatic | Stops error, doesn't fix root cause | Create tech debt ticket + ship |
| Causal | Fixes Why-3/4 level | Implement now |
| Systemic | Fixes Why-5 process gap | ArchUnit test, ADR, or pipeline gate |

Never ship only symptomatic fix without a systemic ticket.

### Postmortem (production incidents only)

Triggers: user-visible downtime, data loss, manual prod intervention, monitoring missed alert.

**Agenda (90 min max):** Action item review (10) → Timeline walkthrough (30) → Core analysis/5 Whys (30) → Action items (20).

**Three-rule policy:** Max 3 action items. All → tickets → next sprint. Every postmortem starts with prior action item review.

Store at: `docs/postmortems/YYYY-MM-DD-incident-title.md`

## Android/Kotlin Starting Points

Priority order (read in this order):

```
1. settings.gradle.kts                          — all modules (rg/glob, it's a config file)
2. app/src/main/AndroidManifest.xml             — permissions, activities (rg/glob)
3. navigation/*.xml / *NavHost*.kt              — user flows (XML: rg; Kt: CBM search_graph → Serena find_symbol)
4. *Application.kt + startKoin { }              — DI root (CBM search_graph → Serena find_symbol)
5. *Module.kt (@Module @ComponentScan)          — what each module owns (CBM search_graph → find_implementations)
6. journey/*/presentation/*ViewModel.kt         — business logic (CBM search_graph or find_symbol)
7. capability/*/domain/*UseCase.kt              — domain ops (CBM trace_path or find_symbol)
8. capability/*/data/*RepositoryImpl.kt         — data layer (CBM search_graph → find_implementations)
```

Android dynamic wiring uses Koin `@Module`, `@ComponentScan`, and `@AutoService` annotations.
They are auto-discovered via `ModuleContributor`.
Trace path:
1. Locate `startKoin { }` call (usually in application class).
2. Query CBM: `search_graph(project="...", name_pattern=".*ModuleContributor.*")` or use Serena: `find_implementations(name_path="ModuleContributor", relative_path="...")`.
3. Locate `@AutoService` providers.

Key `android_signals` from `gather_context.py`:
- `journey_modules` — user-facing flows, each = bounded context
- `capability_modules` — reusable business slices shared by journeys
- `layer_structure` — detected layers (domain/data/presentation/ui/remote/bundle)

## Belief Externalization (critical)

After EVERY file access: update `architecture.json`. Never declare "I understand X" until:
- Component in JSON
- Import commented out
- Tests run
- Failure cascade matches JSON

## References

- [references/phase-protocol.md](references/phase-protocol.md) — full protocol + architecture.json schema
- [references/rca-protocol.md](references/rca-protocol.md) — RCA full detail: history mining, 5 Whys, postmortem, output format
- [references/multi-agent.md](references/multi-agent.md) — multi-agent workflow, handoff schema, Android agent tips
- [references/retrieval-funnel.md](references/retrieval-funnel.md) — layer details, RepoMap, MCP stats
- [references/model-performance.md](references/model-performance.md) — TOCS benchmark, edge types, model failure modes
- [references/archaeology-frameworks.md](references/archaeology-frameworks.md) — Rozlog/OOPSLA, Feathers, edge-diving
- [references/ddd-patterns.md](references/ddd-patterns.md) — bounded context patterns, context mapping
- [references/exception-recovery.md](references/exception-recovery.md) — CFG soundness, debugger commands
- [references/samples.md](references/samples.md) — sample outputs, prompt templates
