---
name: architectural-patterns
description: Core architectural patterns for token efficiency including AtomicRAG, Spine Architecture, Subagent Forking, and Modular Context Loading
metadata:
  type: reference
---

# Architectural Patterns for Token Efficiency

## AtomicRAG

### Concept
Atomize corpus into minimal "knowledge atoms" linked via entities and relationships

### Architecture
```
Document → Knowledge Atoms → Entity Graph → Filtered Context
```

### Process
1. **Atomization**: Break documents into minimal semantic units
2. **Entity Linking**: Connect atoms via shared entities
3. **Co-occurrence**: Track relationship strength
4. **Deduplication**: Merge redundant atoms
5. **Retrieval**: Fetch only relevant atoms

### Benefits
- **Precision**: No bloated passages
- **Efficiency**: Minimal context per query
- **Scalability**: Large corpora without context saturation

### Token Savings
- **Traditional RAG**: 2,000-5,000 tokens per retrieval
- **AtomicRAG**: 300-800 tokens per retrieval
- **Reduction**: 70-85%

### Example
**Traditional RAG Chunk** (500 tokens):
```
The authentication system uses JWT tokens for user sessions. When a user logs in,
the system validates credentials against the database, generates a JWT token with
user claims, and returns it to the client. The token expires after 24 hours and
must be refreshed. The system also supports OAuth2 for third-party authentication
and implements rate limiting to prevent brute force attacks. Password hashing uses
bcrypt with a cost factor of 12. The database stores user credentials in the users
table with columns for email, password_hash, created_at, and last_login...
```

**AtomicRAG Atoms** (80 tokens):
```
Atom 1: Auth uses JWT tokens
Atom 2: Token expiry: 24 hours
Atom 3: Password hash: bcrypt (cost=12)
Atom 4: OAuth2 supported
Atom 5: Rate limiting enabled
```

### Implementation
```python
from atomic_rag import AtomicRAG

rag = AtomicRAG()
rag.ingest_documents(documents)
atoms = rag.retrieve(query, max_atoms=5)
context = rag.build_context(atoms)
```

## Spine Architecture

### Concept
Mirror datacenter networking: high-capacity spine + specialized leaf nodes

### Structure
```
┌─────────────────┐
│  Spine (Core)   │  ← High-level architectural plan
│  State Manager  │
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┐
    │         │        │        │
┌───▼───┐ ┌──▼───┐ ┌──▼───┐ ┌──▼───┐
│Leaf 1 │ │Leaf 2│ │Leaf 3│ │Leaf 4│  ← Specialized sub-agents
│Auth   │ │API   │ │DB    │ │UI    │
└───────┘ └──────┘ └──────┘ └──────┘
```

### Benefits
- **Isolation**: Each leaf only sees relevant context
- **Scalability**: Add leaves without affecting others
- **Efficiency**: No intra-job contention for context window

### Token Savings
- **Monolithic**: 50,000+ tokens (all context)
- **Spine**: 10,000 tokens (spine + active leaf)
- **Reduction**: 80%

### Implementation Pattern

**Spine Agent** (maintains state):
```yaml
role: Architectural Coordinator
context:
  - Project structure
  - Module boundaries
  - Inter-module contracts
responsibilities:
  - Route tasks to leaf agents
  - Maintain global state
  - Coordinate cross-module changes
```

**Leaf Agent** (specialized):
```yaml
role: Authentication Module Expert
context:
  - Auth module code only
  - Auth-related docs
  - Security patterns
responsibilities:
  - Implement auth features
  - Fix auth bugs
  - Optimize auth performance
```

### Routing Logic
```python
def route_task(task):
    if 'auth' in task.keywords:
        return leaf_agents['auth']
    elif 'database' in task.keywords:
        return leaf_agents['database']
    elif 'ui' in task.keywords:
        return leaf_agents['ui']
    else:
        return spine_agent
```

## Subagent Forking

### Problem
Spawning subagent creates fresh session → rewrites prompt cache → expensive

### Solution
Fork session by copying message history to divergence point

### Mechanism
```
Parent Session:
[Msg 1] [Msg 2] [Msg 3] [Msg 4] [Msg 5]
                    ↓
                  Fork here
                    ↓
Child Session:
[Msg 1] [Msg 2] [Msg 3] [New Task]
         ↑
    Shared cache (90% cheaper)
```

### Cost Savings
- **Cache Write**: $0.30 per 1M tokens
- **Cache Read**: $0.03 per 1M tokens
- **Savings**: 90% on shared context

### Example
**Without Forking**:
- Parent: 20,000 tokens cached
- Child: 20,000 tokens re-cached
- Cost: 2 × cache write = $0.012

**With Forking**:
- Parent: 20,000 tokens cached
- Child: 20,000 tokens read from cache
- Cost: 1 × cache write + 1 × cache read = $0.0066
- **Savings**: 45%

### Implementation
```typescript
// Fork session at message 3
const childSession = parentSession.fork({
  fromMessage: 3,
  newPrompt: "Implement authentication module"
});

// Child inherits parent's cache up to message 3
// Only pays cache-read pricing for shared context
```

## Modular Context Loading

### Concept
Load only relevant code modules based on task

### Pattern
```
Task: "Fix login bug"
  ↓
Analyze keywords: login, auth, bug
  ↓
Load modules:
  ✓ auth/login.ts
  ✓ auth/session.ts
  ✓ tests/auth.test.ts
  ✗ payment/checkout.ts (irrelevant)
  ✗ admin/dashboard.ts (irrelevant)
```

### Benefits
- **Precision**: Only relevant code in context
- **Speed**: Faster analysis with less noise
- **Cost**: Fewer tokens per task

### Token Savings
- **Full Codebase**: 100,000+ tokens
- **Modular**: 5,000-10,000 tokens
- **Reduction**: 90-95%

### Implementation
```python
def load_relevant_modules(task):
    keywords = extract_keywords(task)
    modules = []
    
    for module in codebase.modules:
        if module.matches_keywords(keywords):
            modules.append(module)
    
    return modules

# Usage
task = "Fix authentication timeout issue"
modules = load_relevant_modules(task)
context = build_context(modules)
```

## Comparison Matrix

| Pattern | Token Reduction | Complexity | Best For |
|---------|----------------|------------|----------|
| AtomicRAG | 70-85% | Medium | Knowledge retrieval |
| Spine Architecture | 80% | High | Large codebases |
| Subagent Forking | 45% (cost) | Low | Parallel tasks |
| Modular Loading | 90-95% | Low | Focused tasks |

## Selection Guide

### Use AtomicRAG When:
- Working with large documentation
- Need precise information retrieval
- Context saturation is a problem

### Use Spine Architecture When:
- Managing large, modular codebases
- Multiple specialized domains
- Team collaboration required

### Use Subagent Forking When:
- Spawning multiple related tasks
- Shared context across tasks
- Cost optimization critical

### Use Modular Loading When:
- Task scope is well-defined
- Codebase has clear module boundaries
- Quick iteration needed

## Best Practices

1. **Start Simple**: Begin with modular loading
2. **Scale Up**: Add spine architecture for large projects
3. **Optimize Retrieval**: Implement AtomicRAG for docs
4. **Reduce Costs**: Use subagent forking for parallel work
5. **Monitor Performance**: Track token usage per pattern

## Anti-Patterns

❌ **Don't**: Load entire codebase for every task
❌ **Don't**: Create subagents without forking
❌ **Don't**: Use monolithic context for modular projects
❌ **Don't**: Retrieve large RAG chunks

✅ **Do**: Load only relevant modules
✅ **Do**: Fork sessions for related tasks
✅ **Do**: Use spine architecture for large projects
✅ **Do**: Atomize knowledge for retrieval
