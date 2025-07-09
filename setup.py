#!/usr/bin/env python3
"""
Setup script for the Unemployment Tracker application.
This script helps set up the development environment and install dependencies.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

# Project metadata
PROJECT_NAME = "unemployment-tracker"
PYTHON_VERSION = "3.8"
REQUIREMENTS_FILE = "requirements.txt"
ENV_EXAMPLE_FILE = ".env.example"
ENV_FILE = ".env"

def run_command(command, cwd=None):
    """Run a shell command and return True if successful."""
    try:
        print(f"Running: {' '.join(command)}")
        result = subprocess.run(
            command,
            cwd=cwd or os.getcwd(),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}" if e.stderr else f"Command failed with code {e.returncode}")
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False

def check_python_version():
    """Check if the Python version meets the requirements."""
    try:
        major, minor = map(int, PYTHON_VERSION.split('.'))
        if sys.version_info < (major, minor):
            print(f"Error: Python {major}.{minor}+ is required. Current version: {sys.version_info.major}.{sys.version_info.minor}")
            return False
        return True
    except Exception as e:
        print(f"Error checking Python version: {str(e)}")
        return False

def create_virtual_environment():
    """Create a Python virtual environment."""
    venv_dir = ".venv"
    if os.path.exists(venv_dir):
        print(f"Virtual environment already exists at {venv_dir}")
        return True
    
    print(f"Creating virtual environment at {venv_dir}...")
    return run_command([sys.executable, "-m", "venv", venv_dir])

def install_dependencies():
    """Install project dependencies."""
    if not os.path.exists(REQUIREMENTS_FILE):
        print(f"Error: {REQUIREMENTS_FILE} not found")
        return False
    
    # Determine the correct pip command based on the platform
    pip_cmd = os.path.join(".venv", "bin", "pip")
    if sys.platform == "win32":
        pip_cmd = os.path.join(".venv", "Scripts", "pip")
    
    # Install the package in development mode
    if not run_command([pip_cmd, "install", "-e", "."]):
        return False
    
    # Install development dependencies
    if os.path.exists("requirements-dev.txt"):
        if not run_command([pip_cmd, "install", "-r", "requirements-dev.txt"]):
            return False
    
    print("Dependencies installed successfully!")
    return True

def setup_environment_vars():
    """Set up environment variables."""
    if not os.path.exists(ENV_EXAMPLE_FILE):
        print(f"Warning: {ENV_EXAMPLE_FILE} not found. No environment variables to set up.")
        return True
    
    if os.path.exists(ENV_FILE):
        print(f"{ENV_FILE} already exists. Skipping creation.")
        return True
    
    print(f"Creating {ENV_FILE} from {ENV_EXAMPLE_FILE}...")
    try:
        shutil.copy(ENV_EXAMPLE_FILE, ENV_FILE)
        print(f"Created {ENV_FILE}. Please edit it to add your API keys and other settings.")
        return True
    except Exception as e:
        print(f"Error creating {ENV_FILE}: {str(e)}")
        return False

def create_data_directories():
    """Create necessary data directories."""
    directories = [
        "data/raw",
        "data/processed",
        "data/external",
        "logs"
    ]
    
    try:
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"Created directory: {directory}")
        return True
    except Exception as e:
        print(f"Error creating directories: {str(e)}")
        return False

def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "="*50)
    print("SETUP COMPLETE!")
    print("="*50)
    print("\nNext steps:")
    print("1. Edit the .env file and add your API keys")
    print("2. Activate the virtual environment:")
    print("   - On macOS/Linux: source .venv/bin/activate")
    print("   - On Windows: .\\.venv\\Scripts\\activate")
    print("3. Install the package in development mode: pip install -e .")
    print("4. Run the application: python -m unemployment_tracker.app")
    print("\nFor more information, see the README.md file.")

def main():
    """Main setup function."""
    print(f"Setting up {PROJECT_NAME}...\n")
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Create virtual environment
    if not create_virtual_environment():
        return 1
    
    # Set up environment variables
    if not setup_environment_vars():
        return 1
    
    # Create data directories
    if not create_data_directories():
        return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Print next steps
    print_next_steps()
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred during setup: {str(e)}")
        sys.exit(1)
