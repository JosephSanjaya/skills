# Profiling & Memory Optimization (2025/2026)

Identify bottlenecks quantitatively before attempting optimizations.

## 1. Profiling Stack

*   **py-spy**: Sampling profiler for production. Attaches to running process with near-zero overhead. No instrumentation or restart required.
    ```bash
    py-spy record -o profile.svg --pid <PID> --duration 60
    py-spy top --pid <PID>
    ```
*   **scalene**: Development line-level profiler. Attribute execution time to Python vs Native C, memory usage, and GPU overhead. Low overhead (~1.3x).
    ```bash
    scalene my_script.py
    ```
*   **memray**: Bloomberg's memory profiler. Identifies memory leaks, allocations, and heap fragmentation.
    ```bash
    memray run my_script.py
    memray flamegraph memray-my_script.bin
    ```

## 2. Memory Tuning

### instance `__slots__`
Eliminates default `__dict__` overhead. Reduces instance memory footprint by 40-50% and improves attribute access.
*   **When**: Class has >10,000 active instances.
*   **Trade-off**: Prevents adding dynamic properties at runtime.
```python
class Record:
    __slots__ = ("id", "timestamp", "payload")  # Declared fixed attributes
    def __init__(self, id: int, timestamp: float, payload: str):
        self.id = id
        self.timestamp = timestamp
        self.payload = payload
```

### Tuning Generational Garbage Collector (GC)
CPython immediately reclaims objects when reference count is 0. Circular references are handled by generational GC.

Adjust GC thresholds for ETL/high-memory jobs to avoid "stop-the-world" sweep overhead:
```python
import gc

# Increase generation 0 threshold to delay sweeps during heavy allocations
gc.set_threshold(700 * 10, 10, 10) 
```

| Generation | Contents | Scan Strategy |
| :--- | :--- | :--- |
| **Gen 0** | Ephemeral, loop local vars | Scanned very frequently. Keep thresholds low for general apps. |
| **Gen 1** | Function scope, middle lifespan | Scanned moderately. |
| **Gen 2** | Globals, long term caches | Scanned rarely. |
