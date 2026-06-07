# Zsh Optimization and Advanced Features

Master Zsh for maximum interactive productivity.

## Table of Contents
- Profiling and Performance
- Plugin Management
- Completion System
- Zsh Line Editor (ZLE)
- Advanced Globbing
- Custom Widgets
- Prompt Engineering

## Profiling and Performance

### Using zprof

```bash
# Add to top of .zshrc
zmodload zsh/zprof

# ... your configuration ...

# Add to bottom of .zshrc
zprof
```

**Reading zprof output:**
```
num  calls                time                       self            name
-----------------------------------------------------------------------------------
 1)    1         150.23   150.23   50.00%    150.23   150.23   50.00%  compinit
 2)    3          90.15    30.05   30.00%     90.15    30.05   30.00%  nvm_load
 3)   10          60.10     6.01   20.00%     60.10     6.01   20.00%  _zsh_highlight
```

**Focus on:**
- High `self` time (time in function itself)
- High `calls` count (called many times)
- Functions taking > 50ms

### Common Bottlenecks and Solutions

#### 1. compinit (Completion System)

**Problem:** Rescans all completion files on every startup

**Solution:**
```bash
# Cache completions for 24 hours
autoload -Uz compinit

# Only regenerate once per day
if [[ -n ${ZDOTDIR:-$HOME}/.zcompdump(#qN.mh+24) ]]; then
    compinit
else
    compinit -C  # Skip security check
fi
```

#### 2. NVM Initialization

**Problem:** Adds 200-500ms to startup

**Solution - Lazy Loading:**
```bash
# Don't load NVM immediately
export NVM_DIR="$HOME/.nvm"

# Lazy-load wrapper
nvm() {
    unset -f nvm node npm npx
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    nvm "$@"
}

node() {
    unset -f nvm node npm npx
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    node "$@"
}

npm() {
    unset -f nvm node npm npx
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    npm "$@"
}

npx() {
    unset -f nvm node npm npx
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    npx "$@"
}
```

#### 3. Oh My Zsh Framework

**Problem:** Heavy, synchronous loading

**Solution - Switch to Zinit:**
```bash
# Install Zinit
bash -c "$(curl --fail --show-error --silent --location https://raw.githubusercontent.com/zdharma-continuum/zinit/HEAD/scripts/install.sh)"

# Replace Oh My Zsh with Zinit
# ~/.zshrc
source ~/.zinit/bin/zinit.zsh

# Load plugins asynchronously
zinit ice wait lucid
zinit light zsh-users/zsh-autosuggestions

zinit ice wait lucid
zinit light zdharma-continuum/fast-syntax-highlighting

zinit ice wait'1' lucid
zinit light zsh-users/zsh-completions

# Load Oh My Zsh plugins selectively
zinit snippet OMZ::plugins/git/git.plugin.zsh
zinit snippet OMZ::plugins/docker/docker.plugin.zsh
```

## Plugin Management with Zinit

### Installation

```bash
bash -c "$(curl --fail --show-error --silent --location https://raw.githubusercontent.com/zdharma-continuum/zinit/HEAD/scripts/install.sh)"
```

### Loading Strategies

**Immediate loading (critical plugins):**
```bash
zinit light zsh-users/zsh-history-substring-search
```

**Deferred loading (non-critical):**
```bash
# Load after prompt
zinit ice wait lucid
zinit light zsh-users/zsh-autosuggestions

# Load 1 second after prompt
zinit ice wait'1' lucid
zinit light zsh-users/zsh-completions
```

**Turbo mode (fastest):**
```bash
zinit ice wait lucid atload'_zsh_autosuggest_start'
zinit light zsh-users/zsh-autosuggestions
```

**Conditional loading:**
```bash
# Only load if command exists
zinit ice wait lucid has'docker'
zinit snippet OMZ::plugins/docker/docker.plugin.zsh
```

### Essential Plugins

```bash
# Autosuggestions (fish-like)
zinit ice wait lucid atload'_zsh_autosuggest_start'
zinit light zsh-users/zsh-autosuggestions

# Syntax highlighting
zinit ice wait lucid
zinit light zdharma-continuum/fast-syntax-highlighting

# Completions
zinit ice wait lucid
zinit light zsh-users/zsh-completions

# History substring search
zinit light zsh-users/zsh-history-substring-search

# fzf-tab (fuzzy completion)
zinit light Aloxaf/fzf-tab
```

## Completion System

### Basic Setup

```bash
# Enable completion system
autoload -Uz compinit
compinit

# Case-insensitive completion
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'

# Menu selection
zstyle ':completion:*' menu select

# Colors in completion
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"

# Group completions
zstyle ':completion:*' group-name ''
zstyle ':completion:*:descriptions' format '%B%d%b'

# Cache completions
zstyle ':completion:*' use-cache on
zstyle ':completion:*' cache-path ~/.zsh/cache
```

### Advanced Completion Styles

```bash
# Fuzzy matching
zstyle ':completion:*' matcher-list '' \
    'm:{a-z\-}={A-Z\_}' \
    'r:[^[:alpha:]]||[[:alpha:]]=** r:|=* m:{a-z\-}={A-Z\_}' \
    'r:|?=** m:{a-z\-}={A-Z\_}'

# Partial completion
zstyle ':completion:*' list-suffixes
zstyle ':completion:*' expand prefix suffix

# Completion for specific commands
zstyle ':completion:*:*:docker:*' option-stacking yes
zstyle ':completion:*:*:docker-*:*' option-stacking yes

# Kill command completion
zstyle ':completion:*:*:kill:*:processes' list-colors '=(#b) #([0-9]#) ([0-9a-z-]#)*=01;34=0=01'
zstyle ':completion:*:*:*:*:processes' command "ps -u $USER -o pid,user,comm -w -w"

# SSH/SCP/RSYNC completion
zstyle ':completion:*:(ssh|scp|rsync):*' tag-order 'hosts:-host:host hosts:-domain:domain hosts:-ipaddr:ip\ address *'
zstyle ':completion:*:(scp|rsync):*' group-order users files all-files hosts-domain hosts-host hosts-ipaddr
```

### fzf-tab Integration

```bash
# Install fzf-tab
zinit light Aloxaf/fzf-tab

# Configuration
zstyle ':fzf-tab:*' fzf-command ftb-tmux-popup
zstyle ':fzf-tab:complete:cd:*' fzf-preview 'eza -1 --color=always $realpath'
zstyle ':fzf-tab:complete:*:*' fzf-preview 'bat --color=always ${realpath}'
```

## Zsh Line Editor (ZLE)

### Custom Widgets

**Sudo prefixer (Alt+Alt):**
```bash
sudo-command-line() {
    [[ -z $BUFFER ]] && zle up-history
    if [[ $BUFFER == sudo\ * ]]; then
        LBUFFER="${LBUFFER#sudo }"
    else
        LBUFFER="sudo $LBUFFER"
    fi
}
zle -N sudo-command-line
bindkey "\e\e" sudo-command-line
```

**Command parker (Ctrl+Q):**
```bash
# Park current command, run another, then restore
bindkey -s '^Q' '^Uparked_command="$BUFFER"^M'
```

**Edit command in editor (Ctrl+X Ctrl+E):**
```bash
autoload -U edit-command-line
zle -N edit-command-line
bindkey '^X^E' edit-command-line
```

**Accept autosuggestion word by word (Ctrl+Right):**
```bash
bindkey '^[[1;5C' forward-word  # Ctrl+Right
bindkey '^[[1;5D' backward-word # Ctrl+Left
```

### History Configuration

```bash
# History file
HISTFILE=~/.zsh_history
HISTSIZE=50000
SAVEHIST=50000

# Options
setopt EXTENDED_HISTORY          # Write timestamp
setopt HIST_EXPIRE_DUPS_FIRST    # Expire duplicates first
setopt HIST_IGNORE_DUPS          # Don't record duplicates
setopt HIST_IGNORE_ALL_DUPS      # Delete old duplicate
setopt HIST_FIND_NO_DUPS         # Don't display duplicates
setopt HIST_IGNORE_SPACE         # Don't record commands starting with space
setopt HIST_SAVE_NO_DUPS         # Don't write duplicates
setopt HIST_VERIFY               # Show before executing from history
setopt SHARE_HISTORY             # Share history between sessions
```

### Key Bindings

```bash
# Emacs mode (default)
bindkey -e

# Or Vi mode
# bindkey -v

# Custom bindings
bindkey '^[[A' history-substring-search-up      # Up arrow
bindkey '^[[B' history-substring-search-down    # Down arrow
bindkey '^[[1;5C' forward-word                  # Ctrl+Right
bindkey '^[[1;5D' backward-word                 # Ctrl+Left
bindkey '^[[3~' delete-char                     # Delete
bindkey '^[[H' beginning-of-line                # Home
bindkey '^[[F' end-of-line                      # End
```

## Advanced Globbing

### Enable Extended Globbing

```bash
setopt EXTENDED_GLOB
```

### Glob Patterns

**Basic patterns:**
```bash
# All files
ls *

# Recursive
ls **/*

# Files only
ls *(.)

# Directories only
ls *(/)

# Executable files
ls *(*)

# Symbolic links
ls *(@)
```

**Glob qualifiers:**
```bash
# Modified in last 24 hours
ls *(mh-24)

# Larger than 10MB
ls *(Lm+10)

# Owned by current user
ls *(u:$USER:)

# Sort by modification time
ls *(om)

# Reverse sort
ls *(Om)

# Limit to 5 results
ls *(om[1,5])

# Exclude pattern
ls ^*.txt

# Multiple conditions
ls *(mh-24Lm+1.)  # Modified in last 24h, >1MB, regular file
```

**Examples:**
```bash
# Find and delete old log files
rm **/*.log(mw+4)  # Older than 4 weeks

# List 10 largest files
ls -lh *(.OL[1,10])

# Find empty directories
ls -d *(/^F)

# Find broken symlinks
ls -l *(@-^F)

# Recently modified Python files
ls **/*.py(mh-1)
```

### zmv - Mass Rename

```bash
# Load zmv
autoload -U zmv

# Rename .txt to .md
zmv '(*).txt' '$1.md'

# Add prefix
zmv '(*)' 'prefix_$1'

# Change case
zmv '(*)' '${(L)1}'  # Lowercase
zmv '(*)' '${(U)1}'  # Uppercase

# Complex pattern
zmv '(*)-(*).jpg' '$2_$1.jpg'

# Dry run (show what would happen)
zmv -n '(*).txt' '$1.md'
```

## Prompt Engineering

### Minimal Prompt

```bash
# Simple prompt
PROMPT='%F{blue}%~%f %# '

# With Git branch
autoload -Uz vcs_info
precmd() { vcs_info }
zstyle ':vcs_info:git:*' formats '%F{yellow}(%b)%f '
setopt PROMPT_SUBST
PROMPT='%F{blue}%~%f ${vcs_info_msg_0_}%# '
```

### Starship Prompt

```bash
# Install Starship
curl -sS https://starship.rs/install.sh | sh

# Add to .zshrc
eval "$(starship init zsh)"

# Configure ~/.config/starship.toml
[character]
success_symbol = "[➜](bold green)"
error_symbol = "[✗](bold red)"

[directory]
truncation_length = 3
truncate_to_repo = true

[git_branch]
symbol = "🌱 "

[git_status]
ahead = "⇡${count}"
diverged = "⇕⇡${ahead_count}⇣${behind_count}"
behind = "⇣${count}"
```

### Powerlevel10k

```bash
# Install with Zinit
zinit ice depth=1
zinit light romkatv/powerlevel10k

# Configure
p10k configure
```

## Optimization Checklist

**Startup performance:**
- [ ] Profile with `zprof`
- [ ] Cache `compinit` (24h)
- [ ] Lazy-load NVM/RVM
- [ ] Use Zinit with async loading
- [ ] Remove unused plugins
- [ ] Target < 0.5s startup

**Completion:**
- [ ] Enable caching
- [ ] Use fzf-tab for fuzzy completion
- [ ] Configure matcher-list for fuzzy matching
- [ ] Group and color completions

**History:**
- [ ] Set HISTSIZE to 50000+
- [ ] Enable SHARE_HISTORY
- [ ] Use Atuin for sync
- [ ] Configure history-substring-search

**Globbing:**
- [ ] Enable EXTENDED_GLOB
- [ ] Learn glob qualifiers
- [ ] Use zmv for mass renames

**Prompt:**
- [ ] Keep prompt fast (< 10ms)
- [ ] Use async for Git status
- [ ] Consider Starship or P10k

## Complete Optimized .zshrc

```bash
# ~/.zshrc - Optimized configuration

# Profiling (comment out after optimization)
# zmodload zsh/zprof

# Zinit
source ~/.zinit/bin/zinit.zsh

# Completion system (cached)
autoload -Uz compinit
if [[ -n ${ZDOTDIR:-$HOME}/.zcompdump(#qN.mh+24) ]]; then
    compinit
else
    compinit -C
fi

# Completion styles
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'
zstyle ':completion:*' menu select
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
zstyle ':completion:*' use-cache on
zstyle ':completion:*' cache-path ~/.zsh/cache

# History
HISTFILE=~/.zsh_history
HISTSIZE=50000
SAVEHIST=50000
setopt EXTENDED_HISTORY HIST_IGNORE_ALL_DUPS SHARE_HISTORY

# Options
setopt AUTO_CD EXTENDED_GLOB

# Plugins (async loading)
zinit ice wait lucid atload'_zsh_autosuggest_start'
zinit light zsh-users/zsh-autosuggestions

zinit ice wait lucid
zinit light zdharma-continuum/fast-syntax-highlighting

zinit light zsh-users/zsh-history-substring-search
zinit light Aloxaf/fzf-tab

# Modern tools
eval "$(zoxide init zsh)"
eval "$(atuin init zsh)"
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

# Prompt
eval "$(starship init zsh)"

# Aliases
alias cat='bat --paging=never'
alias ls='eza'
alias ll='eza -l --git'
alias la='eza -la --git'

# Custom widgets
sudo-command-line() {
    [[ -z $BUFFER ]] && zle up-history
    if [[ $BUFFER == sudo\ * ]]; then
        LBUFFER="${LBUFFER#sudo }"
    else
        LBUFFER="sudo $LBUFFER"
    fi
}
zle -N sudo-command-line
bindkey "\e\e" sudo-command-line

# Key bindings
bindkey '^[[A' history-substring-search-up
bindkey '^[[B' history-substring-search-down

# Lazy-load NVM
export NVM_DIR="$HOME/.nvm"
nvm() {
    unset -f nvm node npm npx
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    nvm "$@"
}

# Profiling results (comment out after optimization)
# zprof
```

## Remember

- **Profile first** - Use `zprof` to identify bottlenecks
- **Async everything** - Load non-critical plugins after prompt
- **Cache completions** - Don't regenerate on every startup
- **Lazy-load heavy tools** - NVM, RVM, Conda
- **Use modern plugins** - Zinit > Oh My Zsh
- **Target < 0.5s** - Professional startup time
