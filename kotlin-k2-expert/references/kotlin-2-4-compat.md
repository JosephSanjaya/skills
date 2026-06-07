# Kotlin 2.4.0 Compatibility Guide for Plugin Authors

Read when: updating plugins for Kotlin 2.4.0, diagnosing 2.4.0 compilation errors in generated code, or using new 2.4.0 language features.

## Breaking Changes — Full Table

| Component | Change | Mitigation | Impact |
|---|---|---|---|
| Java Nullable Generics | Generic args treated as strict nullable, not flexible | Explicit null-safety casts in generated code | Source Error |
| Inline Visibility | Inline functions blocked from exposing internal types | Raise visibility of synthetic types or drop inline modifier | Source Error |
| Jakarta Nullability | Strict `jakarta.annotation.Nullable`/`@Nonnull` enforcement | Null-check Jakarta-annotated types, use `?.` or `!!` | Source Error |
| Annotation Targets | Default: `param` > `property` > `field` (field only if property N/A) | Specify explicit target (`@field:X`) or `-Xannotation-default-target=first-only` | Binary Change |
| Inner Class Generics | Warns on generic args in wrong qualifier part | Fix qualifier scope: `Outer<Int>.Inner<String>::toString` | Warning |
| Generic Upper Bounds | Restricts args violating bounds dependent on other args | Re-verify generic constraints in generated structures | Error |
| getValue/setValue | getValue: exactly 2 params. setValue: exactly 3 params | Update delegate generation IR templates | Error |
| Java Sealed Exhaustiveness | Non-abstract Java sealed in `when` must be exhaustive or `else` | Append else branches in generated when expressions | Error |
| Enum Constructor OptIn | Error when enum entry calls opt-in constructor | Add `@OptIn` to enum class or entries | Error |
| Function Reference Equality | Refs with differing conversions (SAM/lambda) now unequal on JVM | Don't test reference equality across conversion boundaries | Behavioral |

## Stable Language Features

### Context Parameters
- Type-safe static-dispatch alternative to runtime DI
- Compiler resolves at compile time → eliminates reflection/proxy
- Transforms to implicit bytecode parameters → manual constructor call performance
- 2.4.0 adds **explicit context arguments** for call-site disambiguation

**Plugin impact**: handle `context(LoggingContext, AuthContext)` in FIR resolution. Generated code can use context parameters for zero-overhead DI.

```kotlin
context(logger: Logger)
fun process(data: Data) {
    logger.info("Processing ${data.id}")  // resolved statically
}
```

### Explicit Backing Fields
- `field` keyword inside property declarations
- No separate private backing property generated
- Mapped directly in FIR/IR AST

**Plugin impact**: property-processing plugins must handle `field` declarations. Serialization generators need to detect inline backing fields.

```kotlin
var counter: Int = 0
    get() = field
    set(value) { field = value.coerceAtLeast(0) }
```

### Annotation Target Defaulting
- Priority: `param` → `property` → `field`
- `field` only used when `property` is inapplicable
- Changes annotation placement in class files and metadata

**Plugin impact**: if plugin reads annotations from specific targets, verify target resolution under new defaults. Use `-Xannotation-default-target=first-only` for migration.

## Experimental Features

### Collection Literals
- `-Xcollection-literals` flag
- `[1, 2, 3]` bracket syntax → defaults to `List` if type uninferable
- Custom types: declare `operator fun of(vararg elements: T)` → supports `[a, b]`

### Compile-Time Constants
- Expanded: unsigned ops, `.lowercase()`, `.uppercase()`, `.trim()`, enum `.name`
- Identified by `IntrinsicConstEvaluation` annotation

### Standard Library
- **UUID**: stable common API. Comparison, parsing, `null` returns.
- **Sorted validation**: `.isSorted()`, `.isSortedDescending()`, comparator variants. Short-circuits on first unsorted pair.

## Platform Updates

### JVM
- Java 26 target support
- Annotations in JVM metadata enabled by default (improved external tool compat)

### Native
- Swift packages as dependencies (direct)
- Swift Export → Alpha (concurrency improvements, coroutine flow export)
- CMS GC enabled by default

### Wasm
- Incremental compilation enabled by default
- WebAssembly Component Model support

### JS
- Value class export to JS/TypeScript
- ES2015 syntax in `js()` blocks (arrow functions, spread, classes, generators, `let`/`const`)

## Plugin Code Generation Checklist for 2.4.0

- [ ] getValue delegates have exactly 2 value parameters
- [ ] setValue delegates have exactly 3 value parameters
- [ ] Generated inline functions don't expose internal types
- [ ] Jakarta-annotated types null-checked before non-null assignment
- [ ] Generic arguments satisfy all upper-bound constraints
- [ ] `when` over Java sealed classes includes `else` branch
- [ ] Annotation targets explicitly specified if placement matters
- [ ] Enum constructor opt-in annotations propagated correctly
- [ ] Context parameter handling in overload resolution
- [ ] Explicit backing field declarations handled in property processing
