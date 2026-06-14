# Clean Code & Design Patterns (2025/2026)

Leverage modern syntax features and structural typing to minimize boilerplate.

## 1. PEP 695 Generics (Python 3.12+)

Uses compact type parameter syntax. Eliminates verbose `TypeVar` declarations.

```python
# Generic Function
def first[T](items: list[T]) -> T:
    return items[0]

# Generic Class
class Stack[T]:
    def __init__(self) -> None:
        self._items: list[T] = []
    def push(self, item: T) -> None:
        self._items.append(item)

# Type Statement (Alias)
type Vector = list[float]
type Callback[**P] = Callable[P, None]
```

## 2. Protocols vs ABCs

*   **Protocol (Structural / Duck Typing)**: Best for defining boundaries at DI seams. Decoupled, implementers do not need to inherit.
    ```python
    from typing import Protocol, runtime_checkable

    @runtime_checkable  # Allows isinstance() checks (2-20x faster in 3.12)
    class Writer(Protocol):
        def write(self, data: str) -> int: ...
    ```
*   **ABC (Nominal Typing)**: Best when you want nominal subtyping and shared helper implementations.

## 3. Structural Pattern Matching (Python 3.10+)

Matches type shapes and extracts nested values. Faster bytecode than `if/else` on 3.11+.

```python
def handle_event(event):
    match event:
        case ["quit"]:
            sys.exit(0)
        case ["resize", int(w), int(h)]:
            resize_window(w, h)
        case {"type": "error", "msg": message}:  # Matches dict shape
            logger.error(message)
        case Request(method="GET" | "HEAD", path=p): # Matches class attributes
            route_get(p)
        case _:
            raise ValueError("Unknown event")
```

### Gotchas:
1.  **Capture Trap**: `case HTTPStatus.OK:` matches status. But `case ok:` captures the value, matching *any* input. Use dotted names or literals.
2.  **Order**: Python evaluates top-to-bottom. Put specific cases before generic catch-all patterns.

## 4. Lazy Evaluation

Always prefer generators for streaming large datasets to keep memory consumption flat.
```python
def read_large_file(file_path: Path) -> Generator[str, None, None]:
    with open(file_path, "r") as f:
        for line in f:
            yield line.strip()
```
*   **itertools**: Use `itertools.batched()` (3.12+) for chunking:
    ```python
    import itertools
    for chunk in itertools.batched(large_generator(), n=100):
        process_chunk(chunk)
    ```
