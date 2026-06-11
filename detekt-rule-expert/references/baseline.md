# Baseline Support in Custom Rules

Detekt's baseline feature (`baseline.xml`) suppresses existing violations by checking if a finding's signature matches an entry in the baseline. Custom rules must be designed to generate stable, predictable signatures to work correctly with baselines.

---

## 1. How Detekt Signatures Work

Detekt stores suppressed issues in the baseline file in the format `<RuleID>:<Signature>`.
* **Signature derivation**: Calculated by traversing the AST from the reported `KtElement` up to the file root to build a unique path (e.g., `File.kt$ClassName$functionName`).
* **Suppression matching**: On subsequent runs, Detekt computes the signature for each finding. If a match exists in the baseline, the finding is suppressed.

---

## 2. Common Causes of Baseline Bypass / Failures

### 1. Reporting at File-Level (`KtFile`)
Reporting a finding on a `KtFile` (e.g. `Entity.from(file)`) generates a signature consisting only of the filename (e.g., `MyFile.kt`).
* **Consequence**: Any new violation of the same rule anywhere in that file will match the file-level signature and be incorrectly suppressed.
* **Fix**: Always report findings on the most specific `KtElement` (e.g., function, class, property) causing the issue.

### 2. Reporting on Unnamed or Unstable Nodes
Reporting findings on transient or unnamed AST nodes (e.g., `KtBinaryExpression`, parentheses, or raw list arguments) causes Detekt's signature generator to either:
* Fall back to line/column numbers, making the signature extremely fragile. The baseline will break if any lines are added or removed above the finding.
* Throw an `IllegalArgumentException` in `Signatures.kt` if the AST path cannot be fully resolved.
* **Fix**: Anchor the reported `Entity` to the closest named declaration parent (e.g., the containing function or property) if the sub-expression structure is highly transient.

### 3. Dynamic Rule IDs
If your custom `Rule` class computes its `id` dynamically, the generated signatures will mismatch.
* **Fix**: Ensure the `id` is a static, unique string:
  ```kotlin
  // Detekt 1.x
  override val id: String = "MyCustomRule"
  // Detekt 2.0
  class MyCustomRule(config: Config) : Rule(config, "description") {
      override val id: String = "MyCustomRule"
  }
  ```

### 4. Custom Classpath Discrepancies
If the custom rule JAR is not loaded in the `detektPlugins` classpath of the `detektBaseline` generation task, its findings will be missing from the baseline.
* **Fix**: Verify your Gradle configuration maps the custom rule module to `detektPlugins` consistently across all tasks.

---

## 3. Implementation Patterns for Stable Signatures

### Anchoring to Stable Named Declarations
When checking statements or expressions inside a block, retrieve and report on the nearest stable named declaration to ensure signature stability:

```kotlin
import org.jetbrains.kotlin.psi.KtNamedFunction
import org.jetbrains.kotlin.psi.psiUtil.getParentOfType

// Inside your visitor:
override fun visitCallExpression(expression: KtCallExpression) {
    super.visitCallExpression(expression)
    if (violatesRule(expression)) {
        // Resolve parent function to anchor the signature stably
        val anchorElement = expression.getParentOfType<KtNamedFunction>(true) ?: expression
        report(
            CodeSmell(
                issue = issue,
                entity = Entity.from(anchorElement), // Stably maps to the function signature
                message = "Rule violated inside function ${anchorElement.name ?: ""}"
            )
        )
    }
}
```

### Inspecting Generated Signatures
To verify that your custom rule generates a stable signature without line-number fallbacks:
1. Run Detekt with the text report option:
   ```bash
   ./gradlew detekt --report txt:build/reports/detekt.txt
   ```
2. Inspect `build/reports/detekt.txt`. Each finding displays its computed signature. Ensure it contains structural identifiers (e.g., `MyClass$myMethod`) and not line numbers.
