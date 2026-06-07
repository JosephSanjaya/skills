---
name: caching-strategies
description: Ephemeral prefix caching, semantic caching with embeddings, VectorQ adaptive thresholds, and hybrid multi-layer caching
metadata:
  type: reference
---

# Caching Strategies for Token Optimization

## Overview
Eliminate redundant API calls and token processing through intelligent caching.

## Provider Prefix Caching

### Mechanism
- Cache exact token prefix sequences
- Reuse cached prefix for subsequent requests
- Pay reduced rate for cache hits

### Anthropic Pricing
- **Cache Write**: $0.30 per 1M tokens (first time)
- **Cache Read**: $0.03 per 1M tokens (subsequent)
- **Savings**: 90% on cached portions

### Requirements
- Exact prefix match (byte-for-byte)
- Minimum cache size: 1,024 tokens
- Cache TTL: 5 minutes (Anthropic)

### Example
**Request 1** (20,000 tokens):
```
[System Prompt: 5,000 tokens]
[Project Context: 10,000 tokens]
[User Query: 5,000 tokens]

Cost: 20,000 × $0.003 = $0.06
Cache: First 15,000 tokens
```

**Request 2** (20,000 tokens, same prefix):
```
[System Prompt: 5,000 tokens] ← Cached
[Project Context: 10,000 tokens] ← Cached
[User Query: 5,000 tokens] ← New

Cost: (15,000 × $0.0003) + (5,000 × $0.003) = $0.0195
Savings: 67.5%
```

### Optimization Strategies

1. **Stable Prefix**: Keep system prompt and project context stable
2. **Append-Only**: Add new messages at end, don't modify history
3. **Batch Changes**: Group related changes to maximize cache hits
4. **Monitor TTL**: Submit requests within cache window

### Implementation
```python
from anthropic import Anthropic

client = Anthropic()

# First request - writes to cache
response1 = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "You are an expert developer...",
            "cache_control": {"type": "ephemeral"}
        }
    ],
    messages=[{"role": "user", "content": "Task 1"}]
)

# Second request - reads from cache
response2 = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "You are an expert developer...",  # Same prefix
            "cache_control": {"type": "ephemeral"}
        }
    ],
    messages=[{"role": "user", "content": "Task 2"}]
)
```

## Semantic Caching

### Mechanism
- Use vector embeddings to identify similar queries
- Return cached response for semantically identical requests
- No model call required on cache hit

### Performance
- **Hit Rate**: 60-80% in production
- **Latency**: 27ms (cached) vs 7s (uncached)
- **Cost**: 100% savings on hits (no API call)

### Example Queries (Semantic Match)
```
Query 1: "How do I authenticate users with JWT?"
Query 2: "What's the process for JWT-based user authentication?"
Query 3: "Explain JWT authentication for users"

→ All three hit same cache entry
```

### Implementation
```python
from semantic_cache import SemanticCache

cache = SemanticCache(
    embedding_model="text-embedding-3-small",
    similarity_threshold=0.95
)

def query_llm(prompt):
    # Check cache first
    cached = cache.get(prompt)
    if cached:
        return cached
    
    # Cache miss - call LLM
    response = llm.generate(prompt)
    
    # Store in cache
    cache.set(prompt, response)
    
    return response
```

### Configuration
```yaml
semantic_cache:
  embedding_model: text-embedding-3-small
  similarity_threshold: 0.95  # 95% similarity required
  ttl: 3600  # 1 hour
  max_entries: 10000
  eviction_policy: LRU
```

## VectorQ Adaptive Cache

### Mechanism
- Learns optimal cache hit/miss thresholds
- Adapts to query patterns over time
- Maximizes throughput while minimizing costs

### Features
- **Adaptive Thresholds**: Adjusts similarity requirements
- **Pattern Learning**: Identifies common query clusters
- **Cost Optimization**: Balances cache size vs hit rate

### Performance
- **Hit Rate**: 70-85% (adaptive)
- **Cost Reduction**: 60-75% vs no caching
- **Latency**: 30-50ms (cached)

### Implementation
```python
from vectorq import AdaptiveCache

cache = AdaptiveCache(
    initial_threshold=0.90,
    learning_rate=0.01,
    optimization_target='cost'  # or 'latency' or 'balanced'
)

# Cache learns from usage patterns
for query in queries:
    result = cache.get_or_compute(query, lambda q: llm.generate(q))
    cache.update_metrics(query, result)

# Cache automatically adjusts thresholds
cache.optimize()
```

## Comparison Matrix

| Feature | Prefix Caching | Semantic Caching | VectorQ Adaptive |
|---------|---------------|------------------|------------------|
| Match Type | Exact prefix | Semantic meaning | Learned regions |
| Hit Rate | 30-50% | 60-80% | 70-85% |
| Cost Savings | 50-90% per hit | 100% per hit | Optimized balance |
| Latency | Moderate | Instant (27ms) | Optimized (30-50ms) |
| Setup | Simple | Medium | Complex |

## Hybrid Caching Strategy

### Layer 1: Semantic Cache
```
User Query → Semantic Cache
  ↓ (miss)
Layer 2: Prefix Cache
  ↓ (miss)
LLM API Call
```

### Benefits
- **Maximum Hit Rate**: Combine both approaches
- **Cost Optimization**: Semantic cache eliminates most calls
- **Fallback**: Prefix cache reduces cost of misses

### Implementation
```python
def hybrid_query(prompt, context):
    # Layer 1: Semantic cache
    semantic_hit = semantic_cache.get(prompt)
    if semantic_hit:
        return semantic_hit
    
    # Layer 2: Prefix cache (via API)
    full_prompt = f"{context}\n\n{prompt}"
    response = llm.generate(
        full_prompt,
        cache_control={"type": "ephemeral"}
    )
    
    # Store in semantic cache
    semantic_cache.set(prompt, response)
    
    return response
```

## Best Practices

### Prefix Caching
1. **Stable Prefixes**: Keep system prompts consistent
2. **Append-Only**: Don't modify cached portions
3. **Monitor TTL**: Stay within cache window (5 min)
4. **Batch Requests**: Group related queries

### Semantic Caching
1. **Tune Threshold**: Balance hit rate vs accuracy
2. **Monitor Quality**: Verify cached responses are appropriate
3. **Invalidate Stale**: Clear cache when data changes
4. **Cluster Queries**: Group similar query patterns

### Hybrid Strategy
1. **Layer Appropriately**: Semantic first, prefix second
2. **Share Context**: Use same context for prefix caching
3. **Monitor Metrics**: Track hit rates per layer
4. **Optimize Costs**: Adjust thresholds based on usage

## Anti-Patterns

❌ **Don't**: Modify cached prefixes frequently
❌ **Don't**: Set semantic threshold too low (false hits)
❌ **Don't**: Cache without monitoring quality
❌ **Don't**: Ignore cache TTL windows

✅ **Do**: Keep prefixes stable
✅ **Do**: Tune semantic thresholds carefully
✅ **Do**: Monitor cache hit rates
✅ **Do**: Invalidate stale entries

## Cost Analysis Example

### Scenario: 10,000 queries/day

**No Caching**:
- Cost: 10,000 × $0.06 = $600/day
- Annual: $219,000

**Prefix Caching (40% hit rate)**:
- Hits: 4,000 × $0.006 = $24
- Misses: 6,000 × $0.06 = $360
- Daily: $384
- Annual: $140,160
- **Savings**: $78,840 (36%)

**Semantic Caching (70% hit rate)**:
- Hits: 7,000 × $0 = $0
- Misses: 3,000 × $0.06 = $180
- Daily: $180
- Annual: $65,700
- **Savings**: $153,300 (70%)

**Hybrid (80% semantic + 50% prefix on misses)**:
- Semantic hits: 8,000 × $0 = $0
- Prefix hits: 1,000 × $0.006 = $6
- Misses: 1,000 × $0.06 = $60
- Daily: $66
- Annual: $24,090
- **Savings**: $194,910 (89%)
