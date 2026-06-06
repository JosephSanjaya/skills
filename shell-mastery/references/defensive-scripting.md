# Defensive Shell Scripting

Write scripts that fail fast, clean up properly, and provide clear error messages.

## Bash Strict Mode

### The Essential Initialization

```bash
#!/bin/bash
set -euo pipefail
IFS=$'\n\t'
```

**Breakdown:**
- `set -e` (errexit) - Exit immediately if any command fails
- `set -u` (nounset) - Treat unset variables as errors
- `set -o pipefail` - Return failure if any command in pipeline fails
- `IFS=$'\n\t'` - Safer word splitting (newline and tab only)

### Understanding Each Flag

#### set -e (errexit)

**Without -e:**
```bash
#!/bin/bash
false  # Returns 1
echo "This still runs"  # Executes despite failure
```

**With -e:**
```bash
#!/bin/bash
set -e
false  # Returns 1
echo "This never runs"  # Script exits at previous line
```

**Exceptions to -e:**
```bash
# These don't trigger exit
if false; then echo "won't print"; fi  # Conditional context
false || echo "fallback"  # Part of || or &&
! false  # Negated command
```

#### set -u (nounset)

**Without -u:**
```bash
#!/bin/bash
echo "Value: $UNDEFINED_VAR"  # Prints "Value: " (empty)
```

**With -u:**
```bash
#!/bin/bash
set -u
echo "Value: $UNDEFINED_VAR"  # Error: UNDEFINED_VAR: unbound variable
```

**Safe parameter expansion:**
```bash
# Provide default value
echo "${VAR:-default}"

# Check if set
if [[ -n "${VAR:-}" ]]; then
    echo "VAR is set to: $VAR"
fi
```

#### set -o pipefail

**Without pipefail:**
```bash
#!/bin/bash
set -e
false | true  # Returns 0 (success from true)
echo "This runs"  # Executes
```

**With pipefail:**
```bash
#!/bin/bash
set -eo pipefail
false | true  # Returns 1 (failure from false)
echo "This never runs"  # Script exits
```

## Trap Handlers for Cleanup

### Basic Trap Pattern

```bash
#!/bin/bash
set -euo pipefail

# Define cleanup function
cleanup() {
    local exit_code=$?
    echo "Cleaning up..."
    rm -f "$TEMP_FILE"
    rm -rf "$TEMP_DIR"
    exit $exit_code
}

# Register trap
trap cleanup EXIT INT TERM

# Script logic
TEMP_FILE=$(mktemp)
TEMP_DIR=$(mktemp -d)

# Do work...
```

### Trap Signals

| Signal | When Triggered | Use Case |
|--------|---------------|----------|
| EXIT | Script exits (any reason) | General cleanup |
| INT | Ctrl+C pressed | User interruption |
| TERM | Kill signal received | Process termination |
| ERR | Command fails (with -e) | Error handling |

### Advanced Trap Example

```bash
#!/bin/bash
set -euo pipefail

# Track resources
declare -a TEMP_FILES=()
declare -a TEMP_DIRS=()
declare -a PIDS=()

cleanup() {
    local exit_code=$?
    
    # Kill background processes
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    
    # Remove temporary files
    for file in "${TEMP_FILES[@]}"; do
        rm -f "$file"
    done
    
    # Remove temporary directories
    for dir in "${TEMP_DIRS[@]}"; do
        rm -rf "$dir"
    done
    
    exit $exit_code
}

trap cleanup EXIT INT TERM

# Create temp file and track it
create_temp_file() {
    local temp_file
    temp_file=$(mktemp)
    TEMP_FILES+=("$temp_file")
    echo "$temp_file"
}

# Usage
my_temp=$(create_temp_file)
echo "data" > "$my_temp"
```

## Input Validation

### Validate Arguments

```bash
#!/bin/bash
set -euo pipefail

# Check argument count
if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <input_file> <output_file>" >&2
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="$2"

# Validate file exists
if [[ ! -f "$INPUT_FILE" ]]; then
    echo "Error: Input file '$INPUT_FILE' not found" >&2
    exit 1
fi

# Validate file is readable
if [[ ! -r "$INPUT_FILE" ]]; then
    echo "Error: Input file '$INPUT_FILE' not readable" >&2
    exit 1
fi

# Validate output directory exists
OUTPUT_DIR=$(dirname "$OUTPUT_FILE")
if [[ ! -d "$OUTPUT_DIR" ]]; then
    echo "Error: Output directory '$OUTPUT_DIR' does not exist" >&2
    exit 1
fi
```

### Validate Environment

```bash
#!/bin/bash
set -euo pipefail

# Check required commands
require_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "Error: Required command '$1' not found" >&2
        exit 1
    fi
}

require_command jq
require_command curl
require_command git

# Check required environment variables
require_env() {
    if [[ -z "${!1:-}" ]]; then
        echo "Error: Required environment variable '$1' not set" >&2
        exit 1
    fi
}

require_env API_KEY
require_env DATABASE_URL
```

## Error Handling Patterns

### Custom Error Messages

```bash
#!/bin/bash
set -euo pipefail

error() {
    echo "ERROR: $*" >&2
    exit 1
}

warn() {
    echo "WARNING: $*" >&2
}

info() {
    echo "INFO: $*"
}

# Usage
[[ -f config.json ]] || error "config.json not found"
info "Starting process..."
warn "Using default timeout"
```

### Try-Catch Pattern

```bash
#!/bin/bash
set -euo pipefail

try() {
    "$@" || return $?
}

catch() {
    local exit_code=$?
    echo "Command failed with exit code $exit_code: $*" >&2
    return $exit_code
}

# Usage
if ! try risky_command arg1 arg2; then
    catch "risky_command failed"
    # Handle error
    exit 1
fi
```

### Retry Logic

```bash
#!/bin/bash
set -euo pipefail

retry() {
    local max_attempts="$1"
    shift
    local attempt=1
    
    until "$@"; do
        if [[ $attempt -ge $max_attempts ]]; then
            echo "Command failed after $max_attempts attempts: $*" >&2
            return 1
        fi
        
        echo "Attempt $attempt failed, retrying..." >&2
        ((attempt++))
        sleep 2
    done
}

# Usage
retry 3 curl -f https://api.example.com/data
```

## Safe File Operations

### Atomic File Writes

```bash
#!/bin/bash
set -euo pipefail

atomic_write() {
    local target_file="$1"
    local temp_file="${target_file}.tmp.$$"
    
    # Write to temp file
    cat > "$temp_file"
    
    # Atomic move
    mv "$temp_file" "$target_file"
}

# Usage
echo "new content" | atomic_write config.txt
```

### Safe Directory Creation

```bash
#!/bin/bash
set -euo pipefail

# Create directory with error checking
mkdir -p /path/to/dir || {
    echo "Failed to create directory" >&2
    exit 1
}

# Create with specific permissions
install -d -m 0755 /path/to/dir
```

### File Locking

```bash
#!/bin/bash
set -euo pipefail

LOCK_FILE="/var/lock/myscript.lock"

# Acquire lock
exec 200>"$LOCK_FILE"
flock -n 200 || {
    echo "Another instance is running" >&2
    exit 1
}

# Cleanup lock on exit
trap 'rm -f "$LOCK_FILE"' EXIT

# Script logic here...
```

## PowerShell Error Handling

### Strict Mode

```powershell
# PowerShell strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
```

### Try-Catch-Finally

```powershell
try {
    # Risky operation
    $content = Get-Content "file.txt" -ErrorAction Stop
    
    # Process content
    $result = Process-Data $content
    
} catch [System.IO.FileNotFoundException] {
    Write-Error "File not found: $_"
    exit 1
    
} catch {
    Write-Error "Unexpected error: $_"
    exit 1
    
} finally {
    # Always runs (cleanup)
    if ($tempFile) {
        Remove-Item $tempFile -ErrorAction SilentlyContinue
    }
}
```

### Parameter Validation

```powershell
function Process-File {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [ValidateScript({Test-Path $_})]
        [string]$Path,
        
        [Parameter(Mandatory=$false)]
        [ValidateRange(1, 100)]
        [int]$Timeout = 30
    )
    
    # Function logic
}
```

## Logging Best Practices

### Structured Logging

```bash
#!/bin/bash
set -euo pipefail

LOG_FILE="/var/log/myscript.log"

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }

# Usage
log_info "Script started"
log_warn "Using default configuration"
log_error "Failed to connect to database"
```

### Redirect All Output

```bash
#!/bin/bash
set -euo pipefail

# Redirect stdout and stderr to log file
exec 1> >(tee -a script.log)
exec 2>&1

echo "This goes to both console and log"
```

## Security Considerations

### Never Use eval on Untrusted Input

```bash
# DANGEROUS - Don't do this
user_input="$1"
eval "$user_input"  # Code injection risk!

# SAFE - Use arrays or functions
commands=("ls" "-la" "/tmp")
"${commands[@]}"
```

### Sanitize Inputs

```bash
#!/bin/bash
set -euo pipefail

sanitize_filename() {
    local filename="$1"
    # Remove dangerous characters
    echo "$filename" | tr -cd '[:alnum:]._-'
}

# Usage
user_file=$(sanitize_filename "$1")
cat "$user_file"
```

### Secure Temporary Files

```bash
#!/bin/bash
set -euo pipefail

# Secure temp file creation
TEMP_FILE=$(mktemp) || {
    echo "Failed to create temp file" >&2
    exit 1
}

# Set restrictive permissions
chmod 600 "$TEMP_FILE"

# Cleanup on exit
trap 'rm -f "$TEMP_FILE"' EXIT
```

## Testing Scripts

### Dry-Run Mode

```bash
#!/bin/bash
set -euo pipefail

DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true ;;
        *) break ;;
    esac
    shift
done

execute() {
    if [[ "$DRY_RUN" == true ]]; then
        echo "[DRY RUN] Would execute: $*"
    else
        "$@"
    fi
}

# Usage
execute rm -rf /important/data
```

### Debug Mode

```bash
#!/bin/bash
set -euo pipefail

DEBUG=${DEBUG:-false}

debug() {
    if [[ "$DEBUG" == true ]]; then
        echo "[DEBUG] $*" >&2
    fi
}

# Usage
debug "Processing file: $filename"

# Run with: DEBUG=true ./script.sh
```

## Checklist

**Every production script should:**
- [ ] Use strict mode (`set -euo pipefail`)
- [ ] Implement trap handlers for cleanup
- [ ] Validate all inputs and arguments
- [ ] Check for required commands/environment
- [ ] Provide clear error messages
- [ ] Log important operations
- [ ] Handle signals gracefully
- [ ] Use atomic operations for file writes
- [ ] Sanitize user inputs
- [ ] Include usage/help message

## Remember

- **Fail fast** - Catch errors early before they cascade
- **Clean up always** - Use trap handlers for resource cleanup
- **Validate everything** - Never trust inputs or environment
- **Log appropriately** - Balance verbosity with usefulness
- **Test failure paths** - Don't just test the happy path
- **Security first** - Sanitize inputs, avoid eval, use secure temp files
