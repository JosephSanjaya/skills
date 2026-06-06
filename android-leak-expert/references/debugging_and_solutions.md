# Android Memory Leak Debugging & Solutions Reference

## 1. ART Memory & GC Architecture
- **Allocations**: RegionTLAB (Thread-Local Allocation Buffer) lock-free bump-pointer allocation. Faster allocation, no sync overhead.
- **Garbage Collector**: Generational Concurrent Copying (CC) GC (Android 10+). Rearranges memory contiguously to reduce fragmentation. GC pauses are short (constant-time, independent of heap size) to prevent UI freezes.
- **Heap Limits**: Programmatic check via `Runtime.getRuntime().maxMemory()`. OS enforces strict dynamic memory boundaries. Exceeding them causes termination (often silent, no stack trace).
- **Reference Taxonomy**:
  1. *Strong*: GC root connected. Prevents collection. Default reference type.
  2. *Weak*: Cleared immediately on next GC. Use for listeners, callbacks.
  3. *Soft*: Cleared only during critical memory pressure. Use for resource-heavy caches.
  4. *Phantom*: Finalized objects marked for absolute removal. Use for pre-mortem native memory cleanup.

---

## 2. Heap Diagnostics & Profiling
### 2.1. Android Studio Memory Profiler Metrics
- **Depth**: Shortest path hops from GC Root. Low depth = direct system/static reference.
- **Shallow Size**: Memory consumed by object itself (excludes referenced objects).
- **Native Size**: C/C++ memory allocation (bitmaps, WebViews, custom JNI). Available Android 7.0+.
- **Retained Size**: Sum of memory freed if this object is collected (dominator tree sub-graph).

### 2.2. LeakCanary & Shark Engine
- **ObjectWatcher**: Wraps finished UI components (on onDestroy) in `WeakReference` with a `ReferenceQueue`. Checks after 5s; if weak ref is not cleared, dumps heap to `.hprof`.
- **Shark Engine**: Kotlin-based low-memory heap analyzer using Okio for streaming, sequences, and sealed classes.
- **Dominator Tree**: Rooted tree of ownership. Node $A$ dominates $B$ if all paths to $B$ pass through $A$.
- **ReferenceMatchers**: Exclude known framework/OEM leaks (e.g., `IMM_CURRENT_INPUT_CONNECTION`, `STATIC_MTARGET_VIEW`) via `referenceMatchers` configuration.

---

## 3. Classic Leak Patterns & Solutions
### 3.1. Static References
- **Problem**: Companion objects or static fields holding `Context`, `View`, or `Activity`.
- **Solution**: Never store UI elements statically. If Context is needed, use `context.applicationContext`. Otherwise wrap in `WeakReference`.

### 3.2. Implicit Inner Class References
- **Problem**: Non-static nested classes (anonymous threads, Handlers, AsyncTasks) hold implicit pointer to outer class. Delayed Message/Thread execution blocks GC of outer `Activity`/`Fragment`.
- **Solution**: Declare nested classes as static (no `inner` keyword in Kotlin). Use a `WeakReference` to reference the outer instance if UI interaction is required. Symmetrically clear callbacks on teardown (`removeCallbacksAndMessages(null)`).

### 3.3. RecyclerView Adapter Dual-Lifecycle Leak
- **Problem**: Fragments have two lifecycles: Fragment instance and Fragment View. Storing `RecyclerView.Adapter` as a class property keeps references to ViewHolders and views after `onDestroyView()`.
- **Solution**: Symmetrically nullify the binding and the adapter/RecyclerView:
  ```kotlin
  override fun onDestroyView() {
      binding.recyclerView.adapter = null
      _binding = null
      super.onDestroyView()
  }
  ```

### 3.4. WebView Native Memory
- **Problem**: Chromium allocates out-of-heap native memory. WebViews retain Activity context.
- **Solution**: Initialize with Application Context. On destruction, detach from parent, clear cache/history, and destroy:
  ```kotlin
  val parent = webView.parent as? ViewGroup
  parent?.removeView(webView)
  webView.clearHistory()
  webView.clearCache(true)
  webView.destroy()
  ```

### 3.5. Reactive Streams (RxJava)
- **Problem**: Un-disposed subscriptions hold observers/contexts on background threads.
- **Solution**: Store subscriptions in a `CompositeDisposable`. Symmetrically clear/dispose:
  - `clear()`: Terminates active streams, permits adding new subscriptions later. Use in `Fragment.onDestroyView()`.
  - `dispose()`: Terminates streams permanently, rejects future subscriptions. Use in `Activity.onDestroy()`.

---

## 4. JNI Native Memory Management
- **Local Reference Registry**: Default 16 slots, hard cap of 65,535 references. Exceeding causes VM crash.
- **DeleteLocalRef**: Must manually call inside loops converting C/C++ data to Java objects (e.g., string conversion):
  ```cpp
  jstring localStr = env->NewStringUTF("data");
  // ... process ...
  env->DeleteLocalRef(localStr);
  ```
- **Frame Management**: For complex native blocks, isolate references using `PushLocalFrame(capacity)` and `PopLocalFrame(keepRef)`:
  ```cpp
  if (env->PushLocalFrame(256) < 0) return NULL;
  jobject res = env->NewObject(...);
  return env->PopLocalFrame(res); // All other refs deleted
  ```
- **Native Profiling**: Use `heapprofd` (sampling profiler via Perfetto) or `libmemunreachable` (zero-overhead native mark-and-sweep).

---

## 5. Enterprise-Scale Observations
### 5.1. Production Observability
- **Lyft**: A/B tests memory footprints on feature flag rollouts to detect C++ SDK regressions.
- **Square**: Linear regression on interaction latency & heap usage across navigation transitions (positive slope = memory leak).
- **Uber**:
  - Model Auto-Retirement: Unloads machine learning models when idle to free heap.
  - **FixrLeak**: Automated CI pipeline using AST parsing (Tree-sitter) to find intra-function stream leaks and generate `try-with-resources` patches via GenAI without use-after-close risk.

### 5.2. CI/CD Instrumentation Testing
- **Trap-Tests**: QA tests that rapidly recreate and destroy target Fragments (e.g., 30 times in a loop) to magnify small leaks into obvious OOMs.
- **JUnit Rule Alignment**: Position `DetectLeaksAfterTestSuccess` inside/outside `ActivityScenarioRule` based on target:
  - Outside: Captures Activity teardown leaks.
  - Inside: Captures Fragment/View leaks while Activity is alive.
