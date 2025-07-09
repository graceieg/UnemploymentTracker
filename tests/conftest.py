"""Configuration file for pytest."""
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Set environment variables for testing
    os.environ["ENV"] = "test"
    
    # Create test data directory
    test_data_dir = Path("tests/data")
    test_data_dir.mkdir(exist_ok=True)
