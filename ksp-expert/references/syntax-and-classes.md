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
