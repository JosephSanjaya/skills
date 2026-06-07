---
name: symbolic-languages
description: Mathematical operators, LTL (Less-Token-Language), Hieratic shorthand, Caveman protocol, and Wenyan-lang mode for token reduction
metadata:
  type: reference
---

# Symbolic Instruction Languages

## Overview
Replace verbose natural language with mathematical operators and symbolic logic for extreme token reduction.

## MetaGlyph

### Concept
Use mathematical operators with high semantic stability

### Common Symbols
- `∈` (membership): "X is part of Y"
- `∩` (intersection): "Common elements between X and Y"
- `∪` (union): "Combine X and Y"
- `→` (implication): "If X then Y"
- `∀` (for all): "For every X"
- `∃` (exists): "There exists X"

### Example
**Natural Language** (45 tokens):
```
Create a React component that accepts a user object as a prop and displays the user's name and email address
```

**MetaGlyph** (12 tokens):
```
Component ∈ React, props ∋ user{name,email} → render(name,email)
```

**Reduction**: 73%

## Less-Token-Language (LTL)

### Grammar
- `%` Persona/Role
- `!` Action/Command
- `#` Constraint/Requirement
- `@` Context/Scope
- `>` Output Format

### Example
**Natural Language** (193 tokens):
```
You are a senior React developer. Create a new component for displaying user profiles. 
The component should be written in TypeScript, follow accessibility best practices, 
include comprehensive tests, and provide JSDoc documentation for all props and methods.
```

**LTL** (11 tokens):
```
%React.Senior @component #ts #a11y #test >code+jsdoc
```

**Reduction**: 94.3%

### LTL Patterns
```
# Role + Action + Constraints
%Backend.Expert !api #rest #auth #validation

# Context + Output
@database !optimize >query+explain

# Multi-constraint
%Frontend !component #react #ts #styled #test #a11y
```

## Hieratic Shorthand

### Block Structure
```
@ROLE: [persona]
@TASK: [objective]
@CONSTRAINTS: [requirements]
@EXAMPLES: [samples]
@OUTPUT: [format]
```

### Token Savings
- **Reduction**: ~66% vs natural language
- **Benefit**: Clear semantic markers for attention mechanism

### Example
```
@ROLE: Senior TypeScript Developer
@TASK: Refactor authentication module
@CONSTRAINTS: Maintain backward compatibility, Add unit tests
@OUTPUT: Code with inline comments
```

vs Natural Language (3x longer):
```
I need you to act as a senior TypeScript developer. Your task is to refactor 
the authentication module. Please ensure that you maintain backward compatibility 
with the existing API and add comprehensive unit tests. The output should include 
the refactored code with inline comments explaining the changes.
```

## Caveman Protocol

### Purpose
Eliminate conversational overhead in outputs

### Rules
❌ Forbidden:
- "Certainly!"
- "I hope this helps!"
- "Let me know if you need anything else"
- Apologies
- Pleasantries
- Verbose acknowledgments

✅ Required:
- Raw data only
- Direct code
- Minimal explanations
- Technical details only

### Token Savings
- **Output Reduction**: Up to 65%
- **Use Case**: Cost-sensitive, high-volume deployments

### Example
**Standard Output** (120 tokens):
```
Certainly! I'd be happy to help you with that. Here's the refactored function 
that should address your requirements. I've made sure to include error handling 
and added comments to explain the logic. Let me know if you need any clarification!

[code]

I hope this helps! Feel free to ask if you have any questions.
```

**Caveman Output** (30 tokens):
```
[code]

Error handling added. Comments inline.
```

## Wenyan-lang Mode

### Concept
Use Classical Chinese for maximum token density

### Characteristics
- Inherently dense language
- Fewer characters per concept
- Unparalleled token efficiency

### Token Savings
- **Reduction**: 70-85% vs English
- **Use Case**: Extreme cost optimization for Chinese-capable models

### Example
**English** (25 tokens):
```
Create a function that validates email addresses using regex
```

**Wenyan** (~8 tokens):
```
造函式驗郵址以正則
```

**Reduction**: 68%

## Implementation Guidelines

### When to Use Symbolic Languages

1. **High-Volume Operations**: Repeated similar requests
2. **Cost-Critical**: Budget constraints require maximum efficiency
3. **Structured Tasks**: Well-defined, repeatable workflows
4. **Internal Tools**: Not user-facing interactions

### When to Avoid

1. **Exploratory Work**: Unclear requirements
2. **User-Facing**: Customer interactions
3. **Complex Reasoning**: Nuanced decision-making
4. **Collaborative**: Human readability matters

### Hybrid Approach

Combine natural language for context with symbolic for instructions:

```
Context: Working on user authentication system

Instructions: %Backend.Senior !implement #jwt #refresh #secure @auth-service >code+tests
```

## Selection Matrix

| Need | Recommended Language | Reduction |
|------|---------------------|-----------|
| Maximum density | Wenyan-lang | 70-85% |
| Structured prompts | LTL | 90-95% |
| Mathematical logic | MetaGlyph | 70-80% |
| Clear semantics | Hieratic | 60-70% |
| Output efficiency | Caveman | 50-65% |
