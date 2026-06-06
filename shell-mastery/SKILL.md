---
name: shell-mastery
description: Expert shell configuration, optimization, and automation for Bash, Zsh, and PowerShell. Use when optimizing shell startup times, profiling performance bottlenecks, implementing defensive scripting patterns, configuring modern CLI tools (fzf, tmux, Atuin), writing portable POSIX scripts, engineering Zsh interactive environments, implementing PowerShell parallel execution, or troubleshooting shell performance issues. Applies to shell configuration files (.bashrc, .zshrc, PowerShell profiles), automation scripts, and terminal productivity workflows.
---

<instructions>
Optimize shell configurations and scripts to meet strict performance and defensive targets.

## Shell Selection & Performance

| Use Case | Shell | Key Choice Reason |
|----------|-------|--------------------|
| System Automation | Bash | Universal container/VM compatibility |
| Interactive Dev | Zsh | Native macOS shell, rich completions |
| Windows/Cloud | PowerShell | Object pipeline, native .NET APIs |

- **Interactive Startup Target**: 0.1s - 0.5s. Profile slow shells with Zsh `zprof` or PowerShell `Measure-Command`.
- **Fuzzy Search Latency**: <50ms using `fzf` or `Atuin`.
</instructions>

<rules>
## Core Scripting & Config Snippets

### 1. Defensive Bash (Fail-Fast)
```bash
#!/bin/bash
set -euo pipefail
trap cleanup EXIT INT TERM
cleanup() { rm -f "$TEMP_FILE"; }
```

### 2. Portable Argument Parsing (POSIX)
```bash
while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help) show_help; exit 0 ;;
        -v|--verbose) VERBOSE=1 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
    shift
done
```

### 3. Zsh Lazy-Loading & Async Plugins
```bash
# Lazy-load NVM
nvm() { unset -f nvm node npm; [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"; nvm "$@"; }

# Async plugins via Zinit
zinit ice wait lucid
zinit light zsh-users/zsh-autosuggestions
```

### 4. PowerShell Parallelism
```powershell
1..100 | ForEach-Object -Parallel { # Parallel work } -ThrottleLimit 10
```
</rules>

<references>
## Deep-Dive Reference Manuals

- Read [performance-optimization.md](references/performance-optimization.md) to diagnose slow shells, lazy-load SDKs, or profile startup latency.
- Read [defensive-scripting.md](references/defensive-scripting.md) when writing production scripts requiring signal traps, file locking, or strict error checking.
- Read [portability.md](references/portability.md) to rewrite Bashisms into POSIX-compliant syntax for Alpine/minimal containers.
- Read [modern-toolkit.md](references/modern-toolkit.md) to configure fzf, tmux, Atuin, ripgrep, bat, or eza aliases.
- Read [zsh-optimization.md](references/zsh-optimization.md) to customize ZLE widgets, completion styles, or advanced glob qualifiers.
- Read [powershell-patterns.md](references/powershell-patterns.md) for object-oriented pipelines, ThreadJobs, and secure credential handling.
</references>

<constraints>
- Scripts MUST use defensive patterns (`set -euo pipefail`) to fail fast.
- Non-critical plugins and SDK initializers (e.g. NVM, Conda) SHOULD be lazy-loaded.
- Always verify shell compatibility (POSIX vs Bash/Zsh specific features) before execution.
</constraints>

