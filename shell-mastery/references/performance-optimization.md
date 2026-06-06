# Shell Performance Optimization

## Profiling Methodology

### Zsh Profiling with zprof

**Setup:**
```bash
# Add to top of .zshrc
zmodload zsh/zprof

# ... your configuration ...

# Add to bottom of .zshrc
zprof
```

**Interpreting output:**
- **self** - Time spent in function itself
- **total** - Time including called functions
- **calls** - Number of invocations

**Target bottlenecks:**
1. Functions with high self-time
2. Functions called many times
3. Synchronous plugin loading

### PowerShell Profiling

```powershell
Measure-Command {
    # Code to profile
    Import-Module MyModule
}

# Profile entire profile load
Measure-Command { . $PROFILE }
```

### Bash Profiling

```bash
# Enable execution tracing with timestamps
PS4='+ $(date "+%s.%N")\011 '
exec 3>&2 2>/tmp/bashstart.$$.log
set -x

# ... your .bashrc ...

set +x
exec 2>&3 3>&-
```

## Common Bottlenecks

### 1. NVM/RVM Initialization

**Problem:** Loading node version managers adds 200-500ms

**Solution - Lazy Loading:**
```bash
# Don't load NVM immediately
export NVM_DIR="$HOME/.nvm"

# Create wrapper function
nvm() {
    unset -f nvm node npm
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    nvm "$@"
}

node() {
    unset -f nvm node npm
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    node "$@"
}

npm() {
    unset -f nvm node npm
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    npm "$@"
}
```

### 2. Zsh Completion System (compinit)

**Problem:** `compinit` rescans all completion files

**Solution - Cache completions:**
```bash
# Only regenerate once per day
autoload -Uz compinit
if [[ -n ${ZDOTDIR}/.zcompdump(#qN.mh+24) ]]; then
    compinit
else
    compinit -C
fi
```

### 3. Plugin Managers (Oh My Zsh, Antigen)

**Problem:** Synchronous loading, heavy frameworks

**Solution - Switch to Zinit:**
```bash
# Zinit with turbo mode (async loading)
zinit ice wait lucid
zinit light zsh-users/zsh-autosuggestions

zinit ice wait lucid
zinit light zsh-users/zsh-syntax-highlighting

# Load after prompt
zinit ice wait'1' lucid
zinit light zsh-users/zsh-completions
```

### 4. Conda/Pyenv Initialization

**Problem:** Python environment managers slow startup

**Solution - Conditional loading:**
```bash
# Only initialize when needed
if [[ -n $CONDA_REQUIRED ]]; then
    eval "$(conda shell.zsh hook)"
fi

# Or lazy-load
conda() {
    unset -f conda
    eval "$(command conda shell.zsh hook)"
    conda "$@"
}
```

## Optimization Strategies

### Async Loading Pattern

**Zsh with Zinit:**
```bash
# Load immediately (critical)
zinit light zsh-users/zsh-history-substring-search

# Load after prompt (non-critical)
zinit ice wait lucid
zinit light zdharma-continuum/fast-syntax-highlighting

# Load 1 second after prompt
zinit ice wait'1' lucid
zinit light zsh-users/zsh-completions
```

### Minimize Process Forks

**Bad - External commands:**
```bash
# Each call forks a new process
result=$(cat file.txt | grep pattern | wc -l)
```

**Good - Built-in features:**
```bash
# Use shell built-ins
result=$(grep -c pattern file.txt)

# Or pure shell
count=0
while IFS= read -r line; do
    [[ $line == *pattern* ]] && ((count++))
done < file.txt
```

### PowerShell Performance Hierarchy

**1. Language Features (Fastest):**
```powershell
# Direct language constructs
foreach ($item in $collection) {
    # Process
}

if ($condition) {
    # Execute
}
```

**2. .NET Methods (Fast):**
```powershell
# Direct .NET calls
[Math]::Sqrt($number)
[System.IO.File]::ReadAllLines($path)
```

**3. Cmdlets (Slower):**
```powershell
# PowerShell cmdlets
Get-Content $path
Where-Object { $_.Property -eq $value }
```

**Optimization example:**
```powershell
# Slow - cmdlet for large files
$content = Get-Content large.txt

# Fast - .NET streaming
$content = [System.IO.File]::ReadLines($path)
```

## Parallel Execution

### PowerShell Parallel Strategies

**ForEach-Object -Parallel (Best for most cases):**
```powershell
1..100 | ForEach-Object -Parallel {
    # Runs in runspace pool
    Start-Sleep -Seconds 1
    "Processed $_"
} -ThrottleLimit 10
```

**Start-ThreadJob (In-process threads):**
```powershell
$jobs = 1..10 | ForEach-Object {
    Start-ThreadJob -ScriptBlock {
        param($num)
        # Process in thread
        Start-Sleep -Seconds 1
        $num * 2
    } -ArgumentList $_
}

$results = $jobs | Wait-Job | Receive-Job
$jobs | Remove-Job
```

**Avoid Start-Job (Heavy out-of-process):**
```powershell
# DON'T - Creates new PowerShell process
Start-Job -ScriptBlock { ... }  # 8x slower than ThreadJob
```

### Bash Parallel Execution

**GNU Parallel:**
```bash
# Process files in parallel
find . -name "*.txt" | parallel gzip

# With custom function
export -f process_file
find . -name "*.log" | parallel process_file
```

**Background jobs:**
```bash
# Simple parallelization
for file in *.txt; do
    process_file "$file" &
done
wait  # Wait for all background jobs
```

## Benchmarking

### Zsh Startup Time

**Target: < 0.5 seconds**

```bash
# Measure 10 runs
for i in {1..10}; do
    time zsh -i -c exit
done
```

### PowerShell Startup Time

```powershell
# Measure profile load
Measure-Command { pwsh -NoProfile -Command "exit" }
Measure-Command { pwsh -Command "exit" }
```

### Script Execution Time

**Bash:**
```bash
time ./script.sh

# With detailed breakdown
/usr/bin/time -v ./script.sh
```

**PowerShell:**
```powershell
Measure-Command { ./script.ps1 } | Select-Object TotalMilliseconds
```

## Optimization Checklist

**Zsh:**
- [ ] Profile with `zprof`
- [ ] Lazy-load NVM/RVM/Conda
- [ ] Cache `compinit` results
- [ ] Use async plugin loading (Zinit)
- [ ] Remove unused plugins
- [ ] Minimize prompt complexity
- [ ] Target < 0.5s startup

**Bash:**
- [ ] Minimize external command calls
- [ ] Use shell built-ins
- [ ] Avoid unnecessary subshells
- [ ] Cache expensive operations
- [ ] Profile with execution tracing

**PowerShell:**
- [ ] Profile with `Measure-Command`
- [ ] Use .NET methods for heavy operations
- [ ] Prefer ThreadJobs over Jobs
- [ ] Minimize module imports
- [ ] Use parallel execution for I/O-bound tasks
- [ ] Avoid XML serialization overhead

## Real-World Optimization Examples

### Example 1: Zsh from 640ms to 120ms (81% improvement)

**Before:**
```bash
# Oh My Zsh with many plugins
plugins=(git docker kubectl npm)
source $ZSH/oh-my-zsh.sh
```

**After:**
```bash
# Zinit with async loading
zinit ice wait lucid
zinit snippet OMZ::plugins/git/git.plugin.zsh

zinit ice wait lucid
zinit snippet OMZ::plugins/docker/docker.plugin.zsh
```

### Example 2: PowerShell File Processing

**Before (Slow):**
```powershell
Get-Content large.txt | ForEach-Object {
    # Process line by line
}
```

**After (Fast):**
```powershell
[System.IO.File]::ReadLines("large.txt") | ForEach-Object {
    # Streaming, no full load
}
```

### Example 3: Bash Script Optimization

**Before:**
```bash
for file in $(ls *.txt); do
    lines=$(cat "$file" | wc -l)
    echo "$file: $lines"
done
```

**After:**
```bash
for file in *.txt; do
    lines=$(wc -l < "$file")
    echo "$file: $lines"
done
```

## Monitoring and Maintenance

**Regular checks:**
1. Profile startup monthly
2. Review new plugins/modules
3. Update tools (fzf, ripgrep, etc.)
4. Clean up unused configurations
5. Benchmark critical scripts

**Performance regression detection:**
```bash
# Save baseline
time zsh -i -c exit 2>&1 | tee baseline.txt

# Compare after changes
time zsh -i -c exit 2>&1 | tee current.txt
diff baseline.txt current.txt
```

## Remember

- **Measure, don't guess** - Always profile before optimizing
- **Async is your friend** - Load non-critical components after prompt
- **Built-ins beat externals** - Minimize process forks
- **Cache expensive operations** - Don't recompute on every shell start
- **Parallel when I/O-bound** - Use threads/jobs for network/disk operations
