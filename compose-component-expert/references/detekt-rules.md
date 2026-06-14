# Detekt & Ktlint Compose Static Analysis Rules Index

Conform to static analysis rules to pass CI checks and ensure clean architecture.

## 1. State Rules
- **ViewModelForwarding**: Do not pass ViewModels down to child composables. Pass plain data and callbacks.
- **RememberMissing**: Always wrap snapshot state builders (`mutableStateOf`) in `remember` or `rememberSaveable`.
- **VarsWithoutStateBacking**: Composed local `var` properties must be backed by Compose State (`by remember { ... }`) to trigger recomposition on write.
- **MutableStateAutoboxing**: Use primitive state holders (`mutableIntStateOf`, `mutableFloatStateOf`) instead of boxed variants (`mutableStateOf<Int>`) to avoid JVM allocation overhead.

## 2. Composable API Rules
- **MutableParams**: Do not pass mutable parameters (e.g. `ArrayList`, custom mutable classes) to composables.
- **MutableStateParam**: Do not pass `MutableState<T>` as a parameter. Hoist state instead.
- **StateParam**: Do not pass `State<T>` as a parameter. Pass raw value `T` and update event lambda `(T) -> Unit`.
- **LambdaParameterInRestartableEffect**: Pass dependent callbacks to effects as keys, or use `rememberUpdatedState` to avoid stale capture.
- **ContentEmitterReturningValues**: Composable functions must either emit layout UI or return a value, not both.
- **MultipleEmitters**: A composable must emit exactly zero or one layout node. Wrap multiple children in a `Column`, `Row`, or `Box`.
- **ConditionHoist**: Hoist single conditional layout content out of container layouts (e.g., wrap `Column` in `if (show)` instead of inside).
- **ContentTrailingLambda**: Content slot parameters should be at the trailing position so they support trailing lambda syntax.
- **ContentSlotReused**: Do not reuse content slot lambdas inside branching blocks (causes disposals). Use `remember { movableContentOf { ... } }`.
- **LambdaParameterEventTrailing**: Do not place event lambdas (`onClick`) in trailing position (confuses them with content slots). Place them before `Modifier`.
- **ComposableParamOrder**: Param ordering must be: Required -> Optional (starting with `modifier`) -> Trailing content lambda.
- **ParameterNaming**: Present-tense event callbacks (`onClick`, `onValueChange`).

## 3. Naming Rules
- **CompositionLocalNaming**: Prefix `CompositionLocal` with `Local` (e.g. `LocalSpacing`).
- **PreviewAnnotationNaming**: Prefix custom multipreview annotations with `Previews` (e.g. `@PreviewsPhone`).
- **ComposableNaming**: Unit-returning composables must be PascalCase nouns. Value-returning composables must be camelCase verbs.
- **PreviewNaming**: Composable previews must have `Preview` suffix.

## 4. Lifecycle & Performance
- **RememberContentMissing**: Always wrap `movableContentOf` in `remember`.
- **InvalidReadOnlyComposable**: Leaf read-only composables should only invoke other `@ReadOnlyComposable` targets.
- **MissingReadOnlyComposable**: Annotate pure data-reading composables with `@ReadOnlyComposable`.
- **UnnecessaryComposable**: Do not mark functions as `@Composable` if they don't invoke composables or read state/locals.
- **StaleRememberUpdatedStateInRemember**: Defer reading delegated `rememberUpdatedState` inside another `remember` block to avoid capturing stale values.
- **ViewModelInjection**: Inject ViewModels as default parameter values at the root composable level (`vm: MyViewModel = hiltViewModel()`).
- **CompositionLocalAllowlist**: Limit custom `CompositionLocal` usage; register allowed ones in Detekt config.
- **PreviewPublic**: Preview composables must be `private` to avoid polluting the public API.

## 5. Modifier Rules
- **ModifierMissing**: Public UI components must expose a `modifier: Modifier = Modifier` parameter.
- **ModifierClickableOrder**: Apply `.clip` and `.background` before `.clickable` so the ripple matches the element shape.
- **ModifierNotUsedAtRoot**: Apply the `modifier` parameter to the root layout of the component.
- **ModifierReused**: The `modifier` parameter must only be applied once in the component (at the root node). Children use fresh `Modifier` instances.
- **ModifierWithoutDefault**: Modifier parameters must default to `Modifier`.
- **ModifierNaming**: The root modifier parameter must be named `modifier`. Subcomponents use `headerModifier`, `footerModifier` etc.
- **ModifierComposed**: Do not use `composed { }` to build custom modifiers. Use `Modifier.Node` instead.

## 6. Opt-In Rules
- **Material2**: Restrict usage of Material 2 classes/components; migrate to Material 3.
- **UnstableCollections**: Do not pass standard unstable `List`/`Map`/`Set` interfaces to composables. Use kotlinx immutable collections or wrap them in `@Immutable` data classes.
- **ComposableNestingDepth**: Prevent deeply nested content emitters in a single composable function (threshold defaults to 3 levels). Extract child sections.
