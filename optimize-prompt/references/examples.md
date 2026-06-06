---
name: examples
description: Practical examples of prompt structuring, structured outputs (Pydantic/Zod/CFG), cache preservation, and Claude Code operational workflows
metadata:
  type: reference
---

# Practical Optimization Patterns & Configurations

This reference contains concrete, copy-pasteable examples of high-signal prompt designs, API configurations, and agentic workflows.

---

## 1. Prompt Structuring: Good vs. Bad Patterns

### Bad Pattern (Polite, Persona-led, Wall-of-Text, Cache-unfriendly)
```markdown
Please act as an expert junior software engineer developer. I would like you to write a python test.
Wait, if you don't mind, first can you write down the setup?
Here is the file we are testing today:
{dynamic_source_code_input}
Make sure you do not use any third-party dependencies besides pytest. Thank you!
```
*   *Problems*: Conversational fillers; theatrical role placebo; dynamic content prefix invalidates caching; negative constraint triggers attention sink.

### Good Pattern (Tense, XML Delineated, Cache-Compliant, Prism-Style)
```markdown
<instructions>
Write a Python unit test using pytest. Do not import external packages.
Place static fixtures first.
</instructions>

<context>
Target file for test generation:
</context>

<source_code>
{dynamic_source_code_input}
</source_code>

<constraints>
- Output must be composed exclusively of valid Python code.
- Wrap the output in a single markdown block starting with ```python.
</constraints>
```
*   *Strengths*: XML structures the context; dynamic code placed at the absolute end (append-only); formatting constraints suffix-loaded (recency bias).

---

## 2. Claude Code Workflows (Before/After)

### Bug Fix
*   **Bad (Vague exploration)**: `fix the bug in the auth module`
*   **Good (Targeted)**:
    ```xml
    <task>
      <goal>Fix JWT token expiry — tokens rejected 30s before actual expiry</goal>
      <context>
        @src/auth/middleware.ts:45
        Error: TokenExpiredError: jwt expired
          at /src/auth/middleware.ts:45:18
        Token exp: 1747314000
        Server time at rejection: 1747313970
      </context>
      <constraints>No new dependencies. Must pass: npm test -- auth.test.ts</constraints>
      <verify>npm test -- auth.test.ts</verify>
    </task>
    ```

### Feature Request
*   **Bad (Unbounded)**: `implement the entire OAuth2 flow with refresh tokens, PKCE, and session management`
*   **Good (Incremental)**:
    ```
    Plan Mode: OAuth2 authorization code flow with PKCE
    Scope: @src/auth/ only
    Constraints: use existing `jose` library, no new deps
    Output: written plan only, no code
    ```

### Debugging & Refactoring
*   **Bad (Narrative)**: `The tests are failing because something is wrong with the database connection pool.`
*   **Good (Raw)**:
    ```
    !npm test 2>&1 | tail -30
    @src/db/pool.ts:12
    ```

---

## 3. Session Reset & Subagents

### Post-Subtask Reset Pattern
```
/clear
```
New session prompt:
```
State: JWT expiry fix complete (src/auth/middleware.ts). Tests passing.
Next: Add refresh token endpoint
@src/auth/routes.ts
@src/auth/middleware.ts (for reference)
Constraints: POST /auth/refresh, 7-day TTL, store in httpOnly cookie
Verify: npm test -- refresh.test.ts
```

### Subagent Delegation
```
Delegate to Explorer subagent:
Find all files importing deprecated `TokenV1` class.
Return: file:line list only. No suggestions. No analysis.
Scope: src/ only
```

---

## 4. Structured Outputs: Outlines, Pydantic AI, Zod

### Outlines (Python - CFG & JSON)
```python
from pydantic import BaseModel
from outlines.types import CFG
import outlines

# JSON Schema Constrained Generation
class ModelOutput(BaseModel):
    name: str
    confidence: float

model = outlines.from_transformers(llm_model, tokenizer)
generator = model(prompt, output_type=ModelOutput)

# CFG Lark Grammars
grammar = """
?start: answer
answer: "yes" | "no"
"""
cfg_generator = model(prompt, CFG(grammar))
```

### Pydantic AI (Python - Agent structured output)
```python
from pydantic import BaseModel
from pydantic_ai import Agent

class CityInfo(BaseModel):
    city: str
    country: str

agent = Agent("google:gemini-3.5-flash", output_type=CityInfo)
result = agent.run_sync("Where is the Eiffel Tower?")
print(result.output.city)  # 'Paris'
```

### Zod (TypeScript - Structured schema validation)
```typescript
import { z } from "zod";

const APIResponse = z.object({
  status: z.enum(["success", "error"]),
  data: z.object({
    id: z.string(),
    value: z.number().positive(),
  }),
});
```

---

## 5. Infrastructure Serving Configurations

### vLLM Prefix Caching
*   **CLI Setup**:
    ```bash
    vllm serve meta-llama/Llama-3-8B-Instruct --enable-prefix-caching
    ```
*   **Python SDK Setup**:
    ```python
    from vllm import LLM
    llm = LLM(model="meta-llama/Llama-3-8B-Instruct", enable_prefix_caching=True)
    ```

### LMCache (Distributed KV Cache sharing)
*   **vLLM Command Line integration**:
    ```bash
    PYTHONHASHSEED=0 \
    LMCACHE_CONFIG_FILE=lmcache_config.yaml \
    vllm serve meta-llama/Llama-3-8B-Instruct \
    --gpu-memory-utilization 0.8 \
    --kv-transfer-config '{"kv_connector":"LMCacheConnectorV1", "kv_role":"kv_both"}'
    ```
