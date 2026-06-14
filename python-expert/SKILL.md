---

name: python-expert
description: "Expert Python development guidelines covering Astral tooling (uv, ruff, ty), structured concurrency (TaskGroup, ExceptionGroup), high-performance serialization (msgspec, Pydantic v2), memory optimization, and no-GIL architecture. Trigger this skill whenever the user mentions Python libraries, writing Python scripts, optimizing Python code, debugging async or threading issues, configuring pyproject.toml, or querying python packaging, even if they only ask for a simple python helper function."
---

# Python Expert Skill

Core guidelines for modern (2025/2026) high-performance Python development.

<instructions>
Use progressive disclosure: consult specific reference files for details. Maintain strict token efficiency. Code should be clean, type-safe, and free of conversational fluff.
</instructions>

## 1. Quick Decision Matrix

| Task / Domain | Action / Tool | Details |
| :--- | :--- | :--- |
| **Tooling & Env** | `uv`, `ruff`, `ty` | Consult [tooling-env.md](file:///Users/jsanjaya/.gemini/config/skills/python-expert/references/tooling-env.md) |
| **Concurrency** | `TaskGroup`, `except*`, `anyio` | Consult [concurrency.md](file:///Users/jsanjaya/.gemini/config/skills/python-expert/references/concurrency.md) |
| **Serialization** | `msgspec`, `Pydantic v2` | Consult [serialization.md](file:///Users/jsanjaya/.gemini/config/skills/python-expert/references/serialization.md) |
| **Clean Code** | PEP 695 generics, Protocols, matching | Consult [clean-code.md](file:///Users/jsanjaya/.gemini/config/skills/python-expert/references/clean-code.md) |
| **Profiling & Perf** | `py-spy`, `scalene`, `memray`, `__slots__` | Consult [profiling.md](file:///Users/jsanjaya/.gemini/config/skills/python-expert/references/profiling.md) |

## 2. Directory Structure

All detailed reference materials and examples are partitioned into subdirectories:

*   **References**:
    *   [tooling-env.md](file:///Users/jsanjaya/.gemini/config/skills/python-expert/references/tooling-env.md) — Universal environment setups, lockfiles, and ruff settings.
    *   [concurrency.md](file:///Users/jsanjaya/.gemini/config/skills/python-expert/references/concurrency.md) — Structured concurrency, async timeouts, and free-threaded execution.
    *   [serialization.md](file:///Users/jsanjaya/.gemini/config/skills/python-expert/references/serialization.md) — Comparison of Pydantic v2 and msgspec, including custom validation.
    *   [clean-code.md](file:///Users/jsanjaya/.gemini/config/skills/python-expert/references/clean-code.md) — Generic syntax, structural pattern matching, and ABC vs Protocol.
    *   [profiling.md](file:///Users/jsanjaya/.gemini/config/skills/python-expert/references/profiling.md) — Profiler usage, garbage collector tuning, and memory optimization.
*   **Samples**:
    *   [pydantic_v2.py](file:///Users/jsanjaya/.gemini/config/skills/python-expert/samples/pydantic_v2.py) — Annotated model code.
    *   [async_taskgroup.py](file:///Users/jsanjaya/.gemini/config/skills/python-expert/samples/async_taskgroup.py) — TaskGroup error propagation.
    *   [msgspec_serialization.py](file:///Users/jsanjaya/.gemini/config/skills/python-expert/samples/msgspec_serialization.py) — High-throughput JSON deserializer.

Always read the specific file containing the details required for the task.
