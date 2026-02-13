# Project Setup Summary with uv

This document summarizes the conversion of the dataset-browser project to use `uv` for dependency management.

## What Changed

### Before
- Used `pip` with `requirements_dash.txt` for package management
- Manual virtual environment setup
- Slower dependency resolution

### After  
- Uses `uv` (fast Rust-based package manager) for all dependencies
- Automatic virtual environment in `.venv/`
- Dependencies defined in `pyproject.toml`
- Lock file (`uv.lock`) ensures reproducible installs

## Files Involved

### Configuration Files
- **`pyproject.toml`** - Project metadata and all dependencies
  - Updated with Dash, Plotly, and Pandas dependencies
  - Python version: 3.13+
  
- **`.python-version`** - Python version specification
  - Set to 3.13 (matches pyproject.toml requirement)
  
- **`uv.lock`** (generated) - Exact dependency versions
  - Automatically created/updated by `uv sync`
  - Should be committed to git for reproducibility (NOT ignored)

- **`.gitignore`** - Updated to properly ignore uv-related files
  - `.venv/` ignored (virtual environment)
  - `*.sqlite` files ignored (database files)
  - Standard Python cache files ignored

### Application Files
- **`dash_app.py`** - Main Dash application
  - Fixed import to remove unused `FileSystemStore`
  - All required packages now properly imported and available
  
- **`quickstart.py`** - Interactive setup script
  - Updated to use `uv sync` for dependency installation
  - Auto-detects and installs uv if needed
  - Still works as before but with uv backend

- **`DASH_APP_README.md`** - User guide
  - Updated installation instructions to use uv
  - Includes uv installation steps for all platforms
  - Updated usage examples

### New Documentation
- **`UV_GUIDE.md`** - Complete guide to using uv
  - Common commands and workflows
  - Development practices
  - Troubleshooting tips
  - Migration information

## Quick Reference

### First Time Setup
```bash
# Install dependencies
uv sync

# Or skip manual steps with interactive quickstart
python quickstart.py
```

### Running the App
```bash
# Option 1: Direct uv command
uv run dash_app.py

# Option 2: Using quickstart script
python quickstart.py

# Option 3: After activating venv manually (optional)
.venv\Scripts\activate
python dash_app.py
```

### Adding New Dependencies
```bash
uv add package-name
```

## GitHub Repository Integration

The updated setup works seamlessly with the repository:

1. **For users cloning the repo:**
   ```bash
   git clone https://github.com/nimh-dsst/dataset-browser.git
   cd dataset-browser
   uv sync
   uv run dash_app.py
   ```

2. **For developers:**
   - Edit `pyproject.toml` to add dependencies OR
   - Use `uv add package-name` to update automatically
   - Commit both `pyproject.toml` and `uv.lock`
   - Other developers run `uv sync` to get exact same environment

## Dependency List

Current project dependencies (from `pyproject.toml`):
- `dash>=3.3.0` - Web application framework
- `dash-ag-grid>=32.3.2` - Advanced data grid component  
- `dash-bootstrap-components>=2.0.4` - Bootstrap styling
- `dash-extensions>=1.0.42` - Additional Dash utilities
- `fastparquet>=2024.11.0` - Parquet file support
- `pandas>=2.3.3` - Data manipulation
- `plotly>=5.18.0` - Interactive visualizations

## Benefits of Using uv

### Performance
- Initial install: ~3-5 seconds vs 30+ with pip
- Dependency resolution is 10-100x faster
- Better caching of downloads

### Reliability
- `uv.lock` guarantees everyone has exact same versions
- Faster builds in CI/CD pipelines
- No More "works on my machine" issues

### Developer Experience
- Single tool for package + environment management
- Clearer error messages
- Simpler workflows

### Project Management
- All config in one `pyproject.toml` file
- Easy to add/remove dependencies
- Clean separation of project vs development dependencies (when needed)

## Future Enhancements

The uv setup makes it easy to:
- Add development dependencies: `uv add --dev pytest`
- Create separate dependency groups
- Use `uv run` for guaranteed consistent script execution
- Integrate with CI/CD more efficiently

## Troubleshooting

### Issue: "uv not found"
**Solution:** Install uv first
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex
```

### Issue: Virtual environment not created
**Solution:** Run `uv sync`
```bash
uv sync
```

### Issue: "old package not uninstalled"
**Solution:** Update lockfile and reinstall
```bash
uv sync --upgrade
```

## Verification

To verify everything is working:
```bash
# Check uv is installed and working
uv --version

# Sync dependencies
uv sync

# Verify imports
uv run python -c "import dash; import plotly; print('OK')"

# Run the app
uv run dash_app.py
```

## Additional Resources

- [uv Documentation](https://docs.astral.sh/uv/)
- [uv GitHub Repository](https://github.com/astral-sh/uv)
- [PEP 517 - Build system interface](https://www.python.org/dev/peps/pep-0517/)
- [PEP 518 - Specifying build requirements](https://www.python.org/dev/peps/pep-0518/)
