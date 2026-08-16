#!/usr/bin/env bash
# Check Gradle files for Koog coordinates and print the smallest dep set.
set -euo pipefail
IFS=$'\n\t'

usage() {
    echo "Usage: check_koog_deps.sh <project-root>" >&2
    exit 2
}

[[ $# -ge 1 ]] || usage
ROOT="${1%/}"
[[ -d "$ROOT" ]] || { echo "Not a directory: $ROOT" >&2; exit 1; }

KOOG_VERSION="${KOOG_VERSION:-1.1.1}"

gradle_files=()
while IFS= read -r f; do
    gradle_files+=("$f")
done < <(find "$ROOT" -type f \( -name 'build.gradle.kts' -o -name 'build.gradle' -o -name 'libs.versions.toml' \) \
    ! -path '*/build/*' ! -path '*/.gradle/*' 2>/dev/null)

if [[ ${#gradle_files[@]} -eq 0 ]]; then
    echo "No Gradle files under $ROOT"
    exit 1
fi

haystack="$(cat "${gradle_files[@]}")"

has() { grep -q "$1" <<<"$haystack"; }

echo "Koog dependency check ($KOOG_VERSION)"
echo "-----------------------------------"

if has 'ai.koog:koog-agents'; then
    echo "OK  koog-agents present"
else
    echo "MISSING  implementation(\"ai.koog:koog-agents:$KOOG_VERSION\")"
fi

if has 'koog-ktor' || has 'io.ktor:ktor-server'; then
    if has 'ai.koog:koog-ktor' || has 'koog-ktor'; then
        echo "OK  koog-ktor (Ktor backend)"
    else
        echo "HINT  Ktor server detected — add implementation(\"ai.koog:koog-ktor:$KOOG_VERSION\")"
    fi
fi

if has 'org.springframework'; then
    if has 'koog-spring'; then
        echo "OK  Spring Koog starter"
    else
        echo "HINT  Spring detected — prefer koog-spring-boot-starter over hand-wired clients"
    fi
fi

if has 'agents-test' || has 'ai.koog:agents-test'; then
    echo "OK  agents-test"
else
    echo "HINT  testImplementation(\"ai.koog:agents-test:$KOOG_VERSION\")"
fi

echo
echo "Smallest sets:"
echo "  CLI/lib:     ai.koog:koog-agents:$KOOG_VERSION"
echo "  Ktor:        + ai.koog:koog-ktor:$KOOG_VERSION"
echo "  Tests:       + ai.koog:agents-test:$KOOG_VERSION"
echo "  MCP (JVM):   + agents-mcp (beta)"
echo "  Additions:   ai.koog:koog-agents-additions:${KOOG_VERSION}-beta  (planners/embeddings)"

if grep -R --include='*.yaml' --include='*.yml' --include='*.conf' --include='*.properties' -n \
    -e 'sk-' -e 'apikey:' "$ROOT" \
    --exclude-dir=build --exclude-dir=.gradle 2>/dev/null \
    | grep -v '${' | grep -q .; then
    echo
    echo "WARN  possible committed API key in config — use \${ENV} placeholders"
fi
