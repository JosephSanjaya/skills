# Modern Shell Productivity Toolkit

Transform your terminal into a high-performance workspace with modern CLI tools.

## Essential Tools

### tmux - Terminal Multiplexer

**Purpose:** Persistent sessions, window/pane management, remote work

**Installation:**
```bash
# macOS
brew install tmux

# Linux
apt-get install tmux  # Debian/Ubuntu
yum install tmux      # RHEL/CentOS
```

**Basic Configuration (~/.tmux.conf):**
```bash
# Use Ctrl+A as prefix (instead of Ctrl+B)
unbind C-b
set -g prefix C-a
bind C-a send-prefix

# Enable mouse support
set -g mouse on

# Start windows and panes at 1, not 0
set -g base-index 1
setw -g pane-base-index 1

# Reload config
bind r source-file ~/.tmux.conf \; display "Config reloaded!"

# Split panes with | and -
bind | split-window -h
bind - split-window -v
unbind '"'
unbind %

# Switch panes with Alt+arrow (no prefix)
bind -n M-Left select-pane -L
bind -n M-Right select-pane -R
bind -n M-Up select-pane -U
bind -n M-Down select-pane -D

# Status bar
set -g status-position bottom
set -g status-bg colour234
set -g status-fg colour137
set -g status-left ''
set -g status-right '#[fg=colour233,bg=colour241,bold] %d/%m #[fg=colour233,bg=colour245,bold] %H:%M:%S '
```

**Essential Commands:**
```bash
# Session management
tmux new -s mysession          # Create named session
tmux attach -t mysession       # Attach to session
tmux ls                        # List sessions
tmux kill-session -t mysession # Kill session

# Inside tmux (prefix = Ctrl+A)
Ctrl+A c       # Create new window
Ctrl+A ,       # Rename window
Ctrl+A n       # Next window
Ctrl+A p       # Previous window
Ctrl+A |       # Split vertically
Ctrl+A -       # Split horizontally
Ctrl+A d       # Detach from session
Ctrl+A [       # Enter copy mode (scroll)
```

**Advanced: Persistent Sessions with Mosh:**
```bash
# Install mosh (mobile shell)
brew install mosh  # macOS
apt-get install mosh  # Linux

# Connect with mosh (survives network changes)
mosh user@server -- tmux attach
```

### fzf - Fuzzy Finder

**Purpose:** Interactive fuzzy search for files, history, processes

**Installation:**
```bash
# macOS
brew install fzf
$(brew --prefix)/opt/fzf/install

# Linux
git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf
~/.fzf/install
```

**Shell Integration:**
```bash
# Add to .bashrc or .zshrc
[ -f ~/.fzf.bash ] && source ~/.fzf.bash  # Bash
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh    # Zsh

# Key bindings (after sourcing)
Ctrl+R    # Search command history
Ctrl+T    # Search files
Alt+C     # Change directory
```

**Custom Functions:**
```bash
# Search and edit file
fe() {
    local file
    file=$(fzf --preview 'bat --color=always {}') && ${EDITOR:-vim} "$file"
}

# Search and cd to directory
fd() {
    local dir
    dir=$(find ${1:-.} -type d 2> /dev/null | fzf +m) && cd "$dir"
}

# Kill process
fkill() {
    local pid
    pid=$(ps -ef | sed 1d | fzf -m | awk '{print $2}')
    if [ -n "$pid" ]; then
        echo "$pid" | xargs kill -${1:-9}
    fi
}

# Git branch checkout
fco() {
    local branch
    branch=$(git branch --all | grep -v HEAD | sed 's/.* //' | sed 's#remotes/[^/]*/##' | sort -u | fzf +m)
    git checkout "$branch"
}
```

**Advanced Configuration:**
```bash
# Add to .bashrc/.zshrc
export FZF_DEFAULT_COMMAND='fd --type f --hidden --follow --exclude .git'
export FZF_DEFAULT_OPTS='
    --height 40%
    --layout=reverse
    --border
    --preview "bat --style=numbers --color=always {}"
    --preview-window=right:60%
'

# Use ripgrep for fzf
export FZF_DEFAULT_COMMAND='rg --files --hidden --follow --glob "!.git/*"'
```

### Atuin - Shell History

**Purpose:** Encrypted, synchronized, searchable shell history across machines

**Installation:**
```bash
# macOS
brew install atuin

# Linux
bash <(curl https://raw.githubusercontent.com/atuinsh/atuin/main/install.sh)

# Initialize
atuin import auto  # Import existing history
atuin register     # Create account (for sync)
atuin login
```

**Configuration (~/.config/atuin/config.toml):**
```toml
# Sync settings
auto_sync = true
sync_frequency = "5m"
sync_address = "https://api.atuin.sh"

# Search settings
search_mode = "fuzzy"
filter_mode = "global"
style = "compact"

# UI settings
show_preview = true
max_preview_height = 4
```

**Usage:**
```bash
# Search history (replaces Ctrl+R)
Ctrl+R    # Interactive search

# Commands
atuin search "git commit"  # Search for pattern
atuin stats                # Show statistics
atuin sync                 # Manual sync
atuin history list         # List history
```

**Zsh Integration:**
```bash
# Add to .zshrc
eval "$(atuin init zsh)"

# Optional: Disable default Ctrl+R
bindkey -r '^R'
bindkey '^R' _atuin_search_widget
```

### ripgrep (rg) - Fast Grep

**Purpose:** Blazing fast text search, respects .gitignore

**Installation:**
```bash
# macOS
brew install ripgrep

# Linux
apt-get install ripgrep  # Debian/Ubuntu
```

**Usage:**
```bash
# Basic search
rg "pattern" /path/to/search

# Search specific file types
rg "TODO" -t py          # Python files only
rg "function" -t js -t ts  # JavaScript and TypeScript

# Case insensitive
rg -i "pattern"

# Show context
rg -C 3 "pattern"  # 3 lines before and after

# Search hidden files
rg --hidden "pattern"

# Search specific files
rg "pattern" -g "*.conf"

# Exclude directories
rg "pattern" -g "!node_modules/*"

# Count matches
rg -c "pattern"

# List files with matches
rg -l "pattern"
```

**Configuration (~/.ripgreprc):**
```bash
# Default options
--smart-case
--hidden
--glob=!.git/*
--glob=!node_modules/*
--glob=!.cache/*
--colors=match:fg:yellow
--colors=match:style:bold
```

### bat - Better Cat

**Purpose:** Syntax highlighting, Git integration, line numbers

**Installation:**
```bash
# macOS
brew install bat

# Linux
apt-get install bat  # Debian/Ubuntu (command is 'batcat')
```

**Usage:**
```bash
# View file with syntax highlighting
bat file.py

# Show line numbers
bat -n file.py

# Show Git changes
bat --diff file.py

# Pager mode (like less)
bat --paging=always large_file.log

# Multiple files
bat file1.py file2.js

# Specific language
bat --language=json data.txt
```

**Configuration (~/.config/bat/config):**
```bash
# Default theme
--theme="Monokai Extended"

# Show line numbers
--style="numbers,changes,header"

# Paging
--paging=never
```

**Alias for cat:**
```bash
# Add to .bashrc/.zshrc
alias cat='bat --paging=never'
```

### eza - Modern ls

**Purpose:** Better file listings with colors, icons, Git status

**Installation:**
```bash
# macOS
brew install eza

# Linux
cargo install eza  # Requires Rust
```

**Usage:**
```bash
# Basic listing
eza

# Long format with Git status
eza -l --git

# Tree view
eza --tree --level=2

# All files including hidden
eza -a

# Sort by modified time
eza -l --sort=modified

# Icons (requires Nerd Font)
eza --icons

# Grid view
eza --grid
```

**Aliases:**
```bash
# Add to .bashrc/.zshrc
alias ls='eza'
alias ll='eza -l --git'
alias la='eza -la --git'
alias lt='eza --tree --level=2'
alias l='eza -lah --git'
```

### zoxide - Smart cd

**Purpose:** Frecency-based directory jumping

**Installation:**
```bash
# macOS
brew install zoxide

# Linux
curl -sS https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | bash
```

**Shell Integration:**
```bash
# Add to .bashrc
eval "$(zoxide init bash)"

# Add to .zshrc
eval "$(zoxide init zsh)"
```

**Usage:**
```bash
# Jump to directory (fuzzy match)
z proj      # Jumps to ~/projects
z doc       # Jumps to ~/Documents

# Interactive selection
zi proj     # Shows list if multiple matches

# Add directory manually
zoxide add /path/to/dir

# Remove directory
zoxide remove /path/to/dir

# Query database
zoxide query proj
```

### fd - Better Find

**Purpose:** Fast, user-friendly alternative to find

**Installation:**
```bash
# macOS
brew install fd

# Linux
apt-get install fd-find  # Debian/Ubuntu (command is 'fdfind')
```

**Usage:**
```bash
# Find files by name
fd pattern

# Find in specific directory
fd pattern /path/to/search

# Find specific file types
fd -e py      # Python files
fd -e js -e ts  # JavaScript and TypeScript

# Execute command on results
fd -e txt -x cat {}

# Show hidden files
fd -H pattern

# Exclude patterns
fd pattern -E node_modules -E .git

# Full path search
fd -p "src/.*\.py"
```

## Integrated Workflow

### Complete Zsh Setup

```bash
# ~/.zshrc

# Plugin manager (Zinit)
source ~/.zinit/bin/zinit.zsh

# Load plugins asynchronously
zinit ice wait lucid
zinit light zsh-users/zsh-autosuggestions

zinit ice wait lucid
zinit light zdharma-continuum/fast-syntax-highlighting

# Modern tools
eval "$(zoxide init zsh)"
eval "$(atuin init zsh)"

# fzf integration
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

# Aliases
alias cat='bat --paging=never'
alias ls='eza'
alias ll='eza -l --git'
alias la='eza -la --git'
alias lt='eza --tree --level=2'

# Custom functions
fe() {
    local file
    file=$(fzf --preview 'bat --color=always {}') && ${EDITOR:-vim} "$file"
}

fco() {
    local branch
    branch=$(git branch --all | grep -v HEAD | sed 's/.* //' | sed 's#remotes/[^/]*/##' | sort -u | fzf +m)
    git checkout "$branch"
}

# Environment
export FZF_DEFAULT_COMMAND='fd --type f --hidden --follow --exclude .git'
export FZF_DEFAULT_OPTS='--height 40% --layout=reverse --border'
export BAT_THEME="Monokai Extended"
```

### tmux + fzf Integration

```bash
# Add to .tmux.conf

# fzf session switcher
bind-key s run-shell "tmux list-sessions -F '#{session_name}' | fzf --reverse | xargs tmux switch-client -t"

# fzf window switcher
bind-key w run-shell "tmux list-windows -F '#{window_index}: #{window_name}' | fzf --reverse | cut -d: -f1 | xargs tmux select-window -t"
```

### Git Integration

```bash
# Add to .bashrc/.zshrc

# Interactive git add
ga() {
    git status --short | fzf -m --preview 'git diff --color=always {2}' | awk '{print $2}' | xargs git add
}

# Interactive git log
gl() {
    git log --oneline --color=always | fzf --preview 'git show --color=always {1}' | awk '{print $1}' | xargs git show
}

# Interactive git diff
gd() {
    git diff --name-only | fzf --preview 'git diff --color=always {}' | xargs git diff
}
```

## Tool Comparison

| Task | Traditional | Modern | Improvement |
|------|------------|--------|-------------|
| Search files | `find` | `fd` | 10x faster, simpler syntax |
| Search text | `grep` | `ripgrep` | 100x faster, respects .gitignore |
| View files | `cat` | `bat` | Syntax highlighting, Git integration |
| List files | `ls` | `eza` | Colors, icons, Git status |
| Change dir | `cd` | `zoxide` | Frecency-based, fuzzy matching |
| History search | `Ctrl+R` | `fzf` / `atuin` | Fuzzy search, sync across machines |
| Terminal multiplexing | `screen` | `tmux` | Better UX, more features |

## Installation Script

```bash
#!/bin/bash
# install-modern-tools.sh

set -euo pipefail

echo "Installing modern CLI tools..."

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    brew install tmux fzf ripgrep bat eza fd zoxide atuin
    $(brew --prefix)/opt/fzf/install --all
elif [[ -f /etc/debian_version ]]; then
    # Debian/Ubuntu
    sudo apt-get update
    sudo apt-get install -y tmux ripgrep bat fd-find
    
    # Install from cargo
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    cargo install eza zoxide atuin
    
    # Install fzf
    git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf
    ~/.fzf/install --all
else
    echo "Unsupported OS" >&2
    exit 1
fi

# Initialize tools
atuin import auto
zoxide add ~

echo "Installation complete!"
echo "Add the following to your .bashrc or .zshrc:"
echo ""
echo "eval \"\$(zoxide init bash)\"  # or zsh"
echo "eval \"\$(atuin init bash)\"   # or zsh"
echo "[ -f ~/.fzf.bash ] && source ~/.fzf.bash  # or .fzf.zsh"
```

## Remember

- **tmux** - Never lose your work, persistent sessions
- **fzf** - Fuzzy find everything, blazing fast
- **Atuin** - Never lose command history, sync everywhere
- **ripgrep** - Search code 100x faster
- **bat** - Read files with style
- **eza** - See what matters in listings
- **zoxide** - Jump to directories instantly
- **fd** - Find files without the pain

These tools transform the terminal from a basic interface into a professional, high-performance workspace.
