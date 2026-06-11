# Custom Detekt Rules: Reports & Output Formatting

To make custom rules present cleanly in Detekt's report formats (HTML, SARIF, Checkstyle, Markdown), you must design your rule metadata, messages, and code locations carefully.

## 1. Rule Metadata & Descriptions (Documentation Headers)
Reporters use the rule description as the global documentation for the rule at the top of the violation section.

- **Detekt 1.x**: The metadata is defined inside the overridden `issue` property:
  ```kotlin
  override val issue = Issue(
      id = "ComposeModifierReused",
      severity = Severity.CodeSmell,
      description = "Modifier parameters should not be reused across multiple layout calls.",
      debt = Debt.FIVE_MINS
  )
  ```
- **Detekt 2.0**: The description is passed directly to the `Rule` constructor:
  ```kotlin
  class ComposeModifierReused(config: Config) : Rule(
      config,
      "Modifier parameters should not be reused across multiple layout calls."
  ) {
      override val ruleName = RuleName("ComposeModifierReused")
  }
  ```

## 2. Precise Location Hooking via `Entity`
Avoid anchoring findings to the entire parent class or function. If you pass `Entity.from(function)`, the report highlights the entire function body.
Instead, anchor the finding to the **exact offending element** (e.g., the specific argument or expression):

- **Bad (Highlights whole function)**:
  ```kotlin
  report(Finding(Entity.from(function), "Modifier is reused"))
  ```
- **Good (Highlights only the reused argument/node)**:
  ```kotlin
  report(Finding(Entity.from(modifierArg), "Modifier '$modifierName' is reused here"))
  ```
The reporter will then output the exact line number, column, and highlight a concise code snippet containing only that line.

## 3. Context-Rich Violation Messages
The message in the reported `Finding` / `CodeSmell` is printed directly underneath the code snippet in HTML/SARIF reports. Implement the **Violation -> Rationale -> Recommendation** formula:

- **Template**:
  `"Modifier '$modifierName' is reused in $modifierUsageCount layout calls. Each modifier parameter should only be applied to the root layout node. Replace subsequent reuses with a default 'Modifier' or customized chain."`

## 4. HTML/SARIF Representation Example
When configured correctly, the Detekt HTML report represents the issue as:
```text
[Ruleset: compose]
ComposeModifierReused  -  5 min debt

  Modifier parameters should not be reused across multiple layout calls. (Global Description)

  - MyComponent.kt:28:18  (Hooked from Entity.from(modifierArg))
    
    Code snippet:
    27 |    Row(modifier) {
    28 |        Box(modifier)
       |            ^^^^^^^^ [ComposeModifierReused] Modifier 'modifier' is reused in 2 layout calls. ... (Finding Message)
    29 |    }
```
