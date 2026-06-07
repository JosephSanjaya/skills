#!/bin/bash
# Generate Dagger/Hilt module templates
# Usage: ./generate_module_template.sh <module_name> <component> <type>
# Example: ./generate_module_template.sh Network SingletonComponent provides
# Example: ./generate_module_template.sh Repository SingletonComponent binds

set -e

MODULE_NAME=$1
COMPONENT=$2
TYPE=$3

if [ -z "$MODULE_NAME" ] || [ -z "$COMPONENT" ] || [ -z "$TYPE" ]; then
    echo "Usage: $0 <module_name> <component> <type>"
    echo ""
    echo "Components:"
    echo "  SingletonComponent"
    echo "  ActivityRetainedComponent"
    echo "  ViewModelComponent"
    echo "  ActivityComponent"
    echo "  FragmentComponent"
    echo ""
    echo "Types:"
    echo "  provides  - Generate @Provides template"
    echo "  binds     - Generate @Binds template"
    echo ""
    echo "Examples:"
    echo "  $0 Network SingletonComponent provides"
    echo "  $0 Repository SingletonComponent binds"
    exit 1
fi

# Determine scope annotation based on component
SCOPE=""
case $COMPONENT in
    SingletonComponent)
        SCOPE="@Singleton"
        ;;
    ActivityRetainedComponent)
        SCOPE="@ActivityRetainedScoped"
        ;;
    ViewModelComponent)
        SCOPE="@ViewModelScoped"
        ;;
    ActivityComponent)
        SCOPE="@ActivityScoped"
        ;;
    FragmentComponent)
        SCOPE="@FragmentScoped"
        ;;
    *)
        echo "Unknown component: $COMPONENT"
        exit 1
        ;;
esac

FILENAME="${MODULE_NAME}Module.kt"

if [ "$TYPE" = "provides" ]; then
    cat > "$FILENAME" << EOF
package com.example.di

import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.${COMPONENT}
import javax.inject.Singleton

/**
 * Dagger module for ${MODULE_NAME} dependencies.
 * 
 * Use @Provides for:
 * - Third-party library classes
 * - Complex initialization logic
 * - Conditional dependency creation
 */
@Module
@InstallIn(${COMPONENT}::class)
object ${MODULE_NAME}Module {
    
    /**
     * Provides [YourDependency].
     * 
     * @param dependency Injected dependency from graph
     * @return Configured instance
     */
    @Provides
    ${SCOPE}
    fun provideYourDependency(
        dependency: SomeDependency
    ): YourDependency {
        return YourDependencyImpl(dependency)
    }
    
    // Add more @Provides methods here
    // Keep module focused on single responsibility
}
EOF

elif [ "$TYPE" = "binds" ]; then
    cat > "$FILENAME" << EOF
package com.example.di

import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.${COMPONENT}
import javax.inject.Singleton

/**
 * Dagger module for ${MODULE_NAME} bindings.
 * 
 * Use @Binds for:
 * - Interface to implementation mapping
 * - When implementation has @Inject constructor
 * - Better performance than @Provides
 */
@Module
@InstallIn(${COMPONENT}::class)
interface ${MODULE_NAME}Module {
    
    /**
     * Binds [YourInterface] to [YourImplementation].
     * 
     * Implementation must have @Inject constructor.
     */
    @Binds
    ${SCOPE}
    fun bindYourInterface(
        implementation: YourImplementation
    ): YourInterface
    
    // Add more @Binds methods here
    // All methods must be abstract
}
EOF

else
    echo "Unknown type: $TYPE"
    echo "Use 'provides' or 'binds'"
    exit 1
fi

echo "✅ Generated $FILENAME"
echo ""
echo "Next steps:"
echo "1. Update package name"
echo "2. Replace placeholder types (YourDependency, YourInterface, etc.)"
echo "3. Add actual dependencies"
echo "4. Ensure implementation classes have @Inject constructor (for @Binds)"
echo ""
echo "Remember:"
echo "- Keep modules small and focused"
echo "- Use @Binds when possible (more efficient)"
echo "- Only scope when necessary (state, expensive creation, sync)"
