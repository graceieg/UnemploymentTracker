#!/usr/bin/env python3
"""
Setup script for the Unemployment Tracker application with sample data.
This script sets up the environment, generates sample data, and processes it.
"""
import os
import sys
import subprocess
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.absolute()
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Colors for console output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(message: str) -> None:
    """Print a formatted header message."""
    print(f"\n{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * 60}{Colors.ENDC}")

def print_success(message: str) -> None:
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

def print_error(message: str) -> None:
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def run_script(script_name: str, *args) -> bool:
    """Run a Python script with the given arguments."""
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        print_error(f"Script not found: {script_path}")
        return False
    
    cmd = [sys.executable, str(script_path)] + list(args)
    try:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, cwd=PROJECT_ROOT)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print_error(f"Error running {script_name}: {str(e)}")
        return False

def setup_environment() -> bool:
    """Set up the Python environment."""
    print_header("Setting up Python environment")
    
    # Create a virtual environment
    venv_dir = PROJECT_ROOT / "venv"
    if not venv_dir.exists():
        print("Creating virtual environment...")
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_dir)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print_success("Virtual environment created")
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to create virtual environment: {e.stderr.decode()}")
            return False
    else:
        print_success("Virtual environment already exists")
    
    # Install dependencies
    print("Installing dependencies...")
    pip_cmd = [
        str(venv_dir / "bin" / "pip") if os.name != 'nt' else str(venv_dir / "Scripts" / "pip.exe"),
        "install",
        "-r",
        str(PROJECT_ROOT / "requirements.txt")
    ]
    
    try:
        subprocess.run(pip_cmd, check=True, cwd=PROJECT_ROOT)
        print_success("Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e.stderr}")
        return False

def generate_sample_data() -> bool:
    """Generate sample data."""
    print_header("Generating Sample Data")
    return run_script("fetch_sample_data.py")

def process_sample_data() -> bool:
    """Process the sample data."""
    print_header("Processing Sample Data")
    return run_script("process_sample_data.py")

def run_application() -> bool:
    """Run the Streamlit application."""
    print_header("Starting Unemployment Tracker")
    
    # Check if Streamlit is installed
    try:
        import streamlit
        print_success("Streamlit is installed")
    except ImportError:
        print_error("Streamlit is not installed. Please install it with: pip install streamlit")
        return False
    
    # Run the application
    try:
        app_path = PROJECT_ROOT / "app.py"
        print(f"Starting Streamlit application: {app_path}")
        subprocess.Popen(["streamlit", "run", str(app_path)], cwd=PROJECT_ROOT)
        print_success("Application started successfully!")
        print("\nOpen your web browser and navigate to: http://localhost:8501")
        return True
    except Exception as e:
        print_error(f"Failed to start application: {str(e)}")
        return False

def main() -> int:
    """Main function to run the setup process."""
    print_header("Unemployment Tracker - Setup")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print_error("Python 3.8 or higher is required")
        return 1
    
    # Run setup steps
    steps = [
        ("Environment Setup", setup_environment),
        ("Sample Data Generation", generate_sample_data),
        ("Data Processing", process_sample_data),
        ("Application Launch", run_application)
    ]
    
    success = True
    for step_name, step_func in steps:
        print(f"\n{Colors.OKBLUE}=== {step_name} ==={Colors.ENDC}")
        if not step_func():
            print_warning(f"{step_name} completed with warnings")
            if step_name == "Environment Setup":
                success = False
                break
    
    if success:
        print_header("Setup Completed Successfully!")
        print("\nYou can now access the Unemployment Tracker dashboard in your web browser.")
        print("To run the application again, use:\n")
        print(f"    {Colors.BOLD}cd {PROJECT_ROOT}{Colors.ENDC}")
        print(f"    {Colors.BOLD}source venv/bin/activate  # On Windows: .\\venv\\Scripts\\activate{Colors.ENDC}")
        print(f"    {Colors.BOLD}streamlit run app.py{Colors.ENDC}\n")
        print("Thank you for using the Unemployment Tracker!")
        return 0
    else:
        print_header("Setup Failed")
        print("\nThe setup process encountered some issues. Please check the error messages above.")
        print("If you need help, please open an issue on the project's GitHub repository.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nSetup cancelled by user.")
        sys.exit(1)
