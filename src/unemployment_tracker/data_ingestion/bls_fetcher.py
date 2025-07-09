import os
import json
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BLSDataFetcher:
    """Class to fetch and process unemployment data from BLS API."""
    
    def __init__(self, api_key=None):
        """Initialize with optional API key."""
        self.api_key = api_key or os.getenv('BLS_API_KEY')
        self.base_url = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'
        self.headers = {'Content-type': 'application/json'}
        
        # Common series IDs for unemployment data
        self.series_ids = {
            'total': 'LNS14000000',  # Total unemployment
            'black': 'LNS14000006',  # Black or African American
            'hispanic': 'LNS14000009',  # Hispanic or Latino
            'white': 'LNS14000003',  # White
            'asian': 'LNS14032183',  # Asian
            'men_20_plus': 'LNS14000001',  # Men 20 years and over
            'women_20_plus': 'LNS14000002',  # Women 20 years and over
        }
    
    def fetch_data(self, series_ids=None, start_year=None, end_year=None):
        """
        Fetch data from BLS API for given series IDs and date range.
        
        Args:
            series_ids (list): List of series IDs to fetch
            start_year (int): Start year (default: current year - 5)
            end_year (int): End year (default: current year)
            
        Returns:
            pd.DataFrame: Processed data
        """
        if not series_ids:
            series_ids = list(self.series_ids.values())
            
        if not all(sid in self.series_ids.values() for sid in series_ids):
            raise ValueError("One or more invalid series IDs provided")
            
        current_year = datetime.now().year
        start_year = start_year or (current_year - 5)
        end_year = end_year or current_year
        
        # Prepare API request payload
        data = {
            "seriesid": series_ids,
            "startyear": str(start_year),
            "endyear": str(end_year),
            "registrationkey": self.api_key
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                data=json.dumps(data)
            )
            response.raise_for_status()
            json_data = response.json()
            
            if json_data.get('status') != 'REQUEST_SUCCEEDED':
                raise Exception(f"BLS API error: {json_data.get('message', 'Unknown error')}")
                
            return self._process_response(json_data)
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from BLS API: {e}")
            return pd.DataFrame()
    
    def _process_response(self, json_data):
        """Process the JSON response from BLS API into a pandas DataFrame."""
        records = []
        
        for series in json_data.get('Results', {}).get('series', []):
            series_id = series.get('seriesID')
            demographic = next((k for k, v in self.series_ids.items() if v == series_id), 'unknown')
            
            for data_point in series.get('data', []):
                records.append({
                    'date': f"{data_point['year']}-{data_point['period'][1:]}-01",
                    'demographic': demographic,
                    'value': float(data_point['value']),
                    'footnotes': data_point.get('footnotes', [{}])[0].get('text', '')
                })
        
        df = pd.DataFrame(records)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
        return df
    
    def save_to_csv(self, df, filename='bls_unemployment.csv'):
        """Save the DataFrame to a CSV file."""
        if not df.empty:
            df.to_csv(f"../data/processed/{filename}", index=False)
            print(f"Data saved to {filename}")


def main():
    """Example usage of the BLSDataFetcher class."""
    fetcher = BLSDataFetcher()
    
    # Fetch data for all demographics
    print("Fetching unemployment data from BLS API...")
    df = fetcher.fetch_data()
    
    if not df.empty:
        print(f"Fetched {len(df)} data points")
        fetcher.save_to_csv(df)
    else:
        print("No data was fetched. Please check your API key and try again.")


if __name__ == "__main__":
    main()
