# Dagger & Hilt Expert Skill

Comprehensive expert guidance for Dagger and Hilt dependency injection in Android applications.

## Overview

This skill provides professional-grade guidance for:
- Module organization and architecture
- Scoping strategies and lifecycle management
- Performance optimization and startup latency
- Testing patterns and best practices
- Assisted injection for runtime parameters
- Multi-module setup and configuration

## Structure

```
dagger-hilt-expert/
├── SKILL.md                          # Main skill with quick reference
├── references/                       # Detailed documentation
│   ├── module-organization.md        # Module patterns and multi-module setup
│   ├── scoping-strategies.md         # Component hierarchy and scope selection
│   ├── provides-vs-binds.md          # Performance comparison and usage
│   ├── testing-patterns.md           # Hilt testing strategies
│   ├── performance-optimization.md   # Startup and memory optimization
│   ├── assisted-injection.md         # Runtime parameters and factories
│   └── original-document.md          # Source academic paper
├── scripts/                          # Automation tools
│   ├── analyze_modules.py            # Detect anti-patterns
│   └── generate_module_template.sh   # Generate module boilerplate
└── README.md                         # This file
```

## Quick Start

### Analyze Your Modules
```bash
python scripts/analyze_modules.py app/src/main/java/com/example/di/
```

Detects:
- Monolithic modules
- @Provides that should be @Binds
- Inappropriate @Singleton usage
- Non-static @Provides methods
- Scope/component mismatches

### Generate Module Template
```bash
./scripts/generate_module_template.sh Network SingletonComponent provides
./scripts/generate_module_template.sh Repository SingletonComponent binds
```

## Key Principles

1. **Constructor Injection First**: Prefer `@Inject constructor` over modules
2. **@Binds Over @Provides**: More efficient for interface bindings
3. **Narrow Scoping**: Only scope when necessary
4. **Single-Purpose Modules**: Keep modules focused
5. **Lazy by Default**: Use `Lazy<T>` for non-critical dependencies

## Common Patterns

### Network Module
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides
    @Singleton
    fun provideRetrofit(): Retrofit = ...
}
```

### Repository Binding
```kotlin
@Module
@InstallIn(SingletonComponent::class)
interface RepositoryModule {
    @Binds
    @Singleton
    fun bindUserRepository(impl: UserRepositoryImpl): UserRepository
}
```

### Assisted Injection
```kotlin
class DetailViewModel @AssistedInject constructor(
    private val repository: Repository,
    @Assisted private val itemId: String
) : ViewModel() {
    @AssistedFactory
    interface Factory {
        fun create(itemId: String): DetailViewModel
    }
}
```

## References

Each reference file provides deep dives into specific topics:

- **module-organization.md**: Module patterns, visibility, multi-module architecture
- **scoping-strategies.md**: Component hierarchy, scope selection, lifecycle
- **provides-vs-binds.md**: Performance comparison, when to use each
- **testing-patterns.md**: @TestInstallIn, @BindValue, fakes vs mocks
- **performance-optimization.md**: Lazy injection, startup profiling
- **assisted-injection.md**: Runtime parameters, WorkManager, factories

## Trigger Phrases

This skill activates on:
- "dagger", "hilt", "dependency injection"
- "@Module", "@Inject", "@Provides", "@Binds"
- "@Singleton", "@InstallIn"
- "@HiltAndroidApp", "@AndroidEntryPoint", "@HiltViewModel"
- "@AssistedInject", "@TestInstallIn", "@BindValue"
- "DI setup", "module organization", "scope management"

## Source

Based on comprehensive analysis of official Dagger/Hilt documentation and industry best practices, compiled from 30+ authoritative sources including Android Developer documentation, ProAndroidDev articles, and Dagger.dev guides.

## Usage in Kiro

Once installed, this skill automatically activates when you mention Dagger or Hilt topics. The skill provides:
- Quick reference patterns in SKILL.md
- Detailed documentation in references/
- Automation scripts for analysis and generation
- Decision trees for choosing the right approach

## License

This skill is based on publicly available documentation and best practices. All code examples follow standard Android development patterns.
