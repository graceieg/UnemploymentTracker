#!/usr/bin/env python3
"""
Process sample data for the Unemployment Tracker dashboard.
This script processes the raw sample data and saves it in the processed format.
"""
import os
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import numpy as np

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# Import processing functions from the main application
sys.path.append(str(PROJECT_ROOT))
from data_ingestion.layoff_parser import LayoffDataParser

def process_unemployment_data() -> bool:
    """Process the sample unemployment data."""
    try:
        input_file = DATA_RAW / "sample_unemployment.csv"
        output_file = DATA_PROCESSED / "bls_unemployment.csv"
        
        # Create processed directory if it doesn't exist
        os.makedirs(DATA_PROCESSED, exist_ok=True)
        
        # Read the raw data
        print(f"Reading unemployment data from {input_file}...")
        df = pd.read_csv(input_file, parse_dates=['date'])
        
        # Ensure required columns exist
        required_columns = ['date', 'demographic', 'value']
        if not all(col in df.columns for col in required_columns):
            print(f"Error: Missing required columns in {input_file}")
            return False
        
        # Sort by date and demographic
        df = df.sort_values(['date', 'demographic'])
        
        # Save the processed data
        df.to_csv(output_file, index=False)
        print(f"Saved processed unemployment data to {output_file}")
        return True
        
    except Exception as e:
        print(f"Error processing unemployment data: {str(e)}")
        return False

def process_layoff_data() -> bool:
    """Process the sample layoff data."""
    try:
        input_file = DATA_RAW / "sample_layoffs.csv"
        output_file = DATA_PROCESSED / "processed_layoffs.csv"
        
        # Create processed directory if it doesn't exist
        os.makedirs(DATA_PROCESSED, exist_ok=True)
        
        # Read the raw data
        print(f"Reading layoff data from {input_file}...")
        df = pd.read_csv(input_file, parse_dates=['date_announced'])
        
        # Ensure required columns exist
        required_columns = ['company', 'industry', 'date_announced', 'employees_laid_off']
        if not all(col in df.columns for col in required_columns):
            print(f"Error: Missing required columns in {input_file}")
            return False
        
        # Add a unique ID for each layoff event
        df['layoff_id'] = df.index + 1
        
        # Add additional processing if needed
        if 'percentage_laid_off' not in df.columns and 'total_employees' in df.columns:
            df['percentage_laid_off'] = (df['employees_laid_off'] / df['total_employees']) * 100
        
        # Add location data if not present
        if 'location' not in df.columns:
            df['location'] = 'Unknown'
        
        # Add source if not present
        if 'source' not in df.columns:
            df['source'] = 'sample_data'
        
        # Add notes if not present
        if 'notes' not in df.columns:
            df['notes'] = 'Processed sample data'
        
        # Add date added and last updated timestamps
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df['date_added'] = current_time
        df['last_updated'] = current_time
        
        # Reorder columns for consistency
        columns = [
            'layoff_id', 'company', 'industry', 'date_announced', 
            'employees_laid_off', 'total_employees', 'percentage_laid_off',
            'location', 'source', 'notes', 'date_added', 'last_updated'
        ]
        
        # Only include columns that exist in the DataFrame
        columns = [col for col in columns if col in df.columns]
        df = df[columns]
        
        # Save the processed data
        df.to_csv(output_file, index=False)
        print(f"Saved processed layoff data to {output_file}")
        return True
        
    except Exception as e:
        print(f"Error processing layoff data: {str(e)}")
        return False

def main() -> int:
    """Main function to process sample data."""
    print("Processing sample data...")
    
    success = True
    
    # Process unemployment data
    if not process_unemployment_data():
        print("Failed to process unemployment data")
        success = False
    
    # Process layoff data
    if not process_layoff_data():
        print("Failed to process layoff data")
        success = False
    
    if success:
        print("\nSample data processed successfully!")
        print("You can now run the application with the processed data.")
        return 0
    else:
        print("\nFailed to process some data files.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
