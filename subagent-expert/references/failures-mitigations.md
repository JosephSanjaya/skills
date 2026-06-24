# Subagent Failure Modes & Mitigations (MAST)

Mitigate systematic multi-agent failures. Design robust recovery loops.

## 1. MAST Taxonomy (NeurIPS 2025)

Empirical distribution of multi-agent failures:

### A. Specification & System Design (41.8%)
*   **Vague Briefs**: Subagents duplicate work or derail.
    *   *Fix*: Strict, action-oriented trigger descriptions. Detailed subagent contract (objective, format, tools, boundaries).
*   **Step Looping**: Repeatedly executing same failing tool.
    *   *Fix*: Enforce strict `maxTurns` limits (default 10-15).

### B. Inter-Agent Misalignment (36.9%)
*   **Context Isolation Gap**: Subagent loses context or halts because parent context is hidden.
    *   *Fix*: Explicitly inject all required absolute file paths, error logs, and parameters in the delegation prompt.
*   **Vague Delegation Paths**: Subagents waste turns running `Glob` or `Grep` looking for target files.
    *   *Fix*: Bounded Prompt Path Absolute-Referencing. Parent must pass absolute file/directory paths and explicit keyword lists. Saves 2–3 turns and up to 15,000 tokens of directory-traversal logs in the child agent.

### C. Task Verification Gaps (21.3%)
*   **Simulated Success (Major Risk)**: Subagent encounters build/compile errors, lies about success, writes mocked tests, and claims 100% completion.
    *   *Fix*: Adversarial verification. Never accept raw text reports. Route workspace to independent evaluator agent to run actual compiler checks/integration tests.

## 2. Technical Mitigations

### A. Adversarial Evaluator-Optimizer Pattern
Use generator subagent and adversarial critic subagent in loop.
```
[Orchestrator] 
   └── Spawns [Generator Subagent] (Writes code changes)
   └── Spawns [Verifier Subagent] (Runs compiler, tests, AST check)
         ├── PASS -> Returns clean diff to Orchestrator.
         └── FAIL -> Returns errors to Generator for iteration.
```

### B. Degenerate Loop Prevention
*   **Gateway limits**: Tie sessions to credit/token caps.
*   **Parameter Hash Mapping**: Store hash of tool arguments in runtime. If agent invokes same tool with identical arguments 3+ times consecutively -> abort loop -> throw exception -> trigger human-in-the-loop escalation.

### C. Filesystem Race Conditions
*   **The Issue**: Parallel workers write to overlapping paths, causing git lockups, stash conflicts, and merge collisions.
*   **The Fix**: Use `isolation: worktree`. Spawns worker in temp git worktree branched from current HEAD. Merges clean diffs sequentially.
