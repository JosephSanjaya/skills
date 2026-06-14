# Serialization & Validation (2025/2026)

Choose serialization tools intentionally based on throughput and validation requirements.

## 1. Pydantic v2

Rust-powered core (`pydantic-core`). Ideal for rich schema validation, application configurations, and complex APIs.

### Performance tips
*   Use `model_validate_json()`: parses JSON directly in Rust using `jiter`. Do not use `model_validate(json.loads())`.
*   Instantiate `TypeAdapter` once at module level and reuse it. Creating it in a loop is extremely slow.
*   Enable strict validation: `ConfigDict(strict=True)` to prevent type coercions.

```python
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class User(BaseModel):
    model_config = ConfigDict(strict=True)  # No coercion allowed
    
    username: str
    email: str
    age: int = Field(gt=0)

    @field_validator("username")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("Too short")
        return v

    @model_validator(mode="after")
    def cross_check(self) -> "User":
        # Cross-field checks here
        return self
```

### Discriminated Unions (Tagged Unions)
Use literal tags for O(1) matching:
```python
from typing import Literal, Union
from pydantic import Field

class Cat(BaseModel): pet_type: Literal["cat"]; meows: int
class Dog(BaseModel): pet_type: Literal["dog"]; barks: float

class Household(BaseModel):
    pet: Union[Cat, Dog] = Field(discriminator="pet_type")
```

## 2. msgspec

Best for high-throughput messaging, streaming pipelines, and serverless.
*   **Speed**: 6-12x faster than Pydantic v2.
*   **Memory**: Uses `Struct` layout, skipping python's `__dict__`.
*   **GC skip**: Use `gc=False` to bypass GC tracking and save 16 bytes per instance.

```python
import msgspec

class Payload(msgspec.Struct, gc=False):
    id: int
    name: str
    tags: list[str]

# Fast parsing
decoder = msgspec.json.Decoder(Payload)
data = decoder.decode(b'{"id": 1, "name": "foo", "tags": ["bar"]}')
```

## 3. HTTP Client Pooling

Always reuse client instances (connection pooling). Never create clients inside hot loops.

```python
import httpx

# Good: Reuse single client
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com")
```
For high throughput, configure transport limits:
```python
transport = httpx.AsyncHTTPTransport(retries=3, limits=httpx.Limits(max_connections=100))
client = httpx.AsyncClient(transport=transport)
```
