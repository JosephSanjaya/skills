# Five-Layer Retrieval Funnel

## Layers (ordered by preference)

| Layer | Tools | Scope | Cost | Use When |
|-------|-------|-------|------|----------|
| **1: Graph MCP** | **CBM `search_graph`, `query_graph`, `get_code_snippet`** | **Indexed code graph, PageRank, call chains, git coupling** | Pre-indexed | **DEFAULT — all code symbol/call/coupling lookup (requires `project` parameter)** |
| 2: LSP MCP | Serena `find_symbol`, `get_symbols_overview`, `find_implementations`, `find_referencing_symbols`, `find_declaration` | Real-time LSP-backed, always current | Per-call | CBM not indexed, stale, or precision follow-up |
| 3: Text Scan | rg, glob | Non-code files: XML, YAML, Gradle, configs | Zero config, sub-ms | Config values, string literals, non-code |
| 4: Text on code | rg/glob on `.kt`/`.java` | Last resort code search | Sub-ms but noisy | CBM + Serena both unavailable |
| 5: Semantic | FAISS, nomic-embed-text | Fuzzy NL queries | Embedding cost | Conceptual search, staleness OK |

## Tool Selection Rules

**Code files (.kt, .java, .swift, etc.):**
1. CBM indexed → **use CBM first** (`search_graph`, `query_graph`, `get_code_snippet`)
2. CBM stale/missing → use Serena (no grep on code files)
3. Both fail → rg as last resort

**Non-code files (XML, YAML, .toml, .gradle, AndroidManifest, nav graphs):**
- Always rg/glob — Serena/CBM don't parse these

**When to use which CBM tool:**
- `search_graph(project=..., query=..., label=..., file_pattern="src/")` → NL discovery + BM25 (always scope with file_pattern)
- `query_graph(project=..., query=...)` → structural traversal: CALLS, FILE_CHANGES_WITH, SIMILAR_TO
- `get_code_snippet(project=..., qualified_name=...)` → source read (5× fewer tokens than Read/cat)
- `trace_path(project=..., function_name=...)` → TypeScript/Go only; C resolves to Module (not Function)

**When to use which Serena tool:**
- `find_symbol(name_path_pattern, relative_path=None, include_body=False)` → symbol by name/pattern (zero noise vs grep)
- `get_symbols_overview(relative_path, depth=None)` → all signatures in file/directory without bodies
- `find_implementations(name_path, relative_path=None)` → all impls of interface/abstract method
- `find_referencing_symbols(name_path, relative_path=None)` → precise call sites across repo
- `find_declaration(relative_path, regex)` → jump-to-definition

## Why CBM over Serena as primary

CBM builds a persistent graph: PageRank ranking, cross-module call chains, git co-change history (FILE_CHANGES_WITH), structural clone detection (SIMILAR_TO), CALLS with confidence scoring. 83% answer quality, 10x fewer tokens, 2.1x fewer tool calls vs brute-force.

**Unique CBM signals grep/Serena can't provide:**
- `FILE_CHANGES_WITH.coupling_score` — git co-change aggregated as edge weight; impossible from source
- `CALLS.confidence` + `CALLS.strategy` — ranked call resolution (import_map 0.95 → fuzzy 0.28); grep returns every string with zero ranking
- `SIMILAR_TO.jaccard` — structural fingerprint clone detection; works even if function was renamed

Serena is real-time (no stale index) but single-symbol queries — no graph traversal, no git history, no clone detection.

## Why Serena over grep for code

- LSP-backed: understands Kotlin type system, generics, lambdas — grep sees text
- `find_implementations` impossible with grep on complex inheritance
- Zero false positives on symbol names (grep matches comments, strings, variable names)
- `get_symbols_overview` gives clean signature list in one call vs multi-line grep + awk

## Why grep still wins for non-code

- Works on XML, YAML, TOML, Gradle, configs — Serena/CBM don't parse these
- Zero config, zero setup
- Scans ALL files: Dockerfile, JSON wiring maps, nav graph XMLs

## Layer 2a: RepoMap (Aider / CBM internals)

1. tree-sitter AST parse → extract symbol defs + refs
2. Build global dep graph (files=nodes, symbol refs=edges)
3. Personalized PageRank relative to active file
4. Binary search over ranked symbols → fit token budget
5. Render with elision: signatures + `⋮` for bodies
