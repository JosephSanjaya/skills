# Writing Portable Shell Scripts

Write scripts that work across Unix-like systems: Linux (GNU), macOS (BSD), Alpine (ash), and minimal containers.

## POSIX Compliance

### The POSIX Shebang

```bash
#!/bin/sh
# NOT #!/bin/bash - signals POSIX compliance
```

### Why POSIX Matters

**Environments requiring POSIX:**
- Alpine Linux containers (uses ash, not bash)
- Minimal Docker images
- Embedded systems
- macOS (older bash, defaults to zsh)
- CI/CD environments
- Cross-platform scripts

## Bashisms to Avoid

### Testing and Conditionals

| Bashism | POSIX Equivalent |
|---------|------------------|
| `[[ "$x" == "y" ]]` | `[ "$x" = "y" ]` |
| `[[ "$x" != "y" ]]` | `[ "$x" != "y" ]` |
| `[[ -z "$x" ]]` | `[ -z "$x" ]` |
| `[[ "$x" =~ regex ]]` | `echo "$x" \| grep -E "regex"` |
| `[[ "$x" < "$y" ]]` | `[ "$x" \< "$y" ]` (escape needed) |

**Example:**
```bash
# Bashism
if [[ "$name" == "admin" ]]; then
    echo "Admin user"
fi

# POSIX
if [ "$name" = "admin" ]; then
    echo "Admin user"
fi
```

### String Operations

| Bashism | POSIX Equivalent |
|---------|------------------|
| `${var//old/new}` | `echo "$var" \| sed 's/old/new/g'` |
| `${var^^}` | `echo "$var" \| tr '[:lower:]' '[:upper:]'` |
| `${var,,}` | `echo "$var" \| tr '[:upper:]' '[:lower:]'` |
| `${var:0:5}` | `echo "$var" \| cut -c1-5` |

**Example:**
```bash
# Bashism
text="hello world"
upper="${text^^}"

# POSIX
text="hello world"
upper=$(echo "$text" | tr '[:lower:]' '[:upper:]')
```

### Arrays

**Bashism:**
```bash
# Arrays are NOT POSIX
items=("apple" "banana" "cherry")
echo "${items[0]}"
```

**POSIX alternatives:**

**Option 1: Positional parameters**
```bash
set -- "apple" "banana" "cherry"
echo "$1"  # apple

for item in "$@"; do
    echo "$item"
done
```

**Option 2: Newline-separated string**
```bash
items="apple
banana
cherry"

echo "$items" | while IFS= read -r item; do
    echo "$item"
done
```

**Option 3: Space-separated (careful with spaces in values)**
```bash
items="apple banana cherry"

for item in $items; do
    echo "$item"
done
```

### Arithmetic

| Bashism | POSIX Equivalent |
|---------|------------------|
| `(( count++ ))` | `count=$((count + 1))` |
| `(( count += 5 ))` | `count=$((count + 5))` |
| `let "x = 5"` | `x=$((5))` |

**Example:**
```bash
# Bashism
count=0
(( count++ ))

# POSIX
count=0
count=$((count + 1))
```

### Sourcing Files

| Bashism | POSIX Equivalent |
|---------|------------------|
| `source ./config.sh` | `. ./config.sh` |

**Example:**
```bash
# Bashism
source ./config.sh

# POSIX
. ./config.sh
```

### Command Checking

| Bashism | POSIX Equivalent |
|---------|------------------|
| `which git` | `command -v git` |
| `type -P git` | `command -v git` |

**Example:**
```bash
# Bashism (not portable)
if which git > /dev/null 2>&1; then
    echo "Git found"
fi

# POSIX
if command -v git > /dev/null 2>&1; then
    echo "Git found"
fi
```

### Process Substitution

**Bashism:**
```bash
# NOT POSIX
diff <(sort file1.txt) <(sort file2.txt)
```

**POSIX:**
```bash
# Use temporary files
temp1=$(mktemp)
temp2=$(mktemp)
trap 'rm -f "$temp1" "$temp2"' EXIT

sort file1.txt > "$temp1"
sort file2.txt > "$temp2"
diff "$temp1" "$temp2"
```

### Here Strings

**Bashism:**
```bash
# NOT POSIX
grep pattern <<< "$variable"
```

**POSIX:**
```bash
# Use echo or printf
echo "$variable" | grep pattern

# Or here document
grep pattern << EOF
$variable
EOF
```

## Portable Argument Parsing

### Using getopts (POSIX)

```bash
#!/bin/sh

usage() {
    echo "Usage: $0 [-v] [-f file] [-o output]" >&2
    exit 1
}

VERBOSE=0
INPUT_FILE=""
OUTPUT_FILE=""

while getopts "vf:o:h" opt; do
    case "$opt" in
        v) VERBOSE=1 ;;
        f) INPUT_FILE="$OPTARG" ;;
        o) OUTPUT_FILE="$OPTARG" ;;
        h) usage ;;
        *) usage ;;
    esac
done

shift $((OPTIND - 1))

# Remaining arguments in "$@"
```

### Manual Parsing (Long Options)

```bash
#!/bin/sh

while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=1
            ;;
        -f|--file)
            INPUT_FILE="$2"
            shift
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift
            ;;
        --)
            shift
            break
            ;;
        -*)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
        *)
            break
            ;;
    esac
    shift
done
```

## Platform-Specific Differences

### GNU vs BSD Commands

| Command | GNU (Linux) | BSD (macOS) | Portable Solution |
|---------|-------------|-------------|-------------------|
| `sed -i` | `sed -i 's/old/new/' file` | `sed -i '' 's/old/new/' file` | Use temp file |
| `date` | `date -d "yesterday"` | `date -v-1d` | Use `date +%s` |
| `stat` | `stat -c %s file` | `stat -f %z file` | Use `wc -c < file` |
| `readlink` | `readlink -f path` | `readlink path` | Use `pwd -P` |

### Portable sed -i

```bash
#!/bin/sh

# NOT portable
sed -i 's/old/new/' file.txt

# Portable
sed 's/old/new/' file.txt > file.txt.tmp
mv file.txt.tmp file.txt

# Or use a function
portable_sed_i() {
    local pattern="$1"
    local file="$2"
    sed "$pattern" "$file" > "${file}.tmp"
    mv "${file}.tmp" "$file"
}

portable_sed_i 's/old/new/' file.txt
```

### Portable Date Operations

```bash
#!/bin/sh

# Get current timestamp (portable)
timestamp=$(date +%s)

# Get yesterday (NOT portable)
# GNU: date -d "yesterday"
# BSD: date -v-1d

# Portable: Use arithmetic
yesterday=$(($(date +%s) - 86400))
date -d "@$yesterday" 2>/dev/null || date -r "$yesterday"
```

### Portable File Size

```bash
#!/bin/sh

# NOT portable
# GNU: stat -c %s file
# BSD: stat -f %z file

# Portable
file_size=$(wc -c < file.txt | tr -d ' ')
```

## Testing for Portability

### Use shellcheck

```bash
# Install shellcheck
# macOS: brew install shellcheck
# Linux: apt-get install shellcheck

# Check script
shellcheck --shell=sh script.sh

# Check for POSIX compliance
shellcheck --shell=sh --severity=warning script.sh
```

### Test on Multiple Shells

```bash
# Test with different shells
sh script.sh      # POSIX sh
dash script.sh    # Debian Almquist Shell
ash script.sh     # Alpine Shell
bash script.sh    # Bash (should still work)
```

### Docker Testing

```bash
# Test on Alpine (ash)
docker run --rm -v "$PWD:/scripts" alpine:latest sh /scripts/script.sh

# Test on Ubuntu (dash)
docker run --rm -v "$PWD:/scripts" ubuntu:latest sh /scripts/script.sh

# Test on Debian
docker run --rm -v "$PWD:/scripts" debian:latest sh /scripts/script.sh
```

## Portable Script Template

```bash
#!/bin/sh
# Portable POSIX shell script template

set -eu  # Note: no pipefail in POSIX

# Cleanup trap
cleanup() {
    exit_code=$?
    # Cleanup logic
    rm -f "$temp_file"
    exit "$exit_code"
}

trap cleanup EXIT INT TERM

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS] <argument>

OPTIONS:
    -h, --help      Show this help message
    -v, --verbose   Enable verbose output
    -f, --file      Input file

EXAMPLES:
    $0 -f input.txt
    $0 --verbose input.txt
EOF
    exit 1
}

# Default values
VERBOSE=0
INPUT_FILE=""

# Parse arguments
while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help)
            usage
            ;;
        -v|--verbose)
            VERBOSE=1
            ;;
        -f|--file)
            INPUT_FILE="$2"
            shift
            ;;
        -*)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
        *)
            break
            ;;
    esac
    shift
done

# Validate required arguments
if [ -z "$INPUT_FILE" ]; then
    echo "Error: Input file required" >&2
    usage
fi

# Check file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File not found: $INPUT_FILE" >&2
    exit 1
fi

# Create temp file
temp_file=$(mktemp)

# Main logic
if [ "$VERBOSE" -eq 1 ]; then
    echo "Processing $INPUT_FILE..."
fi

# Process file
while IFS= read -r line; do
    # Process each line
    echo "$line"
done < "$INPUT_FILE"

# Success
exit 0
```

## Common Pitfalls

### 1. Unquoted Variables

```bash
# WRONG - word splitting issues
if [ $var = "value" ]; then
    echo "match"
fi

# CORRECT - always quote
if [ "$var" = "value" ]; then
    echo "match"
fi
```

### 2. Using == Instead of =

```bash
# WRONG - == is Bashism
[ "$x" == "y" ]

# CORRECT - use single =
[ "$x" = "y" ]
```

### 3. Using [[ ]] Instead of [ ]

```bash
# WRONG - [[ ]] is Bashism
if [[ -f "$file" ]]; then
    echo "exists"
fi

# CORRECT - use [ ]
if [ -f "$file" ]; then
    echo "exists"
fi
```

### 4. Using $() Without Quotes

```bash
# WRONG - word splitting
files=$(ls *.txt)
for file in $files; do
    echo "$file"
done

# CORRECT - quote or use glob
for file in *.txt; do
    echo "$file"
done
```

### 5. Using echo for Arbitrary Strings

```bash
# WRONG - echo interprets backslashes
echo "$user_input"

# CORRECT - printf is more portable
printf '%s\n' "$user_input"
```

## Portability Checklist

**Before deploying:**
- [ ] Use `#!/bin/sh` shebang
- [ ] Run `shellcheck --shell=sh`
- [ ] Test on Alpine Linux (ash)
- [ ] Test on macOS (if targeting)
- [ ] Avoid `[[` - use `[`
- [ ] Avoid arrays - use positional parameters
- [ ] Use `=` not `==` in tests
- [ ] Use `. file` not `source file`
- [ ] Use `command -v` not `which`
- [ ] Quote all variable expansions
- [ ] Use `printf` instead of `echo` for variables
- [ ] Avoid GNU-specific flags (sed -i, date -d)
- [ ] Test with `set -u` to catch unset variables

## When to Break POSIX

**Use Bash when:**
- Script only runs on systems with Bash
- Need arrays for complex data structures
- Performance requires Bash features
- Readability significantly improves with Bashisms

**If using Bash, be explicit:**
```bash
#!/bin/bash
# This script requires Bash 4.0+

if [ -z "$BASH_VERSION" ]; then
    echo "This script requires Bash" >&2
    exit 1
fi

if [ "${BASH_VERSINFO[0]}" -lt 4 ]; then
    echo "This script requires Bash 4.0+" >&2
    exit 1
fi
```

## Remember

- **POSIX = Maximum portability** - Works everywhere
- **Test on target platforms** - Don't assume compatibility
- **shellcheck is your friend** - Catches most issues
- **Quote everything** - Prevent word splitting
- **Use [ ] not [[ ]]** - POSIX compliance
- **Avoid arrays** - Use positional parameters or loops
- **Document requirements** - If Bash-only, say so clearly
