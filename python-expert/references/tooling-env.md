# Tooling & Environment Setup (2025/2026)

Astral-powered Rust toolchain = decisive modern standard. Replaces pip, poetry, conda, pyenv, black, isort, mypy (partially).

## 1. uv package manager

Blazing fast (10-100x vs pip). Manages Python interpreters, projects, locks, and environments.

### Core commands
```bash
uv init app && cd app           # init project
uv add ruff fastapi httpx       # add dependency (update pyproject.toml + uv.lock + .venv)
uv run python main.py           # run in env (auto-syncs first)
uv sync --frozen                # CI: install exactly from lockfile
uv python install 3.13 3.13t    # install standard & free-threaded builds
uvx ruff check .                # run one-off tool in ephemeral env
```

### Workspaces (Monorepo)
Add `[tool.uv.workspace]` to root `pyproject.toml`:
```toml
[tool.uv.workspace]
members = ["libs/*", "apps/*"]
```
Local references use workspace source linking:
```toml
[tool.uv.sources]
my-lib = { workspace = true }
```

## 2. ruff Linter/Formatter

Replaces black, isort, flake8, pyupgrade. Fast Rust binary. Configure in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 88
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "S"] # errors, pyflakes, isort, bugbear, pyupgrade, bandit
ignore = ["E501"]                        # line length formatter handles

[tool.ruff.format]
quote-style = "double"
```

## 3. ty Type Checker (Beta)

Astral Rust type checker (Beta since Dec 2025).
*   **Speed**: 10-60x faster than mypy/pyright.
*   **Usage**: Run `ty` on pre-commit / local dev.
*   **CI Recommendation**: Run `ty` for fast feedback, but keep `mypy --strict` as final gate due to conformance limitations.

## 4. pyproject.toml anatomy (PEP 621 / 735)

Standard configuration structure:

```toml
[project]
name = "myproject"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "pydantic>=2.13"
]

[project.optional-dependencies]
cli = ["typer>=0.12"]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.9.0",
    "mypy>=1.15",
    { include-group = "test" }
]
test = [
    "pytest-asyncio>=0.23",
    "httpx>=0.27"
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## 5. CI/CD GitHub Actions

Optimized with cache integration:
```yaml
- uses: astral-sh/setup-uv@v5
  with:
    enable-cache: true
- run: uv sync --frozen
- run: uv run ruff check .
- run: uv run mypy .
- run: uv run pytest
```

## 6. Global Machine Python Setup

Best practices for configuring developer machines globally:

1.  **Zero System Python**: Never use system Python (`/usr/bin/python`) or global `pip install` for development. Avoid Homebrew-managed Pythons for projects.
2.  **uv-Managed Interpreters**: Standardize on `uv python` to fetch, install, and manage interpreters in user space:
    ```bash
    uv python install 3.12 3.13 3.14  # installs to ~/.local/share/uv/python/
    uv python list                    # view all available/installed runtimes
    ```
3.  **Global Tool Isolation**: Use `uv tool` (modern replacement for `pipx`) to install global CLI utilities in isolated environments:
    ```bash
    uv tool install ruff     # installs globally available ruff binary
    uv tool install pyright  # installs globally available pyright binary
    uv tool list             # list installed global tools
    ```
4.  **Global Config (`uv.toml`)**: Standardize defaults at `~/.config/uv/uv.toml`:
    ```toml
    [pip]
    require-virtualenv = true   # prevent accidental global pip installs
    
    [python]
    downloads = "auto"          # automatically download missing python versions
    ```
5.  **Shell Integration**: Add completion helpers to your shell profile (`~/.zshrc` or `~/.bashrc`):
    ```bash
    echo 'eval "$(uv generate-shell-completion zsh)"' >> ~/.zshrc
    echo 'eval "$(uvx --generate-shell-completion zsh)"' >> ~/.zshrc
    ```
