#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path

PROJECT_EXTENSIONS_CONTENT = """package my.architecture.convention

import org.gradle.api.Project
import org.gradle.api.artifacts.VersionCatalog
import org.gradle.api.artifacts.VersionCatalogsExtension
import org.gradle.kotlin.dsl.getByType

val Project.libs: VersionCatalog
    get() = extensions.getByType<VersionCatalogsExtension>().named("libs")

fun Project.findLibrary(alias: String): Any {
    return libs.findLibrary(alias).orElseThrow {
        NoSuchElementException("Dependency alias '$alias' was not declared in libs.versions.toml")
    }
}
"""

SETTINGS_GRADLE_CONTENT = """pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    versionCatalogs {
        create("libs") {
            from(files("../gradle/libs.versions.toml"))
        }
    }
}

rootProject.name = "build-logic"
include(":convention")
"""

CONVENTION_BUILD_CONTENT = """plugins {
    `kotlin-dsl`
}

group = "my.architecture.convention"

dependencies {
    compileOnly(libs.android.gradle.plugin)
    compileOnly(libs.kotlin.gradle.plugin)
}
"""

STARTER_PLUGIN_CONTENT = """import my.architecture.convention.findLibrary

plugins {
    id("com.android.library")
    // NOTE: Since AGP 9.0, built-in Kotlin is enabled by default.
    // Do NOT apply 'org.jetbrains.kotlin.android' here as it will conflict.
    // Apply it ONLY if you are running on legacy AGP 8.x.
    // id("org.jetbrains.kotlin.android")
}

android {
    compileSdk = 35

    defaultConfig {
        minSdk = 26
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    implementation(findLibrary("androidx-core-ktx"))
}
"""

def scaffold(project_path: Path):
    print(f"Scaffolding composite build-logic structure at: {project_path.resolve()}")
    
    # 1. Validate root project
    root_settings = project_path / "settings.gradle.kts"
    if not root_settings.exists():
        root_settings = project_path / "settings.gradle"
        if not root_settings.exists():
            print(f"[ERROR] Target directory is not a Gradle root project (no settings.gradle[.kts] found).", file=sys.stderr)
            sys.exit(1)
            
    # 2. Check if build-logic already exists
    build_logic_dir = project_path / "build-logic"
    if build_logic_dir.exists():
        print(f"[ERROR] build-logic directory already exists. Scaffolding aborted to protect existing configs.", file=sys.stderr)
        sys.exit(1)
        
    # 3. Create directories
    convention_kotlin_dir = build_logic_dir / "convention" / "src" / "main" / "kotlin"
    convention_kotlin_dir.mkdir(parents=True, exist_ok=True)
    
    # Helper package directory my/architecture/convention
    pkg_dir = convention_kotlin_dir / "my" / "architecture" / "convention"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    
    # 4. Write settings.gradle.kts
    (build_logic_dir / "settings.gradle.kts").write_text(SETTINGS_GRADLE_CONTENT)
    print("[OK] Created build-logic/settings.gradle.kts")
    
    # 5. Write build.gradle.kts for convention subproject
    (build_logic_dir / "convention" / "build.gradle.kts").write_text(CONVENTION_BUILD_CONTENT)
    print("[OK] Created build-logic/convention/build.gradle.kts")
    
    # 6. Write ProjectExtensions.kt
    (pkg_dir / "ProjectExtensions.kt").write_text(PROJECT_EXTENSIONS_CONTENT)
    print("[OK] Created build-logic/convention/.../ProjectExtensions.kt")
    
    # 7. Write starter convention plugin
    (convention_kotlin_dir / "my.android.library.gradle.kts").write_text(STARTER_PLUGIN_CONTENT)
    print("[OK] Created build-logic/convention/.../my.android.library.gradle.kts")
    
    # 8. Wire into root settings
    settings_text = root_settings.read_text()
    if "includeBuild(\"build-logic\")" not in settings_text and "includeBuild('build-logic')" not in settings_text:
        # Append includeBuild at the start of pluginManagement or root settings block
        wire_str = '\npluginManagement {\n    includeBuild("build-logic")\n}\n'
        if "pluginManagement {" in settings_text:
            settings_text = settings_text.replace("pluginManagement {", 'pluginManagement {\n    includeBuild("build-logic")')
        else:
            settings_text = wire_str + settings_text
        root_settings.write_text(settings_text)
        print(f"[OK] Wired build-logic into root settings file: {root_settings.name}")
    else:
        print("[INFO] build-logic already wired into root settings.")

    print("\n[SUCCESS] build-logic composite setup scaffolded successfully!")
    print("Next steps:")
    print("1. In your root gradle/libs.versions.toml, ensure you have declared:")
    print("   [plugins]")
    print("   android-gradle-plugin = { id = \"com.android.library\", version = \"9.x.x\" }")
    print("   # (Note: kotlin-gradle-plugin is only required for legacy AGP 8.x environments)")
    print("   kotlin-gradle-plugin = { id = \"org.jetbrains.kotlin.android\", version = \"2.x.x\" }")
    print("   [libraries]")
    print("   androidx-core-ktx = { group = \"androidx.core\", name = \"core-ktx\", version = \"1.12.0\" }")

def main():
    parser = argparse.ArgumentParser(description="Scaffold a composite build-logic layout for Gradle Convention Plugins.")
    parser.add_argument("project_path", nargs="?", default=".", help="Path to the Gradle root project (default: current directory)")
    args = parser.parse_args()
    
    scaffold(Path(args.project_path))

if __name__ == "__main__":
    main()
