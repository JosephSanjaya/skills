# Three-Phase Architecture Recovery Protocol

## Phase 1: Static & Strategic

**Goal:** Build structural skeleton without running code.

1. Run `gather_context.py` → get JSON skeleton (entry points, manifests, file counts, scary sections)
2. If CBM indexed: `search_graph(project="...", name_pattern="...")` + `get_code_snippet(project="...", qualified_name="...")` for top-ranked components; else use Serena `find_symbol(name_path_pattern="...")` + `get_symbols_overview(relative_path="...")`.
3. Query CBM for: top-ranked files by PageRank, all class signatures, import graph; or Serena for per-file signature sweep.
4. Generate C4 Level 2 diagram from graph data.
5. Apply self-reflective prompting: cross-examine C4 output against build artifacts + package manifests to catch abstraction misalignment.
6. DDD boundary analysis: CBM `search_graph(project="...", name_pattern=".*Adapter|.*Mapper")` or Serena `find_symbol(name_path_pattern="Adapter|Mapper", substring_matching=true)` → find ACLs, map context patterns.

**Output:** Architecture JSON + C4 diagram + DDD map

## Phase 2: Dynamic Tracing & Flow Recovery

**Goal:** Validate static model against runtime behavior.

1. Edge-dive: find unique UI string → set breakpoint → trace call stack backward.
2. Build Request Trace Views (RTVs) for each major flow.
3. Exception mapping:
   - Build sound CFG (transform exceptions to conditional edges).
   - Configure GDB/WinDbg catchpoints for dynamic tracing.
   - Audit for fault-tolerant patterns (Watchdog, Memento, Dirty Row, etc.).
4. Validate Phase 1 architecture JSON against observed runtime flows.

**Output:** Annotated architecture JSON with verified/unverified flags

## Phase 3: Hybrid Agent Exploration

**Goal:** Deep discovery of hidden dependencies (Registry Wires, Data Flows).

**Agent tool harness (token-efficient):**
- `LIST(dir)` — directory structure only (glob/ls).
- `SYMBOL(name)` — CBM `search_graph(project="...", name_pattern="...")` or Serena `find_symbol(name_path_pattern="...")` before opening any file.
- `INSPECT(file)` — Serena `get_symbols_overview(relative_path="...")` — signatures without bodies.
- `TRACE(symbol)` — CBM `trace_path(project="...", function_name="...")` or Serena `find_referencing_symbols(name_path="...", relative_path="...")`.
- `OPEN(file)` — full read only after INSPECT confirms relevance.
- `SEARCH(query)` — `rg` only for non-code files (XML/YAML/configs).
- Rule: **CBM/Serena before grep; grep before full file read**.

**System prompt calibration (Goldilocks zone):**
- No hardcoded procedural rules (fragile).
- Direct heuristics: "grep before read", "externalize after every access".
- Not too loose (no direction), not too rigid (breaks on edge cases).

**Belief externalization after every file access:**
```
INSPECT result → update architecture.json → continue
OPEN result → update architecture.json → continue
```

**Validation gates:**
1. Identify component in architecture.json.
2. Break it (comment out import / delete function).
3. Run tests / compiler.
4. Verify failure cascade matches serialized belief.
5. Mark as `verified: true` in JSON.

**Registry Wires discovery:**
1. Serena `find_implementations(name_path="ModuleContributor", relative_path="...")` → all Koin auto-discovered modules.
2. `rg "ServiceLoader|importlib|AutoService|startKoin"` in config/Gradle files (non-code scan).
3. Find config files: `*.json`, `*.yaml` with plugin/stage/handler lists.
4. Read registry loader code + config together → infer dynamic dependency.
5. Add to architecture.json as `dynamic_wiring` entry.

## Architecture JSON Schema

```json
{
  "project_type": "android|web|backend|...",
  "components": {
    "ModuleName": {
      "type": "service|repository|viewmodel|controller|...",
      "file": "path/to/file",
      "imports": ["OtherModule"],
      "exports": ["InterfaceName"],
      "verified": false
    }
  },
  "dynamic_wiring": {
    "config_file.json": {
      "loader": "path/to/registry.kt",
      "loads": ["PluginA", "PluginB"]
    }
  },
  "bounded_contexts": {
    "Order": {"type": "core", "modules": ["OrderService", "OrderRepository"]},
    "Shipping": {"type": "supporting", "modules": ["ShippingService"]}
  },
  "context_relations": [
    {"from": "Order", "to": "Shipping", "pattern": "ACL", "via": "ShippingOrderAdapter"}
  ],
  "constraints": {
    "forbidden": [["ModuleA", "ModuleC"]],
    "interface_only": [["ModuleX", "ModuleY", "InterfaceZ"]],
    "validation_chain": [["InputHandler", "Validator", "ModuleW"]]
  },
  "scary_sections": [],
  "verified": []
}
```
