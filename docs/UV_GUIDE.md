# Using uv with Dataset Browser

This project uses [uv](https://github.com/astral-sh/uv) for dependency management and virtual environment setup.

## What is uv?

`uv` is a fast, Rust-based Python package installer and virtual environment manager. It's designed to be a replacement for pip, pip-tools, pipenv, and venv.

**Benefits:**
- ⚡ **Fast** - 10-100x faster than pip
- 🔒 **Deterministic** - Consistent installs across machines
- 📦 **Integrated** - Handles both packages and environments
- 🎯 **Simple** - Fewer commands needed

## Quick Start

```bash
# Install dependencies and create virtual environment
uv sync

# Run any Python script through the environment
uv run python script.py

# Run the Dash app
uv run dash_app.py

# Advanced: Run arbitrary commands in the environment
uv run pip list
```

## Common Commands

### Setup
```bash
# Initial sync (creates .venv and installs packages)
uv sync

# Upgrade all packages to latest compatible versions
uv sync --upgrade
```

### Running Code
```bash
# Run the Dash app
uv run dash_app.py

# Run Python commands
uv run python -c "import pandas; print(pandas.__version__)"

# Run the quickstart script
uv run python quickstart.py
```

### Adding Dependencies
```bash
# Add a new package to the project
uv add pandas-profiling

# Add a development-only dependency
uv add --dev pytest

# Add a specific version
uv add "requests==2.31.0"
```

### Modifying Dependencies
```bash
# Remove a package
uv remove package-name

# Update dependencies in pyproject.toml and .lock file
uv sync --upgrade

# Lock dependencies without installing
uv lock
```

## Configuration

Dependencies are defined in `pyproject.toml`:

```toml
[project]
dependencies = [
    "dash>=3.3.0",
    "plotly>=5.18.0",
    # ... other packages
]
```

A `uv.lock` file is generated with exact versions for reproducibility.

## Virtual Environment

uv automatically creates and manages a `.venv` directory:

```bash
# Activate the virtual environment (optional, uv run activates it implicitly)
source .venv/bin/activate          # macOS/Linux
.venv\Scripts\activate.bat         # Windows

# Deactivate when done
deactivate
```

## Environment Information

```bash
# Show Python version in use
uv run python --version

# List installed packages
uv run pip list

# Show project information
uv tree
```

## Troubleshooting

### "uv: command not found"
Install uv:
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex
```

### "No such file or directory: '.venv/bin/python'"
This means `.venv` wasn't created. Run:
```bash
uv sync
```

### Dependency conflicts
Use `--upgrade` to get the latest versions:
```bash
uv sync --upgrade
```

### Windows OneDrive hardlink error (os error 396)
If your project is inside a OneDrive-synced directory, hardlink creation can fail during install.

This project sets `link-mode = "copy"` in `pyproject.toml` under `[tool.uv]` so `uv sync` works reliably.

If you still see this issue locally, run:
```bash
uv sync --link-mode=copy
```

## Development Workflow

1. **First time setup:**
   ```bash
   uv sync
   ```

2. **Start development:**
   ```bash
   uv run dash_app.py
   ```

3. **Add a new dependency:**
   ```bash
   uv add new-package-name
   ```

4. **Share project with others:**
   Just commit `pyproject.toml` and `uv.lock`
   They run `uv sync` to get the exact same environment

## Migration from pip/requirements.txt

If you have an old `requirements.txt`, you can migrate to uv:

```bash
# Read the requirements file and add them to pyproject.toml
# Then run:
uv sync

# Delete old requirements.txt (no longer needed)
```

The old `requirements_dash.txt` is deprecated - all dependencies are now in `pyproject.toml`.

## Additional Resources

- **Official uv docs:** https://docs.astral.sh/uv/
- **GitHub repository:** https://github.com/astral-sh/uv
- **FAQ:** https://docs.astral.sh/uv/guides/

## Tips

- **Faster installs:** uv caches packages, so subsequent installs are much faster
- **Reproducible builds:** Commit both `pyproject.toml` and `uv.lock` to version control
- **Python versions:** uv can manage multiple Python versions (see docs)
- **Scripts:** Use `uv run` prefix to ensure consistent scripts across team members
