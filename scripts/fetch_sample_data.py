#!/usr/bin/env python3
"""
Fetch sample unemployment and layoff data for demonstration purposes.
This script generates sample data files in the data/raw directory.
"""
import os
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import random

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
DATA_DIR = PROJECT_ROOT / "data" / "raw"

def create_sample_unemployment_data() -> pd.DataFrame:
    """Create sample unemployment data."""
    # Generate sample data for the past 24 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30*24)  # ~2 years
    
    dates = pd.date_range(start=start_date, end=end_date, freq='M')
    
    # Create sample data for different demographics
    data = []
    demographics = ['total', 'black', 'hispanic', 'white', 'asian', 'men_20_plus', 'women_20_plus']
    
    for date in dates:
        base_rate = random.uniform(3.0, 6.0)  # Base unemployment rate between 3% and 6%
        
        for demo in demographics:
            # Add some variation based on demographic
            if demo == 'black':
                rate = base_rate * random.uniform(1.5, 2.5)  # Higher for black population
            elif demo == 'hispanic':
                rate = base_rate * random.uniform(1.2, 1.8)  # Higher for hispanic population
            elif demo == 'women_20_plus':
                rate = base_rate * random.uniform(0.9, 1.1)  # Slightly different for women
            elif demo == 'men_20_plus':
                rate = base_rate * random.uniform(0.9, 1.1)  # Slightly different for men
            else:
                rate = base_rate * random.uniform(0.8, 1.2)  # Some random variation
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'demographic': demo,
                'value': round(rate, 1)
            })
    
    return pd.DataFrame(data)

def create_sample_layoff_data() -> pd.DataFrame:
    """Create sample layoff data.
    
    Note: This is a simplified version with mock data.
    In a real application, you would fetch this from a reliable source.
    """
    # Sample companies and industries
    companies = [
        {'name': 'TechCorp', 'industry': 'Technology', 'employees': 10000},
        {'name': 'DataSystems', 'industry': 'Technology', 'employees': 5000},
        {'name': 'CloudNine', 'industry': 'Technology', 'employees': 8000},
        {'name': 'RetailGiant', 'industry': 'Retail', 'employees': 50000},
        {'name': 'ShopEasy', 'industry': 'Retail', 'employees': 30000},
        {'name': 'AutoMakers', 'industry': 'Automotive', 'employees': 40000},
        {'name': 'EcoEnergy', 'industry': 'Energy', 'employees': 15000},
        {'name': 'HealthPlus', 'industry': 'Healthcare', 'employees': 20000},
        {'name': 'FinancePro', 'industry': 'Finance', 'employees': 12000},
        {'name': 'MediaNet', 'industry': 'Media', 'employees': 7000},
    ]
    
    # Generate layoff events
    layoffs = []
    end_date = datetime.now()
    
    for i in range(50):  # Generate 50 layoff events
        company = random.choice(companies)
        layoff_date = end_date - timedelta(days=random.randint(1, 365))  # Random date in the past year
        
        # Generate a layoff size (1-20% of company size)
        layoff_percent = random.uniform(0.01, 0.20)
        layoff_count = max(10, int(company['employees'] * layoff_percent))
        
        layoffs.append({
            'company': company['name'],
            'industry': company['industry'],
            'date_announced': layoff_date.strftime('%Y-%m-%d'),
            'employees_laid_off': layoff_count,
            'total_employees': company['employees'],
            'percentage_laid_off': round(layoff_percent * 100, 1),
            'location': f"{random.choice(['San Francisco', 'New York', 'Austin', 'Seattle', 'Boston', 'Chicago', 'Denver', 'Atlanta'])}, {random.choice(['CA', 'NY', 'TX', 'WA', 'MA', 'IL', 'CO', 'GA'])}",
            'source': 'sample_data',
            'notes': 'Sample data for demonstration purposes'
        })
    
    return pd.DataFrame(layoffs)

def generate_sample_data() -> bool:
    """Generate sample data files."""
    try:
        # Create data directory if it doesn't exist
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Generate sample unemployment data
        print("Generating sample unemployment data...")
        unemployment_df = create_sample_unemployment_data()
        unemployment_file = DATA_DIR / "sample_unemployment.csv"
        unemployment_df.to_csv(unemployment_file, index=False)
        print(f"Saved sample unemployment data to {unemployment_file}")
        
        # Generate sample layoff data
        print("Generating sample layoff data...")
        layoff_df = create_sample_layoff_data()
        layoff_file = DATA_DIR / "sample_layoffs.csv"
        layoff_df.to_csv(layoff_file, index=False)
        print(f"Saved sample layoff data to {layoff_file}")
        
        return True
    
    except Exception as e:
        print(f"Error generating sample data: {str(e)}")
        return False

def main() -> int:
    """Main function to generate sample data."""
    print("Generating sample data for demonstration...")
    
    if generate_sample_data():
        print("\nSample data generated successfully!")
        print("You can now run the application with the sample data.")
        return 0
    else:
        print("\nFailed to generate sample data.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
