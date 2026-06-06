# Multi-Agent Context Gathering

## When to Use Multi-Agent

| Task | Single Agent | Multi-Agent Workflow |
|------|-------------|---------------------|
| <5 modules, familiar project | ✓ | overkill |
| 10+ modules, unknown codebase | | ✓ |
| Need git + static + DI in parallel | | ✓ |
| Architecture recovery for onboarding | | ✓ |

Trigger: `Workflow({ name: 'architecture-recovery', args: { repo_root: '/path/to/repo' } })`

## Agent Roles

| Agent | Input | Output |
|-------|-------|--------|
| `static-scan` | repo root | gather_context.py JSON |
| `git-archaeology` | repo root | top churned files + recent commits |
| `dynamic-wiring` | repo root | Koin modules, ServiceLoader, registry files |
| `module:X` | module path + context | MODULE_ANALYSIS_SCHEMA JSON |
| `synthesize` | all above | final architecture.json |

## Handoff Schema (MODULE_ANALYSIS_SCHEMA)

Each per-module agent returns:
```json
{
  "module_name": "feature-payments",
  "components": [
    {
      "name": "PaymentViewModel",
      "type": "viewmodel",
      "file": "feature-payments/PaymentViewModel.kt",
      "imports": ["PaymentUseCase", "PaymentRepository"],
      "exports": [],
      "bounded_context": "Payments",
      "is_scary": false
    }
  ],
  "bounded_context": "Payments",
  "context_type": "core",
  "context_relations": [
    { "to_context": "Auth", "pattern": "Customer-Supplier", "via": "AuthManager" }
  ],
  "dynamic_wiring": [],
  "constraints": { "forbidden": [], "interface_only": [] },
  "verification_targets": ["PaymentViewModel.kt"]
}
```

## Belief Externalization (critical)

Multi-agent amplifies the single-agent belief collapse problem. Every agent must:
1. Read → update local JSON belief → continue
2. Return structured schema (not prose) so synthesizer can merge
3. Never declare "I understand X" without schema output proving it

The `synthesize` agent merges ALL findings. The architecture.json is the single source of truth.

## Android/Kotlin-Specific Agent Tips

Per-module agents on Android repos: prioritize in this order:
1. `*Module.kt` (Koin DI) — tells you what the module owns
2. `*ViewModel.kt` — business logic entry points
3. `*UseCase.kt` / `*Repository.kt` — domain layer
4. `NavGraph*.xml` / `*NavHost*.kt` — navigation structure
5. `*Screen.kt` / `*Fragment.kt` — UI entry points

Skip bodies until signatures confirm relevance — use Serena:
```
# Preferred: Serena (LSP-accurate, no grep noise)
get_symbols_overview(relative_path="path/to/ModuleName.kt")

# Fallback only if Serena unavailable:
rg "^(class|object|interface|fun )" ModuleName.kt | head -20
```

Dynamic wiring in Android = Koin modules. Always trace:
- `startKoin { }` call (app entry) → rg in Application.kt (it's an init call)
- `@Module @ComponentScan @AutoService` → `find_implementations(name_path="ModuleContributor", relative_path="...")` via Serena
- `settings.gradle.kts` include list → rg/glob (it's a config file)

## Token Budget

With a 16-agent cap, scale module parallelism:
- <16 modules: all in parallel in Phase 2
- 16-32 modules: batch into groups of 8
- 32+ modules: pipeline with `scary + hot files first` priority ordering

```js
// Priority ordering: scary + hot files first
const prioritized = [
  ...modules.filter(m => hotFiles.some(f => f.includes(m))),
  ...modules.filter(m => !hotFiles.some(f => f.includes(m))),
]
```

## Verification After Synthesis

After getting architecture.json, verify top 3 claimed dependencies:
1. Pick component A → its `imports` list says it depends on component B
2. Serena `find_referencing_symbols(name_path="ComponentB", relative_path="path/to/ComponentA.kt")` — confirm real usage (preferred over grep)
3. Fallback: `rg "import.*ComponentB" path/to/ComponentA.kt`
4. If not found: mark `verified: false`, note discrepancy

Never ship architecture.json with all `verified: false` — validate at least the core bounded context.
