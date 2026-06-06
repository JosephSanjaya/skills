# DDD Bounded Context Patterns

## Subdomain Classification

| Type | Description | Action |
|------|-------------|--------|
| Core | Competitive advantage, custom high-investment modeling | Prioritize deep recovery |
| Supporting | Necessary but non-differentiating (e.g. custom invoicing) | Standard recovery |
| Generic | Solves standard industry problem | Check for off-the-shelf replacement |

## Context Mapping Patterns

| Pattern | Description | Risk |
|---------|-------------|------|
| **Shared Kernel** | Shared library/schema accessed by multiple contexts | Bidirectional coupling, changes break both |
| **Customer-Supplier** | Upstream provides data, downstream consumes | Downstream depends on upstream schedule |
| **Conformist** | Downstream accepts upstream model without translation | Pollutes downstream domain with foreign concepts |
| **Anti-Corruption Layer (ACL)** | Adapter at downstream boundary translates foreign payloads | Translation cost, but shields domain purity |
| **Open Host Service (OHS) / Published Language (PL)** | Stable documented public API (REST/message schema) | Must maintain backwards compat |

## Same Entity, Different Contexts

Example — `Order` in e-commerce:
- **Order Context**: billing details, customer data, transactional state
- **Shipping Context**: package dimensions array, destination address only

Look for same class name with different fields/methods across packages = bounded context boundary.

## JPMS Enforcement

Java Platform Module System maps logical bounded contexts to physical compile-time modules:
- `module-info.java` `exports` = public API surface
- Internal entities = encapsulated, other contexts can't instantiate directly
- `ServiceLoader` = runtime DI without circular compile-time deps

## Recovery Steps

1. List all top-level packages/modules
2. Group by business noun (Order, User, Payment, Shipping)
3. Find classes with same name in different packages → context boundary
4. Find ACL adapters: classes named `*Translator`, `*Adapter`, `*Mapper` at package boundaries
5. Find Published Language: `@RestController`, protobuf schemas, message contracts
6. Map event bus / shared kernel: classes imported by 3+ modules
