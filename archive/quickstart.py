#!/usr/bin/env python3
"""
Quick start script for the Dash database browser.
Uses uv for dependency management and environment setup.

This script provides an interactive way to:
1. Check/install uv (the fast Python package manager)
2. Set up virtual environment via `uv sync`
3. Find SQLite database files on your system
4. Launch the browser-based Dash app
5. Open it in your default browser

See UV_GUIDE.md for more information about using uv.
"""

import subprocess
import sys
import os
from pathlib import Path
import webbrowser
import time
from typing import Optional


def run_command(cmd: list, description: str = "") -> bool:
    """Run a shell command and return success status."""
    print(f"\n▶ {description or ' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found. Make sure you have {cmd[0]} installed.")
        return False


def check_uv_installed() -> bool:
    """Check if uv is installed."""
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_uv() -> bool:
    """Install uv if not already installed."""
    print("\nInstalling uv (the fast Python package installer)...")
    
    if sys.platform == "win32":
        # Windows
        return run_command(
            ["powershell", "-Command", "irm https://astral.sh/uv/install.ps1 | iex"],
            "Installing uv on Windows"
        )
    else:
        # macOS/Linux
        return run_command(
            ["curl", "-LsSf", "https://astral.sh/uv/install.sh", "|", "sh"],
            "Installing uv on Unix-like system"
        )


def install_dependencies() -> bool:
    """Install required Python packages using uv."""
    print("\n" + "=" * 60)
    print("Setting up dependencies with uv...")
    print("=" * 60)
    
    # Check if uv is installed
    if not check_uv_installed():
        print("uv not found. Installing...")
        if not install_uv():
            print("\n❌ Failed to install uv")
            print("Please install uv manually: https://github.com/astral-sh/uv")
            return False
    
    # Sync dependencies using uv
    return run_command(
        ["uv", "sync"],
        "Installing packages from pyproject.toml with uv"
    )


def get_database_path() -> Optional[str]:
    """Interactively get database path from user."""
    print("\n" + "=" * 60)
    print("Database Configuration")
    print("=" * 60)
    
    # Check if there's a default db.sqlite in the current directory
    default_db = Path("db.sqlite")
    if default_db.exists():
        print(f"\nFound default database: {default_db.absolute()}")
        response = input("Use this database? (y/n): ").strip().lower()
        if response in ['y', 'yes', '']:
            return str(default_db.absolute())
    
    # Check for .sqlite files in common locations
    common_paths = [
        Path.cwd() / "db.sqlite",
        Path.cwd() / "data.sqlite",
        Path.home() / "Downloads" / "database.sqlite",
    ]
    
    sqlite_files = [p for p in common_paths if p.exists()]
    if sqlite_files:
        print("\nFound SQLite files:")
        for i, path in enumerate(sqlite_files, 1):
            print(f"  {i}. {path}")
        
        try:
            choice = input("\nSelect a file (number) or enter custom path (or press Enter to skip): ").strip()
            if choice.isdigit() and 0 < int(choice) <= len(sqlite_files):
                return str(sqlite_files[int(choice) - 1].absolute())
            elif choice:
                return choice
        except (ValueError, IndexError):
            pass
    
    # Manual entry
    print("\nEnter the path to your SQLite database file:")
    print("Examples:")
    print("  - /path/to/database.sqlite")
    print("  - C:\\Users\\username\\Desktop\\data.sqlite")
    print("  - ./relative/path/db.sqlite")
    
    db_path = input("\nDatabase path (leave empty to start without file): ").strip()
    
    if db_path:
        db_path = str(Path(db_path).expanduser())
        if not Path(db_path).exists():
            print(f"⚠️  Warning: File not found at {db_path}")
            print("   You can load a database from the web interface instead.")
        return db_path
    
    return None


def start_app(db_path: Optional[str] = None) -> None:
    """Start the Dash application."""
    print("\n" + "=" * 60)
    print("Starting Database Browser...")
    print("=" * 60)
    
    # Set environment variable if database path provided
    if db_path:
        os.environ['DATABASE_PATH'] = db_path
        print(f"\nDatabase path: {db_path}")
    
    print("\n🚀 Starting web server on http://127.0.0.1:8050")
    print("Press Ctrl+C to stop the server\n")
    
    # Wait a moment then try to open browser
    def open_browser():
        time.sleep(3)
        try:
            webbrowser.open('http://127.0.0.1:8050')
            print("✓ Browser opening...\n")
        except Exception as e:
            print(f"Could not auto-open browser: {e}")
            print("Manually navigate to http://127.0.0.1:8050\n")
    
    import threading
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Run the app using uv
    try:
        subprocess.run(
            ["uv", "run", "dash_app.py"],
            check=False
        )
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped.")
    except Exception as e:
        print(f"❌ Error running app: {e}")


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("  SQLite Database Browser - Quick Start")
    print("=" * 60)
    
    # Check if dash_app.py exists
    if not Path("dash_app.py").exists():
        print("\n❌ Error: dash_app.py not found in current directory")
        print("Please run this script from the dataset_browser directory")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies")
        sys.exit(1)
    
    # Get database path
    db_path = get_database_path()
    
    # Start app
    start_app(db_path)


if __name__ == "__main__":
    main()
