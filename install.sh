#!/bin/bash
# Install script for macOS and Linux using defensive shell-mastery guidelines

# Exit immediately if a command exits with a non-zero status,
# treat unset variables as an error, and prevent errors in pipeline masks.
set -euo pipefail

echo "=== Antigravity Skill Symlinker Installer (macOS/Linux) ==="

# Check for python3
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed or not in your PATH." >&2
    echo "Please install Python 3 and try again." >&2
    exit 1
fi

# Locate current script directory robustly (defensive path resolution)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Make the python script executable
chmod +x "$SCRIPT_DIR/link_skills.py"

# Execute the python script, forwarding all arguments
exec python3 "$SCRIPT_DIR/link_skills.py" "$@"
