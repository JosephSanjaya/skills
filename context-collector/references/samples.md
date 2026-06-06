# Sample Prompts and Outputs

## Trigger Prompts

- "Analyze this codebase and map the architecture"
- "I inherited an unfamiliar codebase, help me understand it"
- "Gather context on this repo before we start working"
- "Map the dependencies in this project"
- "Do architecture recovery on this monolith"
- "Explore this codebase and tell me what's scary"
- "Understand how exception handling works in this system"

## Sample gather_context.py Output

```json
{
  "project_type": "android",
  "entry_points": [
    "app/src/main/java/com/example/MyApplication.kt",
    "app/src/main/java/com/example/MainActivity.kt"
  ],
  "config_files": [
    "app/build.gradle",
    "docker-compose.yml",
    "app/src/main/res/values/strings.xml"
  ],
  "module_structure": {
    "modules": ["app", "core", "feature-auth", "feature-payments"],
    "build_system": "gradle",
    "has_settings_gradle": true
  },
  "file_counts": {
    ".kt": 247,
    ".xml": 89,
    ".gradle": 12,
    ".json": 34,
    ".yml": 3
  },
  "scary_sections": [
    {
      "file": "core/src/main/java/com/example/LegacyDataSync.kt",
      "lines": 1243,
      "reason": "lines > 500"
    },
    {
      "file": "app/src/main/java/com/example/PaymentProcessor.kt",
      "lines": 634,
      "reason": "lines > 500"
    }
  ]
}
```

## Sample Architecture JSON (after Phase 1)

```json
{
  "project_type": "android",
  "components": {
    "PaymentViewModel": {
      "type": "viewmodel",
      "file": "feature-payments/PaymentViewModel.kt",
      "imports": ["PaymentRepository", "PaymentUseCase"],
      "verified": false
    },
    "PaymentRepository": {
      "type": "repository",
      "file": "core/PaymentRepository.kt",
      "imports": ["PaymentApiService", "PaymentDao"],
      "verified": false
    }
  },
  "dynamic_wiring": {},
  "bounded_contexts": {
    "Payments": {"type": "core", "modules": ["PaymentViewModel", "PaymentRepository", "PaymentUseCase"]},
    "Auth": {"type": "supporting", "modules": ["AuthManager", "TokenRepository"]}
  },
  "context_relations": [
    {"from": "Payments", "to": "Auth", "pattern": "Customer-Supplier", "via": "AuthManager"}
  ],
  "constraints": {},
  "scary_sections": ["LegacyDataSync.kt (1243 lines)", "PaymentProcessor.kt (634 lines)"],
  "verified": []
}
```

## Sample C4 Level 2 Prompt

```
Given this SQLite schema of symbols and imports, generate a C4 Container diagram in PlantUML.
Then cross-examine: does each container match a real directory or Gradle module in the manifest?
Flag any container that doesn't correspond to a physical build artifact.
```

## Registry Wire Discovery Pattern

Grep sequence for finding dynamic wiring:
```bash
rg "importlib|ServiceLoader|registerPlugin|pluginRegistry" --type py
rg "loadClass|forName|Class.forName" --type kotlin
cat plugin-registry.json  # read alongside loader code
```
