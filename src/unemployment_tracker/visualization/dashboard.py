import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import json
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

# Custom imports
from processing.trend_detector import TrendDetector, TrendDirection
from visualization.map_view import UnemploymentMap

class UnemploymentDashboard:
    """Streamlit dashboard for unemployment data visualization."""
    
    def __init__(self, data_dir: str = '../data'):
        """Initialize the dashboard.
        
        Args:
            data_dir: Directory containing the data files
        """
        self.data_dir = data_dir
        self.trend_detector = TrendDetector()
        self._load_data()
        self._setup_page_config()
    
    def _setup_page_config(self):
        """Configure the Streamlit page settings."""
        st.set_page_config(
            page_title="Unemployment Tracker",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS for better styling
        st.markdown("""
        <style>
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            .stButton>button {
                width: 100%;
            }
            .stSelectbox, .stSlider, .stDateInput {
                margin-bottom: 1rem;
            }
            .stAlert {
                border-radius: 0.5rem;
            }
            .metric-card {
                background-color: #f8f9fa;
                border-radius: 0.5rem;
                padding: 1rem;
                margin-bottom: 1rem;
                box-shadow: 0 0.15rem 0.5rem rgba(0,0,0,0.1);
            }
            .metric-value {
                font-size: 1.8rem;
                font-weight: bold;
                color: #1f77b4;
            }
            .metric-label {
                font-size: 0.9rem;
                color: #6c757d;
            }
        </style>
        """, unsafe_allow_html=True)
    
    def _load_data(self):
        """Load the unemployment and layoff data."""
        try:
            # Load unemployment data
            self.unemployment_df = pd.read_csv(
                os.path.join(self.data_dir, 'processed', 'bls_unemployment.csv'),
                parse_dates=['date']
            )
            
            # Load layoff data
            self.layoff_df = pd.read_csv(
                os.path.join(self.data_dir, 'processed', 'processed_layoffs.csv'),
                parse_dates=['date_announced'],
                low_memory=False
            )
            
            # Convert date columns to datetime if they exist
            date_columns = ['date_added', 'last_updated']
            for col in date_columns:
                if col in self.layoff_df.columns:
                    self.layoff_df[col] = pd.to_datetime(
                        self.layoff_df[col], 
                        errors='coerce'
                    )
            
            # Set default date range
            today = datetime.today()
            self.min_date = self.unemployment_df['date'].min().to_pydatetime()
            self.max_date = self.unemployment_df['date'].max().to_pydatetime()
            
            # Default to last 2 years of data
            self.default_start_date = max(
                self.min_date,
                today - timedelta(days=730)  # ~2 years
            )
            
            # Get unique values for filters
            self.demographics = sorted(self.unemployment_df['demographic'].unique())
            self.industries = sorted(self.layoff_df['industry'].dropna().unique())
            self.companies = sorted(self.layoff_df['company'].dropna().unique())
            
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            self.unemployment_df = pd.DataFrame()
            self.layoff_df = pd.DataFrame()
    
    def _create_sidebar(self):
        """Create the sidebar with filters and controls."""
        st.sidebar.title("Filters")
        
        # Date range filter
        st.sidebar.subheader("Date Range")
        start_date = st.sidebar.date_input(
            "Start Date",
            value=self.default_start_date,
            min_value=self.min_date,
            max_value=self.max_date
        )
        
        end_date = st.sidebar.date_input(
            "End Date",
            value=self.max_date,
            min_value=self.min_date,
            max_value=self.max_date
        )
        
        self.date_range = (start_date, end_date)
        
        # Demographic filter
        st.sidebar.subheader("Demographics")
        selected_demographics = st.sidebar.multiselect(
            "Select Demographics",
            options=self.demographics,
            default=["total"],  # Default to total
            key="demographic_filter"
        )
        
        # Industry filter
        st.sidebar.subheader("Industries")
        selected_industries = st.sidebar.multiselect(
            "Select Industries",
            options=self.industries,
            default=[],  # Default to all
            key="industry_filter"
        )
        
        # Company filter
        st.sidebar.subheader("Companies")
        selected_companies = st.sidebar.multiselect(
            "Select Companies",
            options=self.companies,
            default=[],  # Default to all
            key="company_filter"
        )
        
        # Update filters
        self.filters = {
            'demographics': selected_demographics,
            'industries': selected_industries,
            'companies': selected_companies
        }
        
        # Add some space and a link to data sources
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Data Sources")
        st.sidebar.markdown("""
        - [Bureau of Labor Statistics](https://www.bls.gov/)
        - [Layoffs.fyi](https://layoffs.fyi/)
        - [US Census Bureau](https://www.census.gov/)
        """)
    
    def _filter_data(self):
        """Filter the data based on user selections."""
        try:
            # Initialize filtered data with empty DataFrames
            self.filtered_unemployment = pd.DataFrame()
            self.filtered_layoffs = pd.DataFrame()
            
            # Check if we have the necessary data
            if not hasattr(self, 'unemployment_df') or self.unemployment_df.empty:
                st.warning("No unemployment data available.")
                return
                
            if not hasattr(self, 'layoff_df'):
                self.layoff_df = pd.DataFrame()
                
            # Filter by date range
            start_date, end_date = self.date_range
            
            # Filter unemployment data
            if not self.unemployment_df.empty:
                mask = (
                    (self.unemployment_df['date'] >= pd.Timestamp(start_date)) & 
                    (self.unemployment_df['date'] <= pd.Timestamp(end_date))
                )
                
                if 'demographics' in self.filters and self.filters['demographics']:
                    mask &= self.unemployment_df['demographic'].isin(self.filters['demographics'])
                
                self.filtered_unemployment = self.unemployment_df[mask].copy()
            
            # Filter layoff data if available
            if not self.layoff_df.empty:
                mask = (
                    (self.layoff_df['date_announced'] >= pd.Timestamp(start_date)) & 
                    (self.layoff_df['date_announced'] <= pd.Timestamp(end_date))
                )
                
                if 'industries' in self.filters and self.filters['industries']:
                    mask &= self.layoff_df['industry'].isin(self.filters['industries'])
                    
                if 'companies' in self.filters and self.filters['companies']:
                    mask &= self.layoff_df['company'].isin(self.filters['companies'])
                
                self.filtered_layoffs = self.layoff_df[mask].copy()
                
        except Exception as e:
            st.error(f"Error filtering data: {str(e)}")
            # Initialize empty DataFrames to prevent further errors
            self.filtered_unemployment = pd.DataFrame()
            self.filtered_layoffs = pd.DataFrame()
    
    def _display_summary_metrics(self):
        """Display summary metrics at the top of the dashboard."""
        try:
            # Check if we have valid data
            if not hasattr(self, 'filtered_unemployment') or self.filtered_unemployment is None or self.filtered_unemployment.empty:
                st.warning("No unemployment data available for the selected filters.")
                return
            
            # Calculate metrics
            latest_date = self.filtered_unemployment['date'].max()
            latest_data = self.filtered_unemployment[
                self.filtered_unemployment['date'] == latest_date
            ]
            
            # Get the latest unemployment rate for the total demographic
            total_unemployment_data = latest_data[
                latest_data['demographic'] == 'total'
            ]
            
            if total_unemployment_data.empty:
                st.warning("No total unemployment data available for the selected period.")
                return
                
            total_unemployment = total_unemployment_data['value'].values[0]
            
            # Ensure we have a valid number
            if pd.isna(total_unemployment):
                st.warning("Invalid unemployment data for the selected period.")
                return
            
            # Calculate month-over-month change if we have enough data
            mom_change = None
            mom_change_pct = None
            
            if len(self.filtered_unemployment) > 1:
                try:
                    # Get previous month's data
                    prev_month_mask = (self.filtered_unemployment['date'] < latest_date)
                    if prev_month_mask.any():
                        # Get the most recent previous month's data
                        prev_month_data = self.filtered_unemployment[prev_month_mask]\
                            .sort_values('date', ascending=False)
                        
                        if not prev_month_data.empty:
                            # Get the total unemployment for the previous month
                            prev_month_total_data = prev_month_data[
                                prev_month_data['demographic'] == 'total'
                            ]
                            
                            if not prev_month_total_data.empty:
                                prev_month_total = prev_month_total_data['value'].iloc[0]
                                
                                if not pd.isna(prev_month_total):
                                    mom_change = total_unemployment - prev_month_total
                                    mom_change_pct = (mom_change / prev_month_total) * 100 if prev_month_total != 0 else 0
                except Exception as e:
                    # Don't show the error to the user, just log it
                    import logging
                    logging.warning(f"Could not calculate month-over-month change: {str(e)}")
                    logging.debug(f"Debug info: {traceback.format_exc()}")
                    # Don't show a warning to the user to avoid cluttering the UI
            
            # Get layoff data if available
            layoff_count = 0
            company_count = 0
            if hasattr(self, 'filtered_layoffs') and self.filtered_layoffs is not None:
                layoff_count = int(self.filtered_layoffs['employees_laid_off'].sum())
                company_count = len(self.filtered_layoffs)
            
            # Create columns for the metrics
            col1, col2, col3 = st.columns(3)
            
            # Current Unemployment Rate
            with col1:
                st.metric(
                    "Current Unemployment Rate",
                    f"{total_unemployment:.1f}%",
                    f"{mom_change_pct:+.1f}% MoM" if mom_change_pct is not None else None,
                    delta_color="inverse"
                )
            
            # Total Layoffs
            with col2:
                st.metric(
                    "Total Layoffs",
                    f"{layoff_count:,}",
                    f"{company_count} companies" if company_count > 0 else "No data"
                )
            
            # Average Unemployment Rate
            with col3:
                avg_unemployment = self.filtered_unemployment['value'].mean()
                st.metric(
                    "Avg. Unemployment Rate",
                    f"{avg_unemployment:.1f}%",
                    f"{len(self.filtered_unemployment)} data points"
                )
                
        except Exception as e:
            st.error(f"Error displaying summary metrics: {str(e)}")
    
    def _display_unemployment_trends(self):
        """Display unemployment trends over time."""
        if self.filtered_unemployment.empty:
            return
        
        st.subheader("Unemployment Trends")
        
        # Pivot the data for plotting
        pivot_df = self.filtered_unemployment.pivot(
            index='date',
            columns='demographic',
            values='value'
        ).reset_index()
        
        # Create the plot
        fig = px.line(
            pivot_df,
            x='date',
            y=pivot_df.columns[1:],  # Skip the date column
            title="Unemployment Rate Over Time",
            labels={'value': 'Unemployment Rate (%)', 'date': 'Date'},
            height=500
        )
        
        # Update layout
        fig.update_layout(
            legend_title_text='Demographic',
            hovermode='x unified',
            xaxis_title='Date',
            yaxis_title='Unemployment Rate (%)',
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        # Add range slider
        fig.update_xaxes(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _display_layoff_analysis(self):
        """Display layoff analysis."""
        if self.filtered_layoffs.empty:
            return
        
        st.subheader("Layoff Analysis")
        
        # Group by industry and sum layoffs
        industry_layoffs = self.filtered_layoffs.groupby('industry').agg({
            'employees_laid_off': 'sum',
            'company': 'count'
        }).reset_index().sort_values('employees_laid_off', ascending=False)
        
        # Create two columns for the charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Top industries by layoffs
            fig = px.bar(
                industry_layoffs.head(10),
                x='employees_laid_off',
                y='industry',
                orientation='h',
                title='Top 10 Industries by Layoffs',
                labels={'employees_laid_off': 'Number of Employees Laid Off', 'industry': 'Industry'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Layoffs by company size
            if 'total_employees' in self.filtered_layoffs.columns:
                # Calculate layoff percentage if total employees data is available
                self.filtered_layoffs['layoff_percentage'] = (
                    self.filtered_layoffs['employees_laid_off'] / 
                    self.filtered_layoffs['total_employees'] * 100
                )
                
                # Get top 10 companies by layoff percentage
                top_companies = self.filtered_layoffs.nlargest(10, 'layoff_percentage')
                
                fig = px.bar(
                    top_companies,
                    x='layoff_percentage',
                    y='company',
                    orientation='h',
                    title='Top 10 Companies by Layoff Percentage',
                    labels={'layoff_percentage': 'Layoff Percentage (%)', 'company': 'Company'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                # Fallback to top companies by layoff count
                top_companies = self.filtered_layoffs.groupby('company').agg({
                    'employees_laid_off': 'sum'
                }).reset_index().nlargest(10, 'employees_laid_off')
                
                fig = px.bar(
                    top_companies,
                    x='employees_laid_off',
                    y='company',
                    orientation='h',
                    title='Top 10 Companies by Layoff Count',
                    labels={'employees_laid_off': 'Number of Employees Laid Off', 'company': 'Company'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Add a map of layoffs by location if we have location data
        if 'latitude' in self.filtered_layoffs.columns and 'longitude' in self.filtered_layoffs.columns:
            st.subheader("Layoff Map")
            
            # Create a map centered on the US
            umap = UnemploymentMap(
                location=(37.0902, -95.7129),  # Center of US
                zoom_start=4
            )
            
            # Add circle markers for layoffs
            umap.add_circle_markers(
                data=self.filtered_layoffs,
                latitude_col='latitude',
                longitude_col='longitude',
                popup_col='company',
                tooltip_col='employees_laid_off',
                radius=10,
                color='#ff4b4b',
                fill=True,
                fill_opacity=0.7,
                weight=1,
                name='Layoffs'
            )
            
            # Add a title to the map
            umap.add_title("Company Layoffs by Location")
            
            # Display the map
            st.components.v1.html(umap.map._repr_html_(), height=500)
    
    def _display_trend_analysis(self):
        """Display trend analysis of unemployment data."""
        if self.filtered_unemployment.empty:
            return
        
        st.subheader("Trend Analysis")
        
        # Analyze trends for each demographic
        trend_results = {}
        for demo in self.filtered_unemployment['demographic'].unique():
            demo_data = self.filtered_unemployment[
                self.filtered_unemployment['demographic'] == demo
            ]
            
            if len(demo_data) < 3:  # Need at least 3 points for trend analysis
                continue
                
            result = self.trend_detector.detect_trends(
                demo_data,
                value_col='value',
                date_col='date',
                group_cols=['demographic']
            )
            
            if result:
                trend_results[demo] = result[demo]
        
        # Display trend results
        if not trend_results:
            st.info("Not enough data points for trend analysis.")
            return
        
        # Create a DataFrame for display
        trend_data = []
        for demo, trend in trend_results.items():
            trend_data.append({
                'Demographic': demo.capitalize(),
                'Trend': trend.direction.value.capitalize(),
                'Magnitude': f"{trend.magnitude:.1%}",
                'Confidence': f"{trend.confidence:.0%}",
                'Start Value': f"{trend.start_value:.1f}%",
                'End Value': f"{trend.end_value:.1f}%"
            })
        
        # Sort by trend direction and magnitude
        trend_df = pd.DataFrame(trend_data).sort_values(
            by=['Trend', 'Magnitude'], 
            ascending=[True, False]
        )
        
        # Display the table with conditional formatting
        st.dataframe(
            trend_df,
            column_config={
                'Trend': st.column_config.SelectboxColumn(
                    'Trend',
                    options=[d.value.capitalize() for d in TrendDirection],
                    width='small'
                ),
                'Magnitude': st.column_config.ProgressColumn(
                    'Magnitude',
                    format='%f',
                    min_value=0,
                    max_value=1.0
                )
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Add some context
        st.caption(
            "Trend analysis shows the direction and strength of unemployment trends "
            "over the selected time period. Confidence indicates how well the trend "
            "fits the data (higher is better)."
        )
    
    def run(self):
        """Run the dashboard."""
        # Set the title and description
        st.title("📊 Unemployment Tracker")
        st.markdown(
            "Track unemployment trends, analyze layoffs, and monitor labor market shifts "
            "across different demographics and industries."
        )
        
        # Create the sidebar
        self._create_sidebar()
        
        # Filter the data
        self._filter_data()
        
        # Display the main content
        self._display_summary_metrics()
        
        # Add tabs for different sections
        tab1, tab2, tab3 = st.tabs(["Unemployment Trends", "Layoff Analysis", "Trend Analysis"])
        
        with tab1:
            self._display_unemployment_trends()
        
        with tab2:
            self._display_layoff_analysis()
        
        with tab3:
            self._display_trend_analysis()
        
        # Add a footer
        st.markdown("---")
        st.caption(
            "Data Sources: Bureau of Labor Statistics (BLS), Layoffs.fyi | "
            "Last updated: " + datetime.now().strftime("%Y-%m-%d")
        )


if __name__ == "__main__":
    # Create and run the dashboard
    dashboard = UnemploymentDashboard()
    dashboard.run()
