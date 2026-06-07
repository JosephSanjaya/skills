# **Comprehensive Architectural Analysis of Dagger and Hilt: Strategies for Efficient Module Management and Scope Optimization in Scalable Android Systems**

The advancement of Android software engineering has historically been characterized by a persistent struggle against complexity, particularly regarding the management of object lifecycles and their interdependencies. Dependency injection (DI) has emerged as the definitive architectural pattern to mitigate this complexity, transitioning from manual implementation to the sophisticated, compile-time validated frameworks represented by Dagger and its Android-specific extension, Hilt.1 As applications scale into the multi-module domain, the efficiency of module management and the precision of scoping become paramount. Inefficient DI configurations—manifesting as overly broad scopes or monolithic modules—directly correlate with degraded runtime performance, increased memory pressure, and sluggish build times.3 This report provides an exhaustive investigation into the latest documentation and industry best practices for Dagger and Hilt, articulating a rigorous framework for professional-grade dependency management.

## **The Evolution of Dependency Injection Frameworks on Android**

The necessity of dependency injection arises from the fundamental requirement for clean architecture, which dictates that classes should not be responsible for instantiating their own dependencies. Manual dependency injection, while transparent in small projects, becomes increasingly error-prone and tedious as the dependency graph expands.1 Historically, developers utilized service locators or manual container classes, but these patterns often led to boilerplate-heavy codebases and difficult-to-trace object lifetimes.6 Dagger 2 revolutionized this space by introducing a compile-time approach to DI, leveraging annotation processing to build and validate dependency graphs during the build phase.5 This methodology ensures that missing dependencies or circular references are caught before runtime, a significant improvement over reflection-based alternatives like Guice.5

Hilt, introduced as an opinionated layer atop Dagger, addresses the specific friction points of Dagger in the Android environment.1 By providing predefined components that map directly to Android framework classes—such as Activities, Fragments, and ViewModels—Hilt eliminates the vast majority of boilerplate code associated with manual component and subcomponent definition.1 The primary goal of Hilt is the standardization of DI infrastructure, enabling developers to focus on module definition rather than graph wiring.1 This shift toward standardization is not merely a convenience but a strategic imperative for large teams, as it prevents the "over-creativity" in Dagger configurations that often results in fragmented, unmaintainable architectures.2

| Comparison Metric | Manual Dependency Injection | Vanilla Dagger | Hilt (Latest) |
| :---- | :---- | :---- | :---- |
| **Validation Timing** | Runtime (Manual checking) | Compile-time (Validation) 9 | Compile-time (Standardized) 6 |
| **Component Creation** | Manual Factory classes 8 | Manual @Component interfaces 5 | Auto-generated standard components 1 |
| **Android Integration** | Manual wiring in onCreate | Manual Subcomponents/Injectors 3 | @AndroidEntryPoint automation 1 |
| **Boilerplate Volume** | Extreme (Linear with graph size) | High (Setup requirements) 2 | Low (Standardized modules) 2 |
| **Scalability** | Poor (Becomes unmanageable) | Excellent (Customizable) 9 | Excellent (Opinionated/Fast) 1 |

## **Principles of Efficient Module Management**

The efficiency of a Dagger or Hilt graph is fundamentally determined by how modules are organized and how dependencies are provided. A module, in this context, is a class annotated with @Module that informs the framework how to provide instances of types that cannot be constructor-injected, such as interfaces or third-party library classes.1 The latest documentation emphasizes two critical axes for module optimization: granularity and provider efficiency.

### **Granularity and the Single-Purpose Module**

A common anti-pattern in maturing projects is the creation of monolithic modules—large classes that house dozens of unrelated @Provides methods. While functional, these modules impede both build performance and testability.11 When a module is overly broad, any change to a single binding forces the annotation processor to re-evaluate the entire module, and any test requiring only one binding from that module may be forced to carry the weight of the entire dependency set.12 Professional best practices now advocate for single-purpose modules, where each module is responsible for a cohesive functional unit, such as a specific API service, a database configuration, or a domain-specific repository.9

The implications of granularity extend into the testing domain. Hilt's testing APIs, such as @TestInstallIn, are designed to replace modules rather than individual bindings.12 Consequently, if a module contains both a network client and a logging service, and a developer only needs to mock the network client, they are forced to provide a fake for the logging service as well if they replace the entire module.11 By splitting these into separate modules, the developer can target the specific dependency replacement precisely, improving the clarity and isolation of the test environment.11

### **Optimizing Provision through @Binds and @Provides**

The choice between @Binds and @Provides is a technical decision with measurable impact on the generated code. @Provides is necessary for types where the developer does not own the constructor or where complex initialization logic is required, such as configuring a Retrofit instance.3 However, @Provides methods have a higher overhead because they typically require Dagger to generate a factory class and, if the method is an instance method, instantiate the module itself to call the provider.14

Conversely, @Binds is an abstract method used for mapping an implementation to an interface when the implementation class already has an @Inject constructor.3 @Binds is the preferred approach because it is more efficient; Dagger does not need to generate a separate factory or instantiate the module at runtime.14 It simply casts the existing provider to the interface type at compile time. When @Provides must be used, it should be marked as static (or defined in a Kotlin object) to avoid the cost of module instantiation.14

| Provision Method | Use Case | Implementation Type | Generated Code Overhead |
| :---- | :---- | :---- | :---- |
| **Constructor Injection** | Classes owned by the project 14 | @Inject on constructor | Minimum (Dagger creates factory) |
| **@Binds** | Interface-to-Implementation mapping 3 | Abstract method in interface/class | Very Low (No module instance) 15 |
| **@Provides (Static)** | 3rd party/Simple logic 15 | Static method/Kotlin object | Moderate (Factory generated) |
| **@Provides (Instance)** | Complex logic requiring state 15 | Non-static method | High (Module instance required) |

## **Strategies for Scope Control and Resource Management**

Scoping is the mechanism by which Dagger ensures a single instance of a dependency is reused within the lifetime of its associated component. While scoping is essential for objects with internal state or expensive initialization, its overuse can lead to significant memory leaks and performance bottlenecks.3

### **The Predefined Hierarchy of Hilt Components**

Hilt simplifies scoping by providing a standardized hierarchy of components, each with a corresponding scope annotation. This hierarchy ensures that dependencies are automatically cleaned up when their parent Android class is destroyed, provided they are correctly scoped.1

* **SingletonComponent (@Singleton):** Lives for the duration of the application process. Best reserved for truly global services like network clients or databases.18  
* **ActivityRetainedComponent (@ActivityRetainedScoped):** Survives configuration changes (like rotations) but is destroyed when the Activity is finished. This is the ideal scope for repositories used in ViewModels.17  
* **ViewModelComponent (@ViewModelScoped):** Tied to the lifecycle of a specific ViewModel, providing a more granular scope than the Activity itself.18  
* **ActivityComponent (@ActivityScoped):** Destroyed when the Activity is destroyed. Suitable for UI-related dependencies like adapters or navigators.16  
* **FragmentComponent (@FragmentScoped):** Tied to a specific Fragment instance. Note that every Fragment gets its own component instance, so scoped bindings are not shared between different Fragment instances of the same class.16

### **Avoiding Broad Scope and Memory Bloat**

A pervasive mistake in Android architecture is the "Singleton-by-default" approach. Developers often place feature-specific dependencies in the SingletonComponent because it is the easiest way to ensure accessibility across the app.4 However, this forces the object to remain in memory even when the user is not interacting with that feature. For instance, an "OnboardingRepository" should not be a @Singleton; it should be scoped to the onboarding activity or its ViewModels so that it is purged once the onboarding flow is complete.4

The technical cost of scoping must also be considered. Scoped bindings in Dagger use a DoubleCheck locking mechanism to ensure thread safety during the initial provision.3 This check is significantly more expensive than the simple factory call used for unscoped bindings. Therefore, the latest documentation advises developers to minimize the use of scoped bindings. Scoping should only be applied if the object has an internal state that must be shared, requires expensive synchronization, or has a construction cost so high that it outweighs the overhead of managing a scoped instance.1

## **Advanced Multi-Module Architectures**

In modern Android development, projects are frequently partitioned into multiple Gradle modules to improve build times and enforce clear boundaries. This modularization complicates the Dagger graph, particularly when dealing with dynamic feature modules and visibility constraints.20

### **Transitive Dependencies and Classpath Aggregation**

Hilt's code generation requires a comprehensive view of the dependency graph. The Gradle module responsible for compiling the Application class (the "app" module) must have all Hilt modules and constructor-injected classes in its transitive dependencies.1 This can be a challenge in deep multi-module projects where dependencies are nested many layers deep. For such architectures, Hilt provides the enableExperimentalClasspathAggregation flag (often set via enableAggregatingTask \= true in the Gradle plugin), which allows Hilt to aggregate dependencies across modules more efficiently, reducing the risk of missing binding errors and potentially improving build performance.20

### **Managing Visibility with the Internal Module Pattern**

Kotlin's internal visibility modifier is a powerful tool for encapsulation, allowing developers to hide implementation details within a Gradle module. However, Dagger requires that the binding relationship between an interface and its implementation be visible to the component builder. This creates a conflict if a public Dagger module attempts to bind an internal implementation class.22

The professional solution is the "Internal Module Trick":

1. Define the interface as public.  
2. Define the implementation as internal.  
3. Create an internal Dagger module within the same Gradle module that performs the @Binds or @Provides of the implementation to the interface.22  
4. Create a public Dagger module that uses the includes parameter to include the internal module.22

This structure allows the public Dagger module to be added to the AppComponent in the app module without exposing the internal implementation class to other parts of the project, thus maintaining true separation of concerns.22

### **Dynamic Feature Modules and Inverted Dependencies**

Dynamic feature modules present a unique challenge because the dependency flow is inverted: the feature module depends on the app module, but the app module does not know about the feature module.20 Since Hilt generates the application-level component in the app module, it cannot automatically include bindings from a dynamic feature module.

To solve this, developers must use Dagger's component dependencies mechanism alongside Hilt's @EntryPoint.20 An @EntryPoint interface is declared in the app module, defining the specific dependencies required by the feature. The feature module then defines a standard Dagger @Component that lists this @EntryPoint as a dependency.20 This allows the feature module to "reach back" into the Hilt graph to pull out the dependencies it needs while maintaining the independence required for dynamic delivery.20

| Architecture Type | Dependency Flow | Hilt Integration Strategy |
| :---- | :---- | :---- |
| **Monolithic App** | Single module | Standard @AndroidEntryPoint and @InstallIn.1 |
| **Static Multi-Module** | Unidirectional to app | Transitive dependencies to app module.20 |
| **Dynamic Feature** | Inverted (Feature \-\> App) | Hilt @EntryPoint \+ Dagger Component Dependencies.20 |
| **Deep Modularization** | Highly nested | enableExperimentalClasspathAggregation \= true.20 |

## **Performance Optimization and Startup Latency**

A common criticism of DI frameworks is their impact on application startup latency. If the Application\#onCreate() or the initial Activity\#onCreate() triggers the instantiation of the entire dependency graph, the user experience suffers.4

### **Lazy Injection and Provider Patterns**

Not every dependency is needed at the moment of injection. For heavy objects like analytics SDKs, remote config managers, or complex database initializers, developers should utilize Lazy\<T\> or Provider\<T\>.4

* **Lazy:** Defers the instantiation of the dependency until the first time get() is called. This is critical for preventing the "fire up the entire world" scenario during app launch.4  
* **Provider:** Allows the caller to retrieve a new instance (or the same instance if scoped) every time get() is called. This is useful for breaking circular dependencies or handling short-lived objects.15

By delaying non-critical initializations and moving them to background threads using a delayed initializer or a background coroutine, developers can achieve an "instant" UI feel while the heavy lifting occurs asynchronously.4

### **The Cost of Monolithic vs. Polylithic Components**

Hilt utilizes a monolithic component system, meaning a single component definition is used to inject all Activity classes, and another for all Fragment classes.2 This is contrasted with Dagger's traditional polylithic approach (common with @ContributesAndroidInjector), where each Activity has its own unique component definition. The monolithic approach offers several advantages for large apps:

1. **Reduced Generated Code:** Sharing the class definition across all Activities significantly reduces the volume of generated Dagger code, which can become astronomical in large apps with hundreds of screens.2  
2. **Binding Key Space:** It merges the binding key space, making it impossible to have different bindings for the same type based on which Activity a Fragment is attached to. This reduces confusion and trace-ability issues in large codebases.26  
3. **FastInit Support:** Hilt enables fastInit by default, a compilation mode that optimizes the speed of component creation, mitigating the potential startup latency of a large monolithic graph.26

## **Testing Paradigms and Replacement Strategies**

Hilt's primary contribution to testing is the ability to easily swap production modules with fakes or mocks without the manual boilerplate of custom test components.12

### **Hermetic Testing and @TestInstallIn**

The goal of professional testing is hermeticity—ensuring that tests do not rely on external state or non-deterministic services like real network calls. Hilt's @TestInstallIn annotation is the recommended mechanism for global dependency replacement.13 It allows a developer to define a module in the test or androidTest folder that replaces a production module for *all* tests in that source set.12

This approach is highly efficient for build speeds because it allows Hilt to reuse the same generated test components across multiple test classes. In contrast, @UninstallModules, which is used for test-specific overrides, forces Hilt to generate a unique set of components for each test class that uses it, significantly increasing total build time.12

### **Simple Swaps with @BindValue**

For individual tests that require replacing a single dependency, @BindValue provides a streamlined alternative to defining a full nested module.12 By annotating a field in the test class with @BindValue, Hilt automatically incorporates that field's value into the dependency graph for that test. This is particularly useful when using mocks created by libraries like Mockito or MockK.13

When using @BindValue with the ActivityScenarioRule, it is a critical best practice to initialize the field at the point of declaration. Initializing it in a @Before method may be too late, as the Activity may be created and its dependencies injected before the @Before method completes, leading to null pointer exceptions or uninitialized mock errors.13

| Testing Annotation | Use Case | Build Speed Impact | Scope |
| :---- | :---- | :---- | :---- |
| **@TestInstallIn** | Global replacement of production modules 13 | Low (Component reuse) 12 | All tests in source set |
| **@UninstallModules** | Test-specific module exclusion 13 | High (Custom component per test) 13 | Single test class |
| **@BindValue** | Test-specific field binding 13 | High (Custom component per test) 12 | Single test class |
| **@HiltAndroidTest** | Enables Hilt in a test class 13 | Mandatory for Hilt tests | Test class |

## **Advanced Patterns: Assisted Injection**

Assisted Injection addresses the scenario where a class needs a mix of dependencies from the DI graph and parameters that are only available at runtime, such as a user ID from a navigation argument.28

### **The Mechanics of Assisted Injection**

Before Hilt's native support, developers had to write complex manual factories or use third-party libraries. Modern Hilt utilizes three specific annotations to handle this pattern elegantly:

1. **@AssistedInject:** Used on the constructor of the class. It signals to Hilt that this class requires runtime assistance.28  
2. **@Assisted:** Used on the specific constructor parameters that will be provided at runtime.28  
3. **@AssistedFactory:** Used on an interface that acts as the bridge. Hilt generates the implementation of this factory, which the developer then injects into their ViewModels or Activities.28

This pattern is especially vital for WorkManager integration. A Worker needs a Context and WorkerParameters from the system, but it also needs repositories and services from the Hilt graph. By using @HiltWorker and @AssistedInject, developers can maintain a clean, injectable architecture for background tasks without sacrificing the dynamic parameters required by the framework.28

## **Architectural Best Practices for Scalable Development**

The mastery of Dagger and Hilt is not merely about understanding annotations but about applying them within a robust architectural framework. Professional peers should prioritize the following strategic recommendations to ensure long-term maintainability.

### **Strict Visibility and Encapsulation**

The "public by default" tendency in Android modules is a significant source of architectural drift. Developers should aggressively use the internal modifier for implementation classes and use Dagger modules as the only public surface area for dependency provision.22 This prevents other developers from accidentally coupling to internal logic, ensuring that the only way to access a service is through its defined interface in the graph.

### **Measured Scoping and Lifecycle Awareness**

Every scoped binding added to the graph should be justified by a specific technical requirement: either state preservation, synchronization, or prohibitive instantiation cost.1 "Convenience" is not a valid reason for scoping. Furthermore, understanding that Hilt's lifecycle hooks piggyback on the Android ViewModel mechanism is crucial for performance. Hilt's ActivityRetainedComponent is stored inside an ActivityRetainedComponentViewModel, meaning its cleanup logic fires when the Activity is finishing, not just rotating.17 This deep integration ensures that resources are reclaimed at the correct architectural boundary.

### **Performance Profiling and Diagnostic Tools**

Architecture should be data-driven. Developers should utilize the Android Studio Profiler and the Macrobenchmark library to measure the impact of DI on app startup and frame drops.4 If the profiler indicates that Application\#onCreate is dominated by Dagger-related initialization, the first course of action should be the implementation of Lazy\<T\> for heavy dependencies and the narrowing of scopes to remove feature-specific logic from the SingletonComponent.4

In conclusion, Dagger and Hilt represent a mature, highly optimized solution for dependency management on Android. By moving away from monolithic modules, applying narrow and precise scoping, leveraging advanced multi-module patterns, and utilizing modern testing replacement strategies, developers can build applications that are both architecturally sound and performantly superior. The transition to Hilt's opinionated framework provides the standardization necessary for large-scale team collaboration while retaining the raw power and compile-time safety of the underlying Dagger engine.2

#### **Works cited**

1. Dependency injection with Hilt | App architecture \- Android Developers, accessed on May 11, 2026, [https://developer.android.com/training/dependency-injection/hilt-android](https://developer.android.com/training/dependency-injection/hilt-android)  
2. Hilt is stable\! Easier dependency injection on Android \- Manuel Vivo .dev, accessed on May 11, 2026, [https://manuelvivo.dev/hilt-stable](https://manuelvivo.dev/hilt-stable)  
3. Using Dagger in Android apps | App architecture, accessed on May 11, 2026, [https://developer.android.com/training/dependency-injection/dagger-android](https://developer.android.com/training/dependency-injection/dagger-android)  
4. Why Your App Might Be Slower Because of Hilt (And How to Fix It) \- ProAndroidDev, accessed on May 11, 2026, [https://proandroiddev.com/why-your-app-might-be-slower-because-of-hilt-and-how-to-fix-it-a0a3c89a9724](https://proandroiddev.com/why-your-app-might-be-slower-because-of-hilt-and-how-to-fix-it-a0a3c89a9724)  
5. Dagger basics | App architecture \- Android Developers, accessed on May 11, 2026, [https://developer.android.com/training/dependency-injection/dagger-basics](https://developer.android.com/training/dependency-injection/dagger-basics)  
6. Mastering Dagger Hilt in Android: From Beginner to Expert with Real Examples Part I | by Niteshkrjhag | Medium, accessed on May 11, 2026, [https://medium.com/@niteshkrjhag/mastering-dagger-hilt-in-android-from-beginner-to-expert-with-real-examples-part-i-e4153572c96f](https://medium.com/@niteshkrjhag/mastering-dagger-hilt-in-android-from-beginner-to-expert-with-real-examples-part-i-e4153572c96f)  
7. What The Hilt\! A Cheat Sheet For Dependency Injection With Hilt For Android Developers | by Rohit Surthi | Medium, accessed on May 11, 2026, [https://medium.com/@rohitsurthi/what-the-hilt-a-guide-for-dependency-injection-with-hilt-for-android-developers-d2ccfca0b6bc](https://medium.com/@rohitsurthi/what-the-hilt-a-guide-for-dependency-injection-with-hilt-for-android-developers-d2ccfca0b6bc)  
8. Dagger, accessed on May 11, 2026, [https://dagger.dev/dev-guide/](https://dagger.dev/dev-guide/)  
9. Deep Dive with Dagger Customization in Multi-Module Android Applications \- Medium, accessed on May 11, 2026, [https://medium.com/@sharmapraveen91/deep-dive-with-dagger-customization-in-multi-module-android-applications-37eea0789270](https://medium.com/@sharmapraveen91/deep-dive-with-dagger-customization-in-multi-module-android-applications-37eea0789270)  
10. Mastering Dependency Injection with Hilt in Android | by praveen sharma | Medium, accessed on May 11, 2026, [https://medium.com/@sharmapraveen91/mastering-dependency-injection-with-hilt-in-android-0d1f9ee5953c](https://medium.com/@sharmapraveen91/mastering-dependency-injection-with-hilt-in-android-0d1f9ee5953c)  
11. Hilt testing best practices \- MAD Skills \- YouTube, accessed on May 11, 2026, [https://www.youtube.com/watch?v=oBpBWTb3k2g](https://www.youtube.com/watch?v=oBpBWTb3k2g)  
12. Hilt Testing Best Practices in the MAD Skills series | by Eric Chang | Android Developers, accessed on May 11, 2026, [https://medium.com/androiddevelopers/hilt-testing-best-practices-in-the-mad-skills-series-8186a57eee2c](https://medium.com/androiddevelopers/hilt-testing-best-practices-in-the-mad-skills-series-8186a57eee2c)  
13. Testing \- Dagger, accessed on May 11, 2026, [https://dagger.dev/hilt/testing.html](https://dagger.dev/hilt/testing.html)  
14. Inject vs Provides vs Binds in Dagger and Hilt \- Android Blog \- Mobile Dev Notes, accessed on May 11, 2026, [https://www.valueof.io/blog/inject-provides-binds-dependencies-dagger-hilt](https://www.valueof.io/blog/inject-provides-binds-dependencies-dagger-hilt)  
15. What is the use case for @Binds vs @Provides annotation in Dagger2 \- Stack Overflow, accessed on May 11, 2026, [https://stackoverflow.com/questions/52586940/what-is-the-use-case-for-binds-vs-provides-annotation-in-dagger2](https://stackoverflow.com/questions/52586940/what-is-the-use-case-for-binds-vs-provides-annotation-in-dagger2)  
16. Components and Scoping in Hilt \- Android Blog \- Mobile Dev Notes, accessed on May 11, 2026, [https://www.valueof.io/blog/components-scope-dagger-hilt](https://www.valueof.io/blog/components-scope-dagger-hilt)  
17. Android SDK lifecycle management with Hilt dependency injection \- RevenueCat, accessed on May 11, 2026, [https://www.revenuecat.com/blog/engineering/hilt-sdk-lifecycle/](https://www.revenuecat.com/blog/engineering/hilt-sdk-lifecycle/)  
18. Modules \- Dagger, accessed on May 11, 2026, [https://dagger.dev/hilt/modules.html](https://dagger.dev/hilt/modules.html)  
19. Understanding Scopes in Dagger Hilt: A Complete Guide | by Manish Kumar | Medium, accessed on May 11, 2026, [https://medium.com/@manishkumar\_75473/understanding-scopes-in-dagger-hilt-a-complete-guide-c36be1a4fc5b](https://medium.com/@manishkumar_75473/understanding-scopes-in-dagger-hilt-a-complete-guide-c36be1a4fc5b)  
20. Hilt in multi-module apps | App architecture \- Android Developers, accessed on May 11, 2026, [https://developer.android.com/training/dependency-injection/hilt-multi-module](https://developer.android.com/training/dependency-injection/hilt-multi-module)  
21. Guide to Android app modularization | App architecture, accessed on May 11, 2026, [https://developer.android.com/topic/modularization](https://developer.android.com/topic/modularization)  
22. A simple trick to hide internal code from a public Dagger module | by ..., accessed on May 11, 2026, [https://medium.com/@blackgin/a-simple-trick-to-hide-internal-code-from-a-public-dagger-module-91bce95be463](https://medium.com/@blackgin/a-simple-trick-to-hide-internal-code-from-a-public-dagger-module-91bce95be463)  
23. Using Dagger in multi-module apps | App architecture \- Android Developers, accessed on May 11, 2026, [https://developer.android.com/training/dependency-injection/dagger-multi-module](https://developer.android.com/training/dependency-injection/dagger-multi-module)  
24. App startup analysis and optimization | App quality \- Android Developers, accessed on May 11, 2026, [https://developer.android.com/topic/performance/appstartup/analysis-optimization](https://developer.android.com/topic/performance/appstartup/analysis-optimization)  
25. Dagger Core Semantics, accessed on May 11, 2026, [https://dagger.dev/semantics/](https://dagger.dev/semantics/)  
26. Monolithic components \- Dagger, accessed on May 11, 2026, [https://dagger.dev/hilt/monolithic.html](https://dagger.dev/hilt/monolithic.html)  
27. Hilt testing guide | App architecture | Android Developers, accessed on May 11, 2026, [https://developer.android.com/training/dependency-injection/hilt-testing](https://developer.android.com/training/dependency-injection/hilt-testing)  
28. Mastering Assisted Injection in Hilt: A Complete Guide | by Vamsi Vaddavalli | ProAndroidDev, accessed on May 11, 2026, [https://proandroiddev.com/mastering-assisted-injection-in-hilt-a-complete-guide-d95037dd38b1](https://proandroiddev.com/mastering-assisted-injection-in-hilt-a-complete-guide-d95037dd38b1)  
29. Understanding Assisted Injection in Hilt for Android Development | by Reena Rote \- Medium, accessed on May 11, 2026, [https://medium.com/@nachare.reena8/understanding-assisted-injection-in-hilt-for-android-development-b1cd13d20f22](https://medium.com/@nachare.reena8/understanding-assisted-injection-in-hilt-for-android-development-b1cd13d20f22)  
30. Use Hilt with other Jetpack libraries | App architecture \- Android Developers, accessed on May 11, 2026, [https://developer.android.com/training/dependency-injection/hilt-jetpack](https://developer.android.com/training/dependency-injection/hilt-jetpack)