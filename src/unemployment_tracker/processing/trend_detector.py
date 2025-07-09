import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum

class TrendDirection(Enum):
    """Enum for trend directions."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"

@dataclass
class TrendResult:
    """Class to hold trend analysis results."""
    direction: TrendDirection
    magnitude: float
    confidence: float
    start_value: float
    end_value: float
    period: Tuple[str, str]
    metadata: Optional[Dict] = None

class TrendDetector:
    """Class for detecting trends in time series data."""
    
    def __init__(self, min_periods: int = 3, threshold: float = 0.1):
        """Initialize the TrendDetector.
        
        Args:
            min_periods: Minimum number of periods required for trend analysis
            threshold: Minimum magnitude to consider a trend significant
        """
        self.min_periods = min_periods
        self.threshold = threshold
    
    def detect_trends(self, 
                     df: pd.DataFrame, 
                     value_col: str, 
                     date_col: str = 'date',
                     group_cols: Optional[List[str]] = None,
                     window: int = 3) -> Dict[str, TrendResult]:
        """Detect trends in a DataFrame.
        
        Args:
            df: Input DataFrame with time series data
            value_col: Name of the column containing values to analyze
            date_col: Name of the date column
            group_cols: Columns to group by before trend analysis
            window: Rolling window size for smoothing
            
        Returns:
            Dictionary of TrendResult objects keyed by group
        """
        if df.empty or len(df) < self.min_periods:
            return {}
            
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Ensure date is datetime and sort
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(by=[*group_cols, date_col] if group_cols else date_col)
        
        results = {}
        
        # If no grouping, analyze the entire dataset
        if not group_cols:
            result = self._analyze_series(df[value_col].values, df[date_col].values)
            if result:
                results['overall'] = result
            return results
        
        # Group and analyze each group
        grouped = df.groupby(group_cols)
        for group_name, group_df in grouped:
            if len(group_df) < self.min_periods:
                continue
                
            result = self._analyze_series(group_df[value_col].values, group_df[date_col].values)
            if result:
                # Convert group_name to string if it's a tuple (multiple grouping columns)
                group_key = ','.join(str(g) for g in group_name) if isinstance(group_name, tuple) else str(group_name)
                results[group_key] = result
        
        return results
    
    def _analyze_series(self, values: np.ndarray, dates: np.ndarray) -> Optional[TrendResult]:
        """Analyze a single time series for trends.
        
        Args:
            values: Array of values
            dates: Array of corresponding dates
            
        Returns:
            TrendResult if a trend is detected, None otherwise
        """
        if len(values) < self.min_periods:
            return None
        
        # Calculate basic statistics
        start_val = values[0]
        end_val = values[-1]
        period = (str(dates[0])[:10], str(dates[-1])[:10])
        
        # Simple linear regression for trend
        x = np.arange(len(values))
        slope, intercept = np.polyfit(x, values, 1)
        
        # Calculate R-squared as a confidence measure
        y_hat = intercept + slope * x
        ss_res = np.sum((values - y_hat) ** 2)
        ss_tot = np.sum((values - np.mean(values)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Calculate percentage change
        pct_change = (end_val - start_val) / start_val if start_val != 0 else 0
        
        # Determine trend direction
        if abs(pct_change) < self.threshold:
            direction = TrendDirection.STABLE
        elif pct_change > 0:
            direction = TrendDirection.INCREASING
        else:
            direction = TrendDirection.DECREASING
        
        return TrendResult(
            direction=direction,
            magnitude=abs(pct_change),
            confidence=float(r_squared),
            start_value=float(start_val),
            end_value=float(end_val),
            period=period
        )
    
    def detect_shocks(self, 
                     df: pd.DataFrame,
                     value_col: str,
                     date_col: str = 'date',
                     group_cols: Optional[List[str]] = None,
                     z_threshold: float = 2.0) -> pd.DataFrame:
        """Detect statistical shocks in time series data.
        
        Args:
            df: Input DataFrame
            value_col: Name of the column containing values to analyze
            date_col: Name of the date column
            group_cols: Columns to group by before analysis
            z_threshold: Z-score threshold for shock detection
            
        Returns:
            DataFrame with shock events
        """
        if df.empty:
            return pd.DataFrame()
            
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        
        # Function to calculate z-scores within each group
        def calculate_zscores(group):
            values = group[value_col].values
            mean = np.mean(values)
            std = np.std(values, ddof=1)
            return (values - mean) / std if std != 0 else np.zeros_like(values)
        
        # Calculate z-scores
        if group_cols:
            df['z_score'] = df.groupby(group_cols, group_keys=False).apply(calculate_zscores).values
        else:
            df['z_score'] = calculate_zscores(df)
        
        # Identify shocks
        shock_mask = abs(df['z_score']) >= z_threshold
        shock_events = df[shock_mask].copy()
        
        # Add shock magnitude and direction
        shock_events['shock_magnitude'] = shock_events['z_score'].abs()
        shock_events['shock_direction'] = np.where(
            shock_events['z_score'] > 0, 
            'positive', 
            'negative'
        )
        
        return shock_events.sort_values(by=['z_score'], ascending=False)


def analyze_seasonality(df: pd.DataFrame, 
                       value_col: str, 
                       date_col: str = 'date',
                       freq: str = 'M') -> Dict:
    """Analyze seasonality in time series data.
    
    Args:
        df: Input DataFrame
        value_col: Name of the column containing values to analyze
        date_col: Name of the date column
        freq: Frequency for seasonal decomposition ('M' for monthly, 'Q' for quarterly)
        
    Returns:
        Dictionary with seasonality analysis results
    """
    try:
        from statsmodels.tsa.seasonal import seasonal_decompose
    except ImportError:
        print("statsmodels is required for seasonality analysis. Install with: pip install statsmodels")
        return {}
    
    if df.empty:
        return {}
        
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col).sort_index()
    
    # Resample to ensure consistent frequency
    resampled = df[value_col].resample(freq).mean().ffill()
    
    if len(resampled) < 2 * 12:  # Need at least 2 years of monthly data
        return {}
    
    # Perform seasonal decomposition
    try:
        decomposition = seasonal_decompose(
            resampled,
            model='additive',
            period=12 if freq == 'M' else 4
        )
        
        # Calculate seasonality strength
        residual = decomposition.resid.dropna()
        seasonal = decomposition.seasonal.dropna()
        
        if len(residual) > 0 and len(seasonal) > 0:
            strength = max(0, 1 - (residual.var() / (residual + seasonal).var()))
        else:
            strength = 0.0
        
        return {
            'seasonal_strength': float(strength),
            'seasonal_component': decomposition.seasonal,
            'trend_component': decomposition.trend,
            'residual_component': decomposition.resid
        }
        
    except Exception as e:
        print(f"Error in seasonality analysis: {e}")
        return {}
