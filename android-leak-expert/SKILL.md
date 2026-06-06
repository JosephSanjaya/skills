---
name: android-leak-expert
description: >-
  Expert guide for detecting, profiling, and resolving memory leaks in Android apps (Java, Kotlin, Compose, JNI). Use when analyzing memory usage, profiling heap dumps, fixing out-of-memory (OOM) issues, checking Compose lifecycle flow collections, resolving WebView/Handler leaks, or configuring LeakCanary. Triggers include android memory leak, OOM in android, profile heap dump, leakcanary setup, fix handler leak, fragment view binding leak, composable memory leak, collectAsState vs collectAsStateWithLifecycle, heapprofd native leak, DeleteLocalRef JNI.
---

# Android Leak Expert

Identify, profile, and fix memory leaks in Android applications (Java, Kotlin, Jetpack Compose, JNI).

<instructions>
Symmetrically unbind resources in lifecycles, collect flow streams lifecycle-aware, use static classes with WeakReference for background work, and manually clear native/JNI references.
</instructions>

## 1. Quick Decision Tree
- **Suspicious code scan** → Run scan script (`scripts/scan_leak_vectors.py`)
- **Profile memory / investigate heap dump** → Heap Profiling & Dominator Trees ([references/debugging_and_solutions.md#2-heap-diagnostics--profiling](references/debugging_and_solutions.md#2-heap-diagnostics--profiling))
- **Fix classic view/fragment leak** → Teardown & Lifecycle Binding ([references/debugging_and_solutions.md#3-classic-leak-patterns--solutions](references/debugging_and_solutions.md#3-classic-leak-patterns--solutions))
- **Fix Compose/flow state leak** → Compose Flow Collection & Effect Cleanups ([references/jetpack_compose.md](references/jetpack_compose.md))
- **Fix native C++/JNI leak** → Native JNI Frame & Registry Release ([references/debugging_and_solutions.md#4-jni-native-memory-management](references/debugging_and_solutions.md#4-jni-native-memory-management))
- **Set up CI/CD verification** → Trap-Tests & JUnit RuleChains ([references/debugging_and_solutions.md#5-enterprise-scale-observations](references/debugging_and_solutions.md#5-enterprise-scale-observations))
- **Now In Android reference** → View code patterns ([references/nowinandroid.md](references/nowinandroid.md))

## 2. Fast Command Tools
Scan target code directory for common memory leaks:
```bash
python3 scripts/scan_leak_vectors.py <path_to_android_project_or_file>
```

## 3. Clean Code Reference Implementations
- **Safe Handler Pattern**: [SecureHandlerSample.kt](assets/SecureHandlerSample.kt)
- **Safe Fragment Adapter Binding**: [SecureFragmentSample.kt](assets/SecureFragmentSample.kt)
- **Safe Compose Lifecycle**: [SecureComposeLifecycleSample.kt](assets/SecureComposeLifecycleSample.kt)

<constraints>
Developers must follow these rules. Ensure all custom handlers are static, fragments should nullify bindings/adapters in onDestroyView, and compose collections must only use collectAsStateWithLifecycle.
</constraints>

