# KSP Core Syntax and Classes

## Processing API (`com.google.devtools.ksp.processing`)

- **`SymbolProcessorProvider`**: Factory interface. Entry point.
  - `fun create(env: SymbolProcessorEnvironment): SymbolProcessor`
- **`SymbolProcessor`**: Processor interface.
  - `fun process(resolver: Resolver): List<KSAnnotated>`: returns deferred symbols.
  - `fun finish()`: run after all rounds complete.
  - `fun onError()`: run if compilation errors occur.
- **`SymbolProcessorEnvironment`**: Context provider.
  - Properties: `codeGenerator`, `logger`, `options` (map), `platforms`, `kotlinVersion`.
- **`Resolver`**: Query engine for AST.
  - `getSymbolsWithAnnotation(name: String): Sequence<KSAnnotated>`
  - `getClassDeclarationByName(name: KSName): KSClassDeclaration?`
  - `getAllFiles(): Sequence<KSFile>`
  - `getModuleName(): KSName`
- **`CodeGenerator`**: File creator. Participates in incrementality.
  - `createNewFile(deps: Dependencies, pkg: String, name: String, ext: String = "kt"): OutputStream`
- **`Dependencies`**: Tracks outputs to sources.
  - `Dependencies(aggregating: Boolean, vararg sources: KSFile)`
  - `Dependencies.ALL_FILES`: Disables incrementality. Avoid.
- **`KSPLogger`**: Diagnostic logger.
  - Methods: `info()`, `warn()`, `error()`, `exception()`.

## AST Symbols (`com.google.devtools.ksp.symbol`)

- **`KSNode`**: Base element. Has `origin: Origin`, `location: Location`.
- **`KSAnnotated`**: Can hold annotations. Has `annotations: Sequence<KSAnnotation>`.
- **`KSAnnotation`**: Annotation reference.
  - Properties: `annotationType: KSTypeReference`, `arguments: List<KSValueArgument>`, `shortName: KSName`.
- **`KSDeclaration`**: Declared symbol. Has `packageName`, `simpleName`, `qualifiedName`, `modifiers`, `isActual`, `isExpect`.
- **`KSClassDeclaration`**: Class / Interface.
  - Properties: `classKind: ClassKind`, `superTypes`, `primaryConstructor`, `declarations: Sequence<KSDeclaration>`.
  - Methods: `getDeclaredFunctions()`, `getDeclaredProperties()`.
- **`KSFunctionDeclaration`**: Function / Constructor.
  - Properties: `parameters: List<KSValueParameter>`, `returnType: KSTypeReference?`.
- **`KSPropertyDeclaration`**: Var/val property.
  - Properties: `type: KSTypeReference`, `getter`, `setter`.
- **`KSFile`**: Source file representation. Has `packageName`, `fileName`, `filePath`, `declarations`.
- **`KSTypeReference`**: Unresolved type reference.
  - `fun resolve(): KSType`: Resolves reference to concrete type (expensive!).
- **`KSType`**: Resolved semantic type.
  - Properties: `declaration: KSDeclaration`, `arguments: List<KSTypeArgument>`, `nullability: Nullability`.
  - Methods: `isAssignableFrom(that: KSType): Boolean`, `makeNullable()`, `makeNotNullable()`.
- **`KSValueArgument`**: Argument passed to annotation.
  - Properties: `name: KSName?`, `value: Any?`.

## Crucial Extension Functions & Imports

Many common AST utility and validation APIs in KSP are defined as extension functions in the `com.google.devtools.ksp` package. You must explicitly import them in your Kotlin source files:

*   **`KSNode.validate(): Boolean`**: Recursively validates that all semantic types under this node are fully resolved (returns `false` if they represent error types, allowing deferring compilation to subsequent rounds).
    ```kotlin
    import com.google.devtools.ksp.validate
    ```
*   **`KSDeclaration.closestClassDeclaration(): KSClassDeclaration?`**: Recursively walks up the parent tree to find the nearest enclosing class declaration.
    ```kotlin
    import com.google.devtools.ksp.closestClassDeclaration
    ```
*   **`KSClassDeclaration.getDeclaredProperties(): Sequence<KSPropertyDeclaration>`**: Returns only properties declared directly in this class body (ignoring superclass properties).
    ```kotlin
    import com.google.devtools.ksp.getDeclaredProperties
    ```
*   **`KSClassDeclaration.getDeclaredFunctions(): Sequence<KSFunctionDeclaration>`**: Returns only functions declared directly in this class body.
    ```kotlin
    import com.google.devtools.ksp.getDeclaredFunctions
    ```
*   **`Resolver.getClassDeclarationByName(name: KSName): KSClassDeclaration?`**: To look up a class declaration by its qualified name string, first convert it to a `KSName` using `Resolver.getKSNameFromString`.
    ```kotlin
    val qualifiedName = "com.example.MyClass"
    val classDeclaration = resolver.getClassDeclarationByName(resolver.getKSNameFromString(qualifiedName))
    ```
