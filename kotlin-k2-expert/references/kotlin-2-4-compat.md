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

## Kotlin Compiler API Evolution (1.7.21 to 2.4.0)

For compiler plugin authors, the compiler internals have undergone significant refactoring. Below is a detailed mapping of signature and API evolution across versions.

### 1. Version Comparison Matrix

| Component / Class | Kotlin 1.7.21 / K1 | Kotlin 2.0.x | Kotlin 2.1.x / 2.2.x / 2.3.x / 2.4.0 |
|---|---|---|---|
| **Plugin Registration** | `ComponentRegistrar` | `CompilerPluginRegistrar` | `CompilerPluginRegistrar` (requires `@OptIn(ExperimentalCompilerApi::class)`) |
| **`FirDeclarationGenerationExtension`** | `generateClassLikeDeclaration(ClassId)` | `generateTopLevelClassLikeDeclaration(ClassId)` | `generateTopLevelClassLikeDeclaration(ClassId)` |
| **Generation Context** | `MemberGenerationContext` (non-null) | `DeclarationGenerationContext.Member` (aliased to `MemberGenerationContext`) | `DeclarationGenerationContext.Member` (aliased to `MemberGenerationContext`) |
| **`getCallableNamesForClass`** | `getCallableNamesForClass(FirClassSymbol<*>)` | `getCallableNamesForClass(FirClassSymbol<*>, MemberGenerationContext)` | `getCallableNamesForClass(classSymbol, MemberGenerationContext)` |
| **`generateFunctions` context** | `MemberGenerationContext` (non-null) | `MemberGenerationContext?` (nullable) | `MemberGenerationContext?` (nullable) |
| **`generateConstructors` context** | `MemberGenerationContext` (non-null) | `MemberGenerationContext` (non-null) | `MemberGenerationContext` (non-null) |
| **`IrGenerationExtension.getPlatformIntrinsicExtension`** | N/A | `getPlatformIntrinsicExtension(BackendContext)` | `getPlatformIntrinsicExtension(LoweringContext)` (since 2.1.21) |
| **Type Nullability Representation** | `ConeNullability` | `ConeNullability` | **Removed**. Replaced with `isMarkedNullable: Boolean` on `ConeKotlinType`. |
| **`FirResolvedTypeRef` Builder** | `type = myConeType` | `type = myConeType` | `coneType = myConeType` (renamed in 2.1+) |

### 2. Nullability Migration & `ConeNullability` Removal

In Kotlin 2.0.x and older, type nullability in FIR was represented by the `ConeNullability` enum. In Kotlin 2.1+ (including 2.3.x and 2.4.0), it has been completely removed.

- **To query nullability**:
  - *2.0.x*: Use `type.nullability.isNullable`
  - *2.1+ / 2.4.0*: Use `type.isMarkedNullable` (or `type.isNullableType(session)`)
- **To construct a nullable/not-null type**:
  - *2.0.x*: `type.withNullability(ConeNullability.NULLABLE, session.typeContext)`
  - *2.1+ / 2.4.0*: `type.withNullability(true, session.typeContext)` (uses `Boolean` instead of enum)

### 3. `FirResolvedTypeRef` Property Rename (`type` -> `coneType`)

The builder DSL for constructing type references has renamed its primary type field:
- **2.0.x**:
  ```kotlin
  buildResolvedTypeRef {
      type = myConeType
  }
  ```
- **2.1+ / 2.4.0**:
  ```kotlin
  buildResolvedTypeRef {
      coneType = myConeType
  }
  ```
Using `type` in 2.4.0 will cause an unresolved reference compile-time error.

### 4. Resolving `session.typeContext` Unresolved References

Because `typeContext` is declared as a top-level extension property on `FirSession` inside the `org.jetbrains.kotlin.fir.types` package, it **must** be explicitly imported:
```kotlin
import org.jetbrains.kotlin.fir.types.typeContext
```
Without this import, calling `session.typeContext` will result in a compiler/IDE error.

### 5. Annotation Querying & Deprecations Handling

Querying annotations and managing deprecations on generated declarations has version-specific nuances between `2.0.x` and `2.4.0`.

#### A. Annotation Querying
To check if a declaration has an annotation, or to read its arguments, utilize the extension functions in `org.jetbrains.kotlin.fir.declarations`.

| Task / Operation | Kotlin 2.0.x | Kotlin 2.1.x / 2.2.x / 2.3.x / 2.4.0 | Multi-Version Compatible Code |
|---|---|---|---|
| **Check for Annotation** | `symbol.hasAnnotation(classId, session)` | `symbol.hasAnnotation(classId, session)` | `symbol.hasAnnotation(classId, session)` |
| **Get Annotation with Resolved Arguments** | `symbol.resolvedAnnotationsWithArguments.getAnnotationByClassId(classId, session)` | `symbol.getAnnotationWithResolvedArgumentsByClassId(classId, session)` | `symbol.resolvedAnnotationsWithArguments.getAnnotationByClassId(classId, session)` |
| **Read String Argument** | `annotation.getStringArgument(name, session)` | `annotation.getStringArgument(name)` | `annotation.getStringArgument(name, session)` |
| **Read Boolean Argument** | `annotation.getBooleanArgument(name, session)` | `annotation.getBooleanArgument(name)` | `annotation.getBooleanArgument(name, session)` |

> [!IMPORTANT]
> - **Always pass the `session` parameter** to `getStringArgument`, `getBooleanArgument`, etc., to maintain compatibility with `2.0.x` (where the session argument is mandatory).
> - Use `symbol.resolvedAnnotationsWithArguments` (imported from `org.jetbrains.kotlin.fir.symbols.resolvedAnnotationsWithArguments`) for multi-version argument resolution compatibility, since `getAnnotationWithResolvedArgumentsByClassId` is missing in `2.0.x`.

**Multi-Version Compliant Annotation Extraction Example:**
```kotlin
import org.jetbrains.kotlin.name.ClassId
import org.jetbrains.kotlin.name.Name
import org.jetbrains.kotlin.fir.declarations.hasAnnotation
import org.jetbrains.kotlin.fir.declarations.getAnnotationByClassId
import org.jetbrains.kotlin.fir.declarations.getStringArgument
import org.jetbrains.kotlin.fir.symbols.resolvedAnnotationsWithArguments

val annotationClassId = ClassId.fromString("com/example/MyAnnotation")
val argumentName = Name.identifier("value")

if (symbol.hasAnnotation(annotationClassId, session)) {
    // Multi-version compatible retrieval of annotation with arguments
    val annotation = symbol.resolvedAnnotationsWithArguments.getAnnotationByClassId(annotationClassId, session)
    val stringValue: String? = annotation?.getStringArgument(argumentName, session)
}
```

#### B. Deprecating Generated (Synthetic) Declarations
When a compiler plugin generates a synthetic method/class, it is often necessary to mark it as deprecated. K2 manages deprecations via `DeprecationsProvider` attached to declarations.

##### Method 1: Programmatic `@Deprecated` Annotation (Recommended)
Add a standard `@Deprecated` annotation to the declaration's `annotations` list during generation. The compiler automatically parses this annotation to construct the declaration's `DeprecationsProvider`.
```kotlin
import org.jetbrains.kotlin.fir.declarations.builder.buildDeprecatedAnnotationCall

val deprecatedAnnotation = buildDeprecatedAnnotationCall {
    // message = "This declaration is deprecated"
    // replaceWith = "..."
    // level = DeprecationLevel.WARNING
}
declaration.annotations.add(deprecatedAnnotation)
```

##### Method 2: Custom `DeprecationsProvider` (Advanced)
If you need to mark a declaration as deprecated without inserting a physical annotation call into the AST, subclass `DeprecationsProvider` and set it directly on the declaration using `replaceDeprecationsProvider`.

> [!WARNING]
> - `EmptyDeprecationsProvider.getDeprecationsInfo(...)` returns `EmptyDeprecationsPerUseSite` (non-null) in `2.0.x`, but returns `null` in `2.3.x`/`2.4.0`.
> - Base class signatures are stable, allowing a custom provider implementation to work across all versions.

```kotlin
import org.jetbrains.kotlin.fir.declarations.DeprecationsProvider
import org.jetbrains.kotlin.fir.declarations.DeprecationsPerUseSite
import org.jetbrains.kotlin.fir.declarations.FirDeprecationInfo
import org.jetbrains.kotlin.resolve.deprecation.DeprecationLevelValue
import org.jetbrains.kotlin.config.LanguageVersionSettings
import org.jetbrains.kotlin.fir.FirSession
import org.jetbrains.kotlin.fir.declarations.replaceDeprecationsProvider

class CustomDeprecationsProvider(val deprecation: FirDeprecationInfo) : DeprecationsProvider() {
    override fun getDeprecationsInfo(languageVersionSettings: LanguageVersionSettings): DeprecationsPerUseSite {
        return DeprecationsPerUseSite(deprecation, null)
    }
}

class CustomDeprecationInfo(
    override val deprecationLevel: DeprecationLevelValue,
    override val propagatesToOverrides: Boolean,
    private val message: String?
) : FirDeprecationInfo() {
    override fun getMessage(session: FirSession): String? = message
}

// Usage on a synthetic declaration:
val customProvider = CustomDeprecationsProvider(
    CustomDeprecationInfo(
        deprecationLevel = DeprecationLevelValue.WARNING,
        propagatesToOverrides = true,
        message = "This synthetic function is deprecated."
    )
)
declaration.replaceDeprecationsProvider(customProvider)
```

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
