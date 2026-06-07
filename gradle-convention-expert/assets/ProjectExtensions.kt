package my.architecture.convention

import org.gradle.api.Project
import org.gradle.api.artifacts.VersionCatalog
import org.gradle.api.artifacts.VersionCatalogsExtension
import org.gradle.kotlin.dsl.getByType

/**
 * Safely fetches the shared "libs" Version Catalog.
 */
val Project.libs: VersionCatalog
    get() = extensions.getByType<VersionCatalogsExtension>().named("libs")

/**
 * Resolves a library coordinate from the catalog via its alias.
 */
fun Project.findLibrary(alias: String): Any {
    return libs.findLibrary(alias).orElseThrow {
        NoSuchElementException("Dependency alias '$alias' was not declared in libs.versions.toml")
    }
}
