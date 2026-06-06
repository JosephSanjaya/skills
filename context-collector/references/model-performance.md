# TOCS Benchmark — Model Performance

## Theory of Code Space (TOCS)

Procedurally generated codebases, partial observability. Agent gets action budget:
`LIST(d)` `OPEN(f)` `SEARCH(q)` `INSPECT(f,s)` `DONE()`

Goal: produce JSON schema of architecture + find 3 planted constraints:
1. **Forbidden Dependency** — "Module A must not import module C"
2. **Interface-Only Access** — "Module X accesses Y only through interface Z"
3. **Validation Chain** — "Data passes validation before reaching module W"

## Edge Types (discovery difficulty order)

| Edge | Discovery Method | Difficulty |
|------|-----------------|------------|
| Imports | Static AST parsing | Easy |
| Calls API | Read function bodies | Medium |
| Registry Wires | Read config file + registry loader (no static import) | Hard |
| Data Flows To | Understand full pipeline orchestration | Hardest |

**Registry Wires critical note:** dynamic loading via `importlib` + JSON/YAML config. No static import statement exists. Agent must read BOTH the config file AND the registry's loading logic.

## Model Results

| Model | Import Recall | Unique Edge Discovery | Belief Stability | Failure Mode |
|-------|-------------|----------------------|-----------------|--------------|
| GPT-5.3-Codex | 69% | High | Stable, high variance (F1: 0.392–0.719) | Moderate edge over-generation |
| Claude Sonnet 4.6 | 55% | Excellent | Near-perfect precision (0.983), monotonic | High token cost (exhaustive reads) |
| Gemini 2.5 Flash | Low | Minimal | Monotonic, zero correct-edge loss | Conservative heuristics = low recall |
| Gemini 2.5 Pro | 11–12% | Weak | **CATASTROPHIC COLLAPSE** | Builds F1 0.33 by step 9, drops 12 edges → F1 0.09 |
| Gemini 3 Flash | 9–11% | Minimal | **RECENCY BIAS** | Only reports 3–5 recently opened files |
| Gemini 3.1 Pro | Low–Moderate | Variable | Unstable (F1: 0.203–0.458) | Least consistent |

## Root Cause of Failures

Transformer self-attention = O(n²) pairwise token relationships → attention budget depletes as context grows → recency bias: recent code snippets overwrite earlier structural mappings in working context.

## Belief Externalization Problem

Agents successfully locate files + execute correct paths **but fail to serialize** discoveries into structured representations.

**Fix:** Write architecture JSON after EVERY file access. Never declare flow understood until component broken + failure cascade verified against serialized belief.

```json
{
  "components": {"ModuleA": {"type": "service", "imports": ["ModuleB"]}},
  "dynamic_wiring": {"registry.json": {"loads": ["PluginA", "PluginB"]}},
  "constraints": {"forbidden": [["ModuleA", "ModuleC"]]},
  "verified": []
}
```
