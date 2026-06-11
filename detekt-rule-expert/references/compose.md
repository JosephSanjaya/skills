# Custom Detekt Rules for Jetpack Compose: AST/PSI Parsing Guide

This guide details how to implement custom Detekt rules that target and analyze Jetpack Compose syntax, using patterns extracted from the `compose-rules` codebase.

---

## 1. Identifying Composable Declarations

To target `@Composable` functions or properties, check their annotations and receivers.

### Annotation Parsing
```kotlin
import org.jetbrains.kotlin.psi.KtFunction
import org.jetbrains.kotlin.psi.KtAnnotationEntry

val KtFunction.isComposable: Boolean
    get() = annotationEntries.any { it.shortName?.asString() == "Composable" }
```
*Note*: For custom Composable annotations (e.g. `@ComposableTargetMarker`), use K2 type resolution inside `analyze {}` to verify if the annotation's symbol or meta-annotations match the target marker class.

### Visibility & Override Filters
Composable checks should typically ignore overridden functions, interface declarations, and previews:
```kotlin
import org.jetbrains.kotlin.psi.KtFunction
import org.jetbrains.kotlin.psi.psiUtil.isPublic

fun shouldCheck(function: KtFunction): Boolean {
    val isOverride = function.modifierList?.hasModifier(org.jetbrains.kotlin.lexer.KtTokens.OVERRIDE_KEYWORD) == true
    val isPreview = function.annotationEntries.any { it.shortName?.asString() == "Preview" }
    
    return !isOverride && !isPreview && function.isPublic
}
```

---

## 2. Counting Layout Emitters (Layout-emitting vs. Return composables)

To enforce rules like `MultipleEmitters` or `ContentEmitterReturningValues`, you must detect if a Composable function calls elements that emit layout content.

### Emitter Allowlist / Denylist
Maintain standard sets of names for layout-emitting UI components (e.g., `Box`, `Column`, `Row`, `Text`, `Canvas`, etc.) and non-emitting components (e.g., `AlertDialog`, `Dialog`, `Popup`).

### Tracing Layout Calls
Check if a `KtCallExpression` represents a content emitter:
1. Callee name matches a standard UI emitter.
2. The callee uses a modifier argument (e.g., a named argument named `"modifier"`, or an argument starting with `Modifier.`).

```kotlin
import org.jetbrains.kotlin.psi.KtCallExpression
import org.jetbrains.kotlin.psi.KtDotQualifiedExpression

fun KtCallExpression.emitsContent(emitters: Set<String>): Boolean {
    val calleeName = calleeExpression?.text ?: return false
    if (calleeName in emitters) return true
    
    // Check if any argument is a modifier chain starting with "Modifier"
    return valueArguments.mapNotNull { it.getArgumentExpression() }
        .filterIsInstance<KtDotQualifiedExpression>()
        .any { it.rootExpression.text == "Modifier" }
}
```

### Recursive AST Counting
Use a visitor or recursive helper to calculate how many UI emitters are invoked within a Composable body, handling control flows:
- **Conditionals (`KtIfExpression`, `KtWhenExpression`)**: Take the *maximum* number of emitters between the branches.
- **Loops (`KtLoopExpression`)**: Count the body emitters; if > 0, assume at least 2 iterations.
- **Scope functions (`run`, `let`, `with`)**: Recursively parse the statements in the lambda block body.

---

## 3. Tracing Modifiers

Rules like `ModifierReused` and `ModifierNotUsedAtRoot` require tracking the lifecycle and reassignments of modifier arguments.

### Collecting Modifier Names (Name Propagation)
Modifiers are often reassigned or chained (e.g. `val customModifier = modifier.fillMaxWidth()`). To find all usages, recursively search the block for properties that reassign the original modifier parameter name.

```kotlin
import org.jetbrains.kotlin.psi.KtBlockExpression
import org.jetbrains.kotlin.psi.KtProperty
import org.jetbrains.kotlin.psi.KtReferenceExpression

fun KtBlockExpression.obtainAllModifierNames(initialName: String): List<String> {
    val names = mutableSetOf(initialName)
    var previousSize = 0
    
    while (names.size > previousSize) {
        previousSize = names.size
        // Find local variables that reference any name in our set
        val manipulations = statements
            .filterIsInstance<KtProperty>()
            .filter { property ->
                property.findAllChildrenByClass<KtReferenceExpression>()
                    .any { it.text in names }
            }
            .mapNotNull { it.nameIdentifier?.text }
        names.addAll(manipulations)
    }
    return names.toList()
}
```

### Checking Modifier Usage in Calls
Check if a layout call is passed a modifier reference:
```kotlin
fun KtCallExpression.isUsingModifier(modifierNames: Set<String>): Boolean {
    return valueArguments.any { argument ->
        val expression = argument.getArgumentExpression()
        expression is KtReferenceExpression && expression.text in modifierNames ||
        expression is KtDotQualifiedExpression && expression.rootExpression.text in modifierNames
    }
}
```

---

## 4. Tracing ViewModel/State Holders

### Identifying ViewModel Parameters
Inspect parameters to find type references matching state holder patterns:
```kotlin
import org.jetbrains.kotlin.psi.KtParameter

fun KtParameter.isViewModel(stateHolderRegex: Regex): Boolean {
    val typeText = typeReference?.text ?: return false
    return typeText.matches(stateHolderRegex)
}
```

### Checking for ViewModel Forwarding
To verify if a ViewModel reference is passed down (forwarded) to another Composable:
1. Walk children of the function body to collect all `KtCallExpression` nodes.
2. Filter out non-UI calls (like `LaunchedEffect`, `DisposableEffect`).
3. Inspect their `valueArguments` to check if a resolved reference matches the parameters holding the ViewModel.

---

## 5. CompositionLocal & Scopes

### Detecting CompositionLocal Declarations
Verify if a `KtProperty` initializes a CompositionLocal:
```kotlin
import org.jetbrains.kotlin.psi.KtProperty
import org.jetbrains.kotlin.psi.KtCallExpression

val KtProperty.declaresCompositionLocal: Boolean
    get() = !isVar &&
            hasInitializer() &&
            initializer is KtCallExpression &&
            (initializer as KtCallExpression).calleeExpression?.text in setOf(
                "staticCompositionLocalOf",
                "compositionLocalOf"
            )
```

### Detecting Nested `remember` Scopes
Check if a `KtCallExpression` is nested under a `remember` block by traversing its AST parents:
```kotlin
import com.intellij.psi.PsiElement
import org.jetbrains.kotlin.psi.psiUtil.parents

fun KtCallExpression.isRemembered(stopAt: PsiElement): Boolean {
    return parents
        .takeWhile { it != stopAt }
        .filterIsInstance<KtCallExpression>()
        .mapNotNull { it.calleeExpression?.text }
        .any { name -> name.startsWith("remember") || name == "retain" }
}
```
