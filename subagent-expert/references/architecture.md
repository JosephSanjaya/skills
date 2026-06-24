# Subagent Architecture Topologies & Design Patterns

Decouple complex tasks. Prevent context dilution. Choose right topology based on parallelizability.

## 1. Orchestration Topologies

| Topology | Control Mechanism | Parallelizability | Cost Overhead | Optimal Use Cases |
| :--- | :--- | :--- | :--- | :--- |
| **Manager / Worker** | Lead agent plans, delegates. Workers stateless, specialized. | High (up to 10 workers) | ~15x chat rate | Breadth-first research, parallel file scans. |
| **Sequential Pipeline** | State transitions sequentially through fixed stages. | None (serial) | ~4x-8x chat rate | Bounded workflows (e.g. compile -> lint -> test). |
| **Split-and-Merge** | Workspaces split; processed in parallel; merged via AST. | Moderate (dependency capped) | Variable | Repository migrations, test suite generation. |
| **Evaluator-Optimizer** | Generator loop + adversarial critic. Iterative. | Low (serial loop) | Capped by loop exit | High-fidelity drafting, security validation. |

## 2. Core Heuristics

### Parallel Read vs. Sequential Write Heuristic
- **Reads parallelize**: Spawning 3-5 read-only subagents to search/parse code/logs cuts research latency by ~90%.
- **Writes serialize**: Multiple agents writing to same files/workspace causes merge conflicts, AST breaks, conflicting decisions.
- **Single-Writer rule**: Keep writes single-threaded. Use subagents for parallelized intelligence gathering (reading). Route synthesis and code writing to single thread.

### Concurrency Effort Scaling Bounds
- **1 Agent (3-10 tool calls)**: Simple fact-finding, single-symbol lookups.
- **2-4 Agents (10-15 tool calls each)**: Comparative analysis, trade-off evaluations.
- **10+ Agents**: Deep repository-wide research, multi-module migration planning.
- *Diminishing Returns*: Multi-agent coordination degrades performance if single-agent baseline success >45% or tasks tightly coupled.
