# Custom Detekt Rules: Type Resolution (Analysis API)

Type resolution allows querying compiler symbols, smart casts, and fully-resolved types instead of raw syntax. This is required when syntactic inspection alone is insufficient.

## 1. Detekt 1.x (K1 Compiler)
Requires implementing `RequiresFullAnalysis` (older: `@RequiresTypeResolution`) and accessing via `bindingContext`.

```kotlin
import io.gitlab.arturbosch.detekt.api.Config
import io.gitlab.arturbosch.detekt.api.Rule
import io.gitlab.arturbosch.detekt.api.RequiresFullAnalysis
import org.jetbrains.kotlin.resolve.BindingContext
import org.jetbrains.kotlin.psi.KtNamedFunction

class MyTypeRule(config: Config) : Rule(config), RequiresFullAnalysis {
    override fun visitNamedFunction(function: KtNamedFunction) {
        super.visitNamedFunction(function)
        if (bindingContext == BindingContext.EMPTY) return // Guard against light analysis
        val type = function.typeReference?.getType(bindingContext)
        // ...
    }
}
```

## 2. Detekt 2.0 (K2 Compiler & Analysis API)
Requires implementing `RequiresAnalysisApi`. Wrap resolution inside Kotlin's Analysis API `analyze(element)` block. Do not cache symbol instances outside the `analyze` block.

```kotlin
import dev.detekt.api.Config
import dev.detekt.api.Rule
import dev.detekt.api.RequiresAnalysisApi
import org.jetbrains.kotlin.analysis.api.analyze
import org.jetbrains.kotlin.analysis.api.types.KaFunctionType
import org.jetbrains.kotlin.psi.KtNamedFunction

class MyTypeRule(config: Config) : Rule(config, "desc"), RequiresAnalysisApi {
    override fun visitNamedFunction(function: KtNamedFunction) {
        super.visitNamedFunction(function)
        analyze(function) {
            val returnType = function.symbol.returnType
            if (returnType is KaFunctionType) {
                // ...
            }
        }
    }
}
```

### API Translation Mapping (1.x -> 2.0)
| 1.x (K1) | 2.0 (K2 Analysis API inside `analyze {}`) |
| :--- | :--- |
| `expression.getType(bindingContext)` | `expression.expressionType` |
| `bindingContext[REFERENCE_TARGET, ref]` | `ref.mainReference.resolveToSymbol()` |
| `expression.getResolvedCall(bindingContext)` | `expression.resolveToCall().successfulCallOrNull()` |
| `DeclarationDescriptor` | `KaSymbol` (obtained via `element.symbol`) |
| `KotlinType` | `KaType` |
