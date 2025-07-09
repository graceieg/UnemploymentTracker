import os
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LayoffDataParser:
    """Class to parse and process layoff data from various sources."""
    
    def __init__(self, data_path=None):
        """Initialize the LayoffDataParser.
        
        Args:
            data_path (str, optional): Path to the raw layoff data file.
        """
        self.data_path = data_path or "../data/raw/tech_layoffs.csv"
        self.geolocator = Nominatim(
            user_agent="layoff_tracker",
            timeout=10
        )
        # Add rate limiting to respect the geocoding service
        self.geocode = RateLimiter(
            self.geolocator.geocode,
            min_delay_seconds=1,
            return_value_on_exception=None
        )
        
    def load_data(self, file_path=None):
        """Load layoff data from a CSV file.
        
        Args:
            file_path (str, optional): Path to the layoff data file.
            
        Returns:
            pd.DataFrame: Loaded data
        """
        file_path = file_path or self.data_path
        try:
            return pd.read_csv(file_path)
        except FileNotFoundError:
            print(f"Error: File not found at {file_path}")
            return pd.DataFrame()
    
    def clean_data(self, df):
        """Clean and standardize the layoff data.
        
        Args:
            df (pd.DataFrame): Raw layoff data
            
        Returns:
            pd.DataFrame: Cleaned data
        """
        if df.empty:
            return df
            
        # Make a copy to avoid SettingWithCopyWarning
        df = df.copy()
        
        # Standardize column names
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        # Handle missing values
        df['employees_laid_off'] = pd.to_numeric(
            df['employees_laid_off'].astype(str).str.replace(',', ''), 
            errors='coerce'
        )
        
        # Convert date columns to datetime
        date_columns = ['date_announced', 'date_added', 'last_updated']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Standardize company names
        if 'company' in df.columns:
            df['company'] = df['company'].str.title().str.strip()
            
        # Standardize industry names
        if 'industry' in df.columns:
            df['industry'] = df['industry'].str.title().str.strip()
        
        return df
    
    def geocode_locations(self, df, location_col='location'):
        """Add latitude and longitude for each location.
        
        Args:
            df (pd.DataFrame): DataFrame containing location data
            location_col (str): Name of the column containing location strings
            
        Returns:
            pd.DataFrame: DataFrame with added 'latitude' and 'longitude' columns
        """
        if df.empty or location_col not in df.columns:
            return df
            
        # Make a copy to avoid SettingWithCopyWarning
        df = df.copy()
        
        # Initialize columns
        df['latitude'] = None
        df['longitude'] = None
        
        # Only geocode locations that don't have coordinates yet
        for idx, row in df.iterrows():
            location_str = row[location_col]
            if pd.isna(location_str):
                continue
                
            try:
                location = self.geocode(location_str)
                if location:
                    df.at[idx, 'latitude'] = location.latitude
                    df.at[idx, 'longitude'] = location.longitude
            except Exception as e:
                print(f"Error geocoding {location_str}: {e}")
                
        return df
    
    def process_layoff_data(self, input_path=None, output_path=None):
        """Process layoff data from input to output.
        
        Args:
            input_path (str, optional): Path to input CSV file
            output_path (str, optional): Path to save processed data
            
        Returns:
            pd.DataFrame: Processed layoff data
        """
        # Load the data
        df = self.load_data(input_path or self.data_path)
        if df.empty:
            return df
        
        # Clean the data
        df_clean = self.clean_data(df)
        
        # Add geocoding
        if 'location' in df_clean.columns:
            print("Geocoding locations (this may take a while)...")
            df_clean = self.geocode_locations(df_clean)
        
        # Save the processed data
        output_path = output_path or "../data/processed/processed_layoffs.csv"
        df_clean.to_csv(output_path, index=False)
        print(f"Processed data saved to {output_path}")
        
        return df_clean


def main():
    """Example usage of the LayoffDataParser class."""
    parser = LayoffDataParser()
    
    # Process the layoff data
    print("Processing layoff data...")
    df_processed = parser.process_layoff_data()
    
    if not df_processed.empty:
        print(f"Processed {len(df_processed)} layoff records")
        print("Sample data:")
        print(df_processed.head())
    else:
        print("No data was processed. Please check your input file.")


if __name__ == "__main__":
    main()
