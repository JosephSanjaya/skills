# Concurrency & Parallelism (2025/2026)

Modern Python concurrency defaults to structured concurrency (asyncio/anyio) and leverages free-threading for CPU-bound tasks.

## 1. Structured Concurrency (Python 3.11+)

Always use `asyncio.TaskGroup` instead of `asyncio.gather`.
*   **Behavior**: Sibling tasks are cancelled immediately if any task raises an exception.
*   **Errors**: Raises `ExceptionGroup`, handled via `except*`.

```python
async def run_tasks():
    try:
        async with asyncio.TaskGroup() as tg:
            t1 = tg.create_task(fetch_data("A"))
            t2 = tg.create_task(fetch_data("B"))
        # block exits when all tasks complete. Access results: t1.result()
    except* ValueError as eg:
        for e in eg.exceptions:
            logger.error(f"Val error: {e}")
```

## 2. Cancellations & Timeouts

Use `asyncio.timeout` for scoped cancellation:
```python
async def request_with_timeout():
    try:
        async with asyncio.timeout(2.0):  # raises TimeoutError
            await fetch_data("C")
    except TimeoutError:
        logger.warning("Request timed out")
```
*   **Rule**: Always propagate `CancelledError` if caught. Clean up resources in `finally` blocks.

## 3. GIL Removal & Free-Threading (PEP 703)

In Python 3.14 (released Oct 2025), free-threading is fully supported and no longer experimental. Single-threaded overhead is reduced to 5-10%.

### Key mechanisms:
1.  **Biased Reference Counting**: Thread-owner uses fast non-atomic updates; borrower threads use atomic updates.
2.  **Deferred Reference Counting**: Skips tracking for certain specialized runtime objects.
3.  **Immortal Objects**: Constants (small ints, interned strings) have constant ref count, avoiding thread contention.
4.  **Python Critical Sections**: Fine-grained locking on containers (lists/dicts) instead of a single global lock.

### Check GIL status at runtime:
```python
import sys
# C extensions not compiled with free-threading support silently re-enable the GIL.
# Always check after all imports have completed.
print(sys._is_gil_enabled()) 
```

### Core Concurrency Matrix:
*   **I/O Bound**: Use `asyncio` or `anyio`.
*   **CPU Bound (traditional)**: Use `ProcessPoolExecutor` or `multiprocessing`.
*   **CPU Bound (free-threaded)**: Run on `3.14t` with threads / `ThreadPoolExecutor`. Keep shared state safe with explicit `threading.Lock`.
*   **Blocking calls**: Offload from event loop to executor:
    ```python
    res = await asyncio.get_running_loop().run_in_executor(None, blocking_func, arg)
    ```
