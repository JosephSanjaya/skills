---
name: data-formats
description: Token density comparison across Markdown, YAML, JSON, XML, and TOON (Token-Oriented Object Notation)
metadata:
  type: reference
---

# Data Format Optimization

## Format Efficiency Comparison

| Format | Token Efficiency | Reasoning Accuracy | Best Use Case |
|--------|-----------------|-------------------|---------------|
| Markdown | Highest (baseline) | High | Nested data, documentation |
| YAML | High (-5% vs MD) | Highest | Symbolic tasks, configs |
| JSON | Medium (-34% vs MD) | High | Standard APIs |
| XML | Lowest (-80% vs MD) | Medium | Legacy systems only |

## Markdown: Most Token-Dense

### Advantages
- 34-38% fewer tokens than JSON
- 80% fewer tokens than XML
- Natural hierarchy through headers
- Excellent for nested data

### Example
```markdown
# Users
## Alice (ID: 1)
- Role: Admin
- Email: alice@example.com

## Bob (ID: 2)
- Role: User
- Email: bob@example.com
```

## YAML: Best for Reasoning

### Advantages
- Visual hierarchy through indentation
- Easier for models to reason through symbolic tasks
- Slightly more tokens than Markdown but higher accuracy

### Example
```yaml
users:
  - id: 1
    name: Alice
    role: admin
  - id: 2
    name: Bob
    role: user
```

## TOON: Token-Oriented Object Notation

### Declare-Schema-Once Principle
- **Problem**: JSON repeats keys for every object
- **Solution**: Declare schema once, then raw data

### Token Savings
| Format | 100k Records | Efficiency |
|--------|-------------|------------|
| JSON (Formatted) | 4.5M tokens | Baseline |
| XML | 5.1M tokens | -14% (worse) |
| TOON | 2.7M tokens | +40% (better) |

### Example
```
users{id,name,role}:
1,Alice,admin
2,Bob,user
3,Charlie,developer
```

### Cost Impact
- **Annual Savings**: ~$2,000 for daily 100k record pipeline
- **Use Case**: High-volume tabular data processing

## Format Selection Guide

1. **Documentation/Nested Data**: Use Markdown
2. **Configuration/Symbolic Tasks**: Use YAML
3. **Standard APIs**: Use JSON (when required)
4. **High-Volume Tabular**: Use TOON
5. **Legacy Systems Only**: Use XML (avoid if possible)

## Anti-Patterns

❌ **Don't**: Use XML for new projects
❌ **Don't**: Use formatted JSON when Markdown works
❌ **Don't**: Repeat schemas in every data object

✅ **Do**: Choose format based on token efficiency
✅ **Do**: Use TOON for large datasets
✅ **Do**: Prefer Markdown for general-purpose data
