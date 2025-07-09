#!/usr/bin/env python3
"""
Unemployment Tracker - Real-Time Labor Shock Visualizer

This application provides interactive visualizations of unemployment trends,
layoff data, and labor market analysis to help understand workforce dynamics.
"""
import os
import sys
import logging
from pathlib import Path
import streamlit as st

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.append(str(project_root))

# Import dashboard components
from visualization.dashboard import UnemploymentDashboard

# Set environment variables
os.environ["STREAMLIT_SERVER_PORT"] = "8501"
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

def check_data_files():
    """Check if required data files exist and are accessible."""
    data_dir = project_root / 'data'
    required_dirs = ['raw', 'processed']
    required_files = {
        'processed/bls_unemployment.csv': 'BLS Unemployment Data',
        'processed/processed_layoffs.csv': 'Processed Layoff Data'
    }
    
    # Check if data directory exists
    if not data_dir.exists():
        logger.warning(f"Data directory not found at: {data_dir}")
        return False
    
    # Check for required subdirectories
    for subdir in required_dirs:
        if not (data_dir / subdir).exists():
            logger.warning(f"Missing data subdirectory: {subdir}")
            return False
    
    # Check for required files
    missing_files = []
    for file_path, desc in required_files.items():
        full_path = data_dir / file_path
        if not full_path.exists():
            missing_files.append(desc)
            logger.warning(f"Missing data file: {full_path}")
    
    if missing_files:
        logger.warning(f"Missing {len(missing_files)} required data files")
        return False
    
    return True

def show_setup_instructions():
    """Display setup instructions if data files are missing."""
    st.title("🚧 Setup Required")
    st.markdown(
        "### Missing Data Files\n"
        "The application is missing some required data files. Please follow these steps to set up the application:"
    )
    
    st.markdown("""
    ### 1. Create the data directory structure
    Run these commands in your terminal:
    ```bash
    mkdir -p data/raw data/processed
    ```
    
    ### 2. Download the required data files
    - **BLS Unemployment Data**: 
      1. Visit the [BLS Data Tools](https://www.bls.gov/data/)
      2. Download the unemployment rate data (Series ID: LNS14000000 for total unemployment)
      3. Save as `bls_unemployment.csv` in the `data/raw` directory
    
    - **Layoff Data**:
      1. Visit [Layoffs.fyi](https://layoffs.fyi/)
      2. Download the layoff dataset
      3. Save as `tech_layoffs.csv` in the `data/raw` directory
    
    ### 3. Process the data
    Run the data processing scripts:
    ```bash
    python data_ingestion/bls_fetcher.py
    python data_ingestion/layoff_parser.py
    ```
    
    ### 4. Restart the application
    After completing these steps, restart the application.
    """)
    
    st.error("Please complete the setup steps above to use the application.")

def main():
    """Main entry point for the application."""
    # Check if we're running in Streamlit
    if 'streamlit' in sys.modules:
        # Check if data files exist
        if not check_data_files():
            show_setup_instructions()
            return
        
        # Initialize and run the dashboard
        try:
            dashboard = UnemploymentDashboard(data_dir=str(project_root / 'data'))
            dashboard.run()
        except Exception as e:
            logger.error(f"Error running dashboard: {str(e)}", exc_info=True)
            st.error(f"An error occurred: {str(e)}")
    
    else:
        # Command-line interface
        import argparse
        
        parser = argparse.ArgumentParser(description='Unemployment Tracker')
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Fetch command
        fetch_parser = subparsers.add_parser('fetch', help='Fetch data from APIs')
        fetch_parser.add_argument('--bls', action='store_true', help='Fetch BLS unemployment data')
        fetch_parser.add_argument('--layoffs', action='store_true', help='Fetch layoff data')
        
        # Process command
        process_parser = subparsers.add_parser('process', help='Process data')
        process_parser.add_argument('--bls', action='store_true', help='Process BLS data')
        process_parser.add_argument('--layoffs', action='store_true', help='Process layoff data')
        
        # Run command
        run_parser = subparsers.add_parser('run', help='Run the dashboard')
        run_parser.add_argument('--port', type=int, default=8501, help='Port to run the dashboard on')
        
        args = parser.parse_args()
        
        if args.command == 'fetch':
            # Implement data fetching logic
            print("Data fetching not yet implemented. Use the --help flag for more information.")
        
        elif args.command == 'process':
            # Implement data processing logic
            print("Data processing not yet implemented. Use the --help flag for more information.")
        
        elif args.command == 'run' or not args.command:
            # Run the Streamlit dashboard
            import subprocess
            
            # Set the port
            os.environ["STREAMLIT_SERVER_PORT"] = str(args.port)
            
            # Run the dashboard
            subprocess.run(["streamlit", "run", __file__], check=True)
        
        else:
            parser.print_help()

if __name__ == "__main__":
    main()
