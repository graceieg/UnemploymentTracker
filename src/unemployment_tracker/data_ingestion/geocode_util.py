from geopy.geocoders import Nominatim, GoogleV3
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import pandas as pd
import time
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

@dataclass
class GeoPoint:
    """Class to hold geographic point information."""
    latitude: float
    longitude: float
    address: Optional[Dict[str, Any]] = None
    raw: Optional[Any] = None

class GeoCoder:
    """A utility class for geocoding operations with rate limiting and retry logic."""
    
    def __init__(self, provider: str = 'nominatim', api_key: str = None, **kwargs):
        """Initialize the geocoder with the specified provider.
        
        Args:
            provider: Geocoding service to use ('nominatim' or 'google')
            api_key: API key for the geocoding service (required for Google)
            **kwargs: Additional arguments to pass to the geocoder
        """
        self.provider = provider.lower()
        self.api_key = api_key
        self.kwargs = kwargs
        self._init_geocoder()
        
    def _init_geocoder(self):
        """Initialize the appropriate geocoder based on the provider."""
        if self.provider == 'google':
            if not self.api_key:
                raise ValueError("API key is required for Google Geocoding API")
            self.geocoder = GoogleV3(api_key=self.api_key, **self.kwargs)
        else:  # Default to Nominatim
            user_agent = self.kwargs.pop('user_agent', 'unemployment_tracker')
            self.geocoder = Nominatim(user_agent=user_agent, **self.kwargs)
        
        # Set up rate limiting (1 request per second by default)
        min_delay = 1.1  # Slightly more than 1 second to be safe
        self.geocode = RateLimiter(
            self._geocode_with_retry,
            min_delay_seconds=min_delay,
            max_retries=3,
            return_value_on_exception=None
        )
    
    def _geocode_with_retry(self, query: str, **kwargs) -> Optional[GeoPoint]:
        """Internal method with retry logic for geocoding."""
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                location = self.geocoder.geocode(query, **kwargs)
                if location:
                    return GeoPoint(
                        latitude=location.latitude,
                        longitude=location.longitude,
                        address=location.raw.get('address', {}) if hasattr(location, 'raw') else {},
                        raw=location.raw if hasattr(location, 'raw') else None
                    )
                return None
                    
            except (GeocoderTimedOut, GeocoderServiceError) as e:
                if attempt == max_retries - 1:
                    print(f"Geocoding failed after {max_retries} attempts: {e}")
                    return None
                time.sleep(retry_delay * (attempt + 1))
            except Exception as e:
                print(f"Unexpected error during geocoding: {e}")
                return None
    
    def geocode_dataframe(self, 
                         df: pd.DataFrame, 
                         address_col: str = 'location',
                         lat_col: str = 'latitude',
                         lon_col: str = 'longitude',
                         address_components: list = None) -> pd.DataFrame:
        """Geocode addresses in a DataFrame.
        
        Args:
            df: Input DataFrame containing addresses
            address_col: Column name containing the address strings
            lat_col: Column name to store latitude
            lon_col: Column name to store longitude
            address_components: List of address components to extract (e.g., ['city', 'state', 'country'])
            
        Returns:
            DataFrame with added latitude and longitude columns
        """
        if df.empty or address_col not in df.columns:
            return df
            
        df = df.copy()
        
        # Initialize columns if they don't exist
        df[lat_col] = df.get(lat_col, None)
        df[lon_col] = df.get(lon_col, None)
        
        # Only process rows without existing coordinates
        mask = df[lat_col].isna() | df[lon_col].isna()
        to_geocode = df.loc[mask, address_col].drop_duplicates()
        
        print(f"Geocoding {len(to_geocode)} unique locations...")
        
        # Create a mapping of address to coordinates
        geo_cache = {}
        for address in to_geocode:
            if pd.isna(address):
                continue
                
            result = self.geocode(address)
            if result:
                geo_cache[address] = {
                    lat_col: result.latitude,
                    lon_col: result.longitude
                }
                
                # Add address components if requested
                if address_components and result.address:
                    for comp in address_components:
                        if comp in result.address:
                            geo_cache[address][comp] = result.address[comp]
            
            # Small delay to be nice to the geocoding service
            time.sleep(0.1)
        
        # Update the DataFrame with geocoded data
        for address, coords in geo_cache.items():
            mask = (df[address_col] == address) & (df[lat_col].isna() | df[lon_col].isna())
            for col, value in coords.items():
                if col in df.columns:
                    df.loc[mask, col] = value
        
        print(f"Geocoding complete. {len(geo_cache)}/{len(to_geocode)} locations geocoded successfully.")
        return df

def reverse_geocode(latitude: float, longitude: float, provider: str = 'nominatim', **kwargs) -> Optional[Dict[str, Any]]:
    """Reverse geocode coordinates to get address information.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        provider: Geocoding service to use ('nominatim' or 'google')
        **kwargs: Additional arguments to pass to the geocoder
        
    Returns:
        Dictionary with address components or None if not found
    """
    try:
        if provider.lower() == 'google':
            geolocator = GoogleV3(**kwargs)
        else:
            user_agent = kwargs.pop('user_agent', 'unemployment_tracker')
            geolocator = Nominatim(user_agent=user_agent, **kwargs)
            
        location = geolocator.reverse(f"{latitude}, {longitude}")
        return location.raw if location else None
        
    except Exception as e:
        print(f"Error in reverse geocoding: {e}")
        return None
