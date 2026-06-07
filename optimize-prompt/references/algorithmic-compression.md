---
name: algorithmic-compression
description: Secondary model prompt compression (LLMLingua), Dynamic Memory Sparsification (DMS), and AST-aware Claw Compactor
metadata:
  type: reference
---

# Algorithmic Compression Techniques

## Overview
Use secondary models or structural analyzers to prune prompts before sending to primary LLM.

## LLMLingua (Microsoft)

### Mechanism
- Uses small language model (SLM) to calculate perplexity scores
- Removes low-perplexity (highly predictable) tokens
- Examples: "the", "please", "a", "an"

### Performance
- **Compression Ratio**: Up to 20x
- **Semantic Preservation**: High similarity maintained
- **Use Case**: Long documents, verbose prompts

### Example
**Original** (100 tokens):
```
Please create a new function that will take a user object as input and 
return a formatted string containing the user's full name and email address. 
The function should handle cases where the user object might be null or undefined.
```

**Compressed** (35 tokens):
```
Create function: user object → formatted string (name, email). Handle null/undefined.
```

**Reduction**: 65%

### Implementation
```python
from llmlingua import PromptCompressor

compressor = PromptCompressor()
compressed = compressor.compress_prompt(
    original_prompt,
    rate=0.5,  # Target 50% compression
    force_tokens=['\n', '.']  # Preserve structure
)
```

## Dynamic Memory Sparsification (DMS)

### Mechanism
- Identifies non-essential tokens in KV cache during inference
- Deletes them from active memory
- Hardware-level optimization

### Performance
- **Memory Reduction**: Up to 8x
- **Accuracy**: Actually improves on math/coding tasks
- **Power**: Reduced consumption
- **Reasoning**: More concurrent threads possible

### Benefits
- Allows more reasoning exploration
- Reduces inference cost
- Improves response quality

### Use Case
- Long-running reasoning chains
- Complex problem-solving
- Resource-constrained environments

## Claw Compactor

### 14-Stage Fusion Pipeline

1. **Whitespace Normalization**: Remove redundant spaces
2. **Comment Stripping**: Remove non-essential comments
3. **Variable Renaming**: Shorten identifiers
4. **Neurosyntax (AST-aware)**: Preserve logical structure
5. **Control Flow Preservation**: Maintain program logic
6. **Identifier Mapping**: Track renames for reversibility
7. **String Literal Compression**: Deduplicate strings
8. **Import Optimization**: Consolidate imports
9. **Dead Code Elimination**: Remove unused code
10. **Expression Simplification**: Reduce complex expressions
11. **Pattern Recognition**: Identify common patterns
12. **Semantic Chunking**: Group related code
13. **Metadata Preservation**: Keep critical annotations
14. **Reversible Encoding**: Enable decompression

### Key Innovation: Neurosyntax
- Uses tree-sitter for Abstract Syntax Tree analysis
- Ensures logical control flows remain intact
- Prevents hallucination from dropping critical variable names

### Performance
- **Compression**: Up to 95% reduction
- **Reversibility**: Zero information loss
- **Inference Cost**: Zero (pre-processing only)

### Example
**Original** (500 tokens):
```typescript
// User authentication service
export class UserAuthenticationService {
  private readonly databaseConnection: DatabaseConnection;
  
  constructor(databaseConnection: DatabaseConnection) {
    this.databaseConnection = databaseConnection;
  }
  
  public async authenticateUser(
    emailAddress: string,
    password: string
  ): Promise<AuthenticationResult> {
    // Validate input parameters
    if (!emailAddress || !password) {
      throw new Error('Email and password are required');
    }
    
    // Query database for user
    const user = await this.databaseConnection.query(
      'SELECT * FROM users WHERE email = ?',
      [emailAddress]
    );
    
    // Check if user exists
    if (!user) {
      return { success: false, error: 'User not found' };
    }
    
    // Verify password
    const isValid = await this.verifyPassword(password, user.passwordHash);
    
    return { success: isValid, user: isValid ? user : null };
  }
}
```

**Compressed** (75 tokens):
```typescript
class A{c:B;constructor(c:B){this.c=c}async a(e:string,p:string):Promise<C>{if(!e||!p)throw Error('Required');const u=await this.c.q('SELECT * FROM users WHERE email=?',[e]);if(!u)return{s:false,e:'Not found'};const v=await this.v(p,u.h);return{s:v,u:v?u:null}}}
```

**Reduction**: 85%

### Implementation
```bash
# Install
npm install -g claw-compactor

# Compress
claw-compress --input src/ --output compressed/ --rate 0.9

# Decompress (if needed)
claw-decompress --input compressed/ --output restored/
```

## Comparison Matrix

| Technique | Compression | Reversible | Accuracy | Use Case |
|-----------|-------------|------------|----------|----------|
| LLMLingua | 5-20x | No | High | Verbose prompts |
| DMS | 8x (memory) | N/A | Improved | Inference optimization |
| Claw Compactor | Up to 95% | Yes | Perfect | Code compression |

## Selection Guide

### Use LLMLingua When:
- Compressing natural language prompts
- One-way compression acceptable
- Need quick implementation

### Use DMS When:
- Optimizing inference performance
- Working with long reasoning chains
- Hardware constraints exist

### Use Claw Compactor When:
- Compressing code for context
- Need reversibility
- AST preservation critical
- Maximum compression required

## Best Practices

1. **Test Compression**: Verify output quality after compression
2. **Preserve Critical Tokens**: Force-keep important keywords
3. **Monitor Accuracy**: Track semantic similarity metrics
4. **Combine Techniques**: Use multiple methods for maximum effect
5. **Profile Performance**: Measure actual token savings

## Anti-Patterns

❌ **Don't**: Compress without testing output quality
❌ **Don't**: Remove all comments (some are critical)
❌ **Don't**: Over-compress at expense of accuracy
❌ **Don't**: Use same compression rate for all content

✅ **Do**: Adjust compression based on content type
✅ **Do**: Preserve structural elements
✅ **Do**: Test with representative samples
✅ **Do**: Monitor semantic preservation
