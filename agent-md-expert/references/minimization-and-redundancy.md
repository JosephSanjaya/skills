# Minimization & Redundancy

## Controlled Study Findings (Gloaguen et al., 2026)
Empirical analysis across 138 repositories (arXiv:2602.11988) evaluated repository-level context files (such as `AGENTS.md` and `CLAUDE.md`) on benchmarks like SWE-bench Lite and AGENTbench.

### Quantitative Results
- **Performance Impact:** LLM-generated context files *reduced* task success rates by **0.5% to 2%** (averaging ~3% on some setups). Hand-written developer files only provided a minor boost of **+4%**.
- **Resource Inflation:** Both developer-written and LLM-generated context files increased inference costs by **20% to 23%** and added **2.45 to 3.92 steps** per task.
- **Why?** Context files cause agents to execute redundant tests, traverse unnecessary directories, and search too broadly without adding resolving value.

## The Redundancy Penalty
The study showed that when all other documentation was removed, LLM-generated context files improved performance by **2.7%**. This proves context files are not inherently bad; they are bad because they **duplicate existing information** (e.g. README.md, CONTRIBUTING.md, configs) and overwhelm the context window.

## What to Remove (Ruthless Pruning)
1. **Codebase Overviews:** Delete directory trees, file lists, and high-level architecture maps. Agents discover structure dynamically using their tools.
2. **Existing Docs Duplication:** If setup, installation, or configuration instructions are in `README.md` or package manifests, remove them.
3. **Generic Best Practices:** Delete generic advice like "write clean code", "add error handling", "use camelCase", or standard language guidelines (e.g., PEP 8). The model already knows these.
4. **Tooling-Enforceable Rules:** Never list formatting, linting, or type-checking rules. The formatter/linter config (e.g. `biome.json`, `tsconfig.json`, `ruff.toml`) is the source of truth.

## What to Keep (High-Signal Content)
1. **Tool-Specific Commands:** Specify exact test commands, linter commands, and package managers (e.g. "use uv, not pip", "run tests with `pytest -x --tb=short`"). Agents follow exact commands with 1.6-2.5x higher fidelity.
2. **Non-Obvious Constraints:** Document Gotchas that a competent developer cannot discover from code alone (e.g., "always run DB migrations before tests", "do not mock the auth service, use stub endpoints").
3. **Imperative Directives:** Write direct commands instead of narrative prose. Directives (e.g., "Run `pnpm lint --fix`") are followed more reliably than descriptive paragraphs.
