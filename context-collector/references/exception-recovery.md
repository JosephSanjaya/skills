# Exception Handling Recovery

## Static Analysis Soundness Problem

Ignoring exceptions in data flow analysis = **unsound**. If `method()` throws, subsequent state resets are skipped → analyzer unsoundly concludes variable always has reset value.

Fix: transform exceptions into conditional CFG edges → exponential CFG bloat → thousands of dead code paths. Trade-off: sound but imprecise. Use **forward liveness analysis** to kill data structures along exception paths where handler destroys the data.

## Dynamic Tracing Commands

**WinDbg (Windows)**
```
sxe <event>    # break on first/second-chance exception dispatch
sxd <event>    # disable break
sxe c0000005   # break on access violation
```

**GDB (Linux)**
```
catch throw        # pause on any C++ exception throw
catch syscall      # intercept OS-level transitions
```

**Hardware Breakpoints**
- Write memory coordinates to debug registers DR0–DR3
- Triggers INT 1 on read/write/execute — no code patching needed
- Guard pages: change memory page permissions → page-fault on access → one-time trigger for boundary violations

## Fault-Tolerant Patterns — What to Look For

| Pattern | Mechanism | How to Find |
|---------|-----------|-------------|
| **Secure State Change** | Transactional state: failure rolls back to last secure state | Find transactional boundaries + rollback blocks in DB/state managers |
| **Dirty Row Flag** | Transient marker written before mod, cleared on success | Audit DB schemas for boolean dirty/pending columns + state-mutation flows |
| **Inverse Functions** | Opposite function undoes state (reserve → release) | Search for paired ops in catch blocks: `reserveX`/`releaseX`, `lock`/`unlock` |
| **Watchdog** | Detached process monitors heartbeat, restarts on hang/crash | Find independent background threads with ping/pong protocols |
| **Memento** | Serializes object state to external storage before high-risk op, restores on error | Find metadata snapshot instantiation before risky operations |

## Recovery Strategy

Separate two concerns:
1. **Classes of failures** — unique, domain-specific per module
2. **Recovery strategies** — centralized global tactics (replication, rollback, degradation)

Map recovery strategies as global architectural tactics, not per-module details.
