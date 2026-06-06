#!/bin/bash
# Submodule updater and symlink re-installer using defensive shell-mastery guidelines

# Exit immediately on error, treat unset variables as errors, fail-fast in pipelines
set -euo pipefail

echo "=== Antigravity Submodule Updater & Symlink Installer ==="

# Check for git
if ! command -v git &> /dev/null; then
    echo "Error: git is not installed or not in your PATH." >&2
    exit 1
fi

# Locate current script directory robustly
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Updating git submodules..."
git submodule update --init --recursive --remote

# Retrigger the install script, forwarding any arguments (like --dry-run or --clean)
echo "Retriggering symlink installation..."
exec "$SCRIPT_DIR/install.sh" "$@"
