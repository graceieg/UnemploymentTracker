import folium
from folium.plugins import HeatMap, MarkerCluster
import pandas as pd
from typing import Optional, Dict, List, Tuple, Any, Union
import numpy as np
from branca.colormap import LinearColormap
import json
import os

class UnemploymentMap:
    """Class for creating interactive maps of unemployment and layoff data."""
    
    def __init__(self, 
                location: Tuple[float, float] = (37.0902, -95.7129),  # Center of US
                zoom_start: int = 4,
                tiles: str = 'cartodbpositron'):
        """Initialize the map.
        
        Args:
            location: (lat, lon) tuple for the initial map center
            zoom_start: Initial zoom level
            tiles: Map tiles to use (default: CartoDB Positron)
        """
        self.map = folium.Map(
            location=location,
            zoom_start=zoom_start,
            tiles=tiles,
            control_scale=True
        )
        self.layers = {}
        self.feature_groups = {}
    
    def add_choropleth(self,
                      geo_data: Union[str, Dict],
                      data: pd.DataFrame,
                      columns: Tuple[str, str],
                      key_on: str = 'feature.properties.GEOID',
                      fill_color: str = 'YlOrRd',
                      fill_opacity: float = 0.7,
                      line_opacity: float = 0.2,
                      legend_name: str = 'Unemployment Rate',
                      **kwargs) -> 'UnemploymentMap':
        """Add a choropleth layer to the map.
        
        Args:
            geo_data: GeoJSON string, file path, or dict containing the geometries
            data: DataFrame containing the data to plot
            columns: Tuple of (id_col, value_col) for the data
            key_on: Variable in the GeoJSON to bind the data to
            fill_color: Color scheme for the choropleth
            fill_opacity: Opacity of the fill (0-1)
            line_opacity: Opacity of the boundary lines (0-1)
            legend_name: Title for the legend
            **kwargs: Additional arguments to pass to folium.Choropleth
            
        Returns:
            self for method chaining
        """
        # Create a unique name for the layer
        layer_name = f"Choropleth: {legend_name}"
        
        # Create a feature group for this layer
        self.feature_groups[layer_name] = folium.FeatureGroup(name=layer_name, show=True)
        
        # Create the choropleth
        choropleth = folium.Choropleth(
            geo_data=geo_data,
            data=data,
            columns=columns,
            key_on=key_on,
            fill_color=fill_color,
            fill_opacity=fill_opacity,
            line_opacity=line_opacity,
            legend_name=legend_name,
            highlight=True,
            **kwargs
        ).add_to(self.feature_groups[layer_name])
        
        # Add tooltip with data on hover
        if 'feature.properties.NAME' in geo_data:
            folium.GeoJsonTooltip(
                fields=['NAME', columns[1]],
                aliases=['Location', legend_name],
                style=('background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 2px;')
            ).add_to(choropleth.geojson)
        
        # Add the feature group to the map
        self.feature_groups[layer_name].add_to(self.map)
        self.layers[layer_name] = 'choropleth'
        
        return self
    
    def add_heatmap(self,
                   data: pd.DataFrame,
                   latitude_col: str = 'latitude',
                   longitude_col: str = 'longitude',
                   weight_col: Optional[str] = None,
                   radius: int = 15,
                   blur: int = 15,
                   max_zoom: int = 13,
                   name: str = 'Heatmap',
                   **kwargs) -> 'UnemploymentMap':
        """Add a heatmap layer to the map.
        
        Args:
            data: DataFrame containing the data points
            latitude_col: Name of the latitude column
            longitude_col: Name of the longitude column
            weight_col: Name of the column to use for weights (optional)
            radius: Radius of each point in the heatmap
            blur: Amount of blur
            max_zoom: The maximum zoom level for the heatmap
            name: Name for the layer
            **kwargs: Additional arguments to pass to HeatMap
            
        Returns:
            self for method chaining
        """
        # Create a unique name for the layer
        layer_name = f"Heatmap: {name}"
        
        # Prepare the data
        if weight_col:
            heat_data = data[[latitude_col, longitude_col, weight_col]].values.tolist()
            heat_data = [[x[0], x[1], float(x[2])] for x in heat_data]
        else:
            heat_data = data[[latitude_col, longitude_col]].values.tolist()
        
        # Create a feature group for this layer
        self.feature_groups[layer_name] = folium.FeatureGroup(name=layer_name, show=True)
        
        # Add the heatmap to the feature group
        HeatMap(
            heat_data,
            radius=radius,
            blur=blur,
            max_zoom=max_zoom,
            **kwargs
        ).add_to(self.feature_groups[layer_name])
        
        # Add the feature group to the map
        self.feature_groups[layer_name].add_to(self.map)
        self.layers[layer_name] = 'heatmap'
        
        return self
    
    def add_circle_markers(self,
                         data: pd.DataFrame,
                         latitude_col: str = 'latitude',
                         longitude_col: str = 'longitude',
                         popup_col: Optional[str] = None,
                         tooltip_col: Optional[str] = None,
                         radius: int = 5,
                         color: str = '#3186cc',
                         fill: bool = True,
                         fill_color: Optional[str] = None,
                         fill_opacity: float = 0.7,
                         weight: int = 1,
                         name: str = 'Markers',
                         **kwargs) -> 'UnemploymentMap':
        """Add circle markers to the map.
        
        Args:
            data: DataFrame containing the data points
            latitude_col: Name of the latitude column
            longitude_col: Name of the longitude column
            popup_col: Name of the column to use for popups
            tooltip_col: Name of the column to use for tooltips
            radius: Radius of the markers in pixels
            color: Stroke color
            fill: Whether to fill the markers
            fill_color: Fill color (defaults to stroke color if None)
            fill_opacity: Fill opacity (0-1)
            weight: Stroke width in pixels
            name: Name for the layer
            **kwargs: Additional arguments to pass to CircleMarker
            
        Returns:
            self for method chaining
        """
        # Create a unique name for the layer
        layer_name = f"Markers: {name}"
        
        # Create a feature group for this layer
        self.feature_groups[layer_name] = folium.FeatureGroup(name=layer_name, show=True)
        
        # Create a marker cluster
        marker_cluster = MarkerCluster().add_to(self.feature_groups[layer_name])
        
        # Add each marker
        for _, row in data.iterrows():
            if pd.isna(row[latitude_col]) or pd.isna(row[longitude_col]):
                continue
                
            # Create popup if specified
            popup = None
            if popup_col and popup_col in row:
                popup = str(row[popup_col])
            
            # Create tooltip if specified
            tooltip = None
            if tooltip_col and tooltip_col in row:
                tooltip = str(row[tooltip_col])
            
            # Create the marker
            folium.CircleMarker(
                location=[row[latitude_col], row[longitude_col]],
                radius=radius,
                color=color,
                fill=fill,
                fill_color=fill_color or color,
                fill_opacity=fill_opacity,
                weight=weight,
                popup=popup,
                tooltip=tooltip,
                **kwargs
            ).add_to(marker_cluster)
        
        # Add the feature group to the map
        self.feature_groups[layer_name].add_to(self.map)
        self.layers[layer_name] = 'markers'
        
        return self
    
    def add_layers_control(self, position: str = 'topright') -> 'UnemploymentMap':
        """Add a layers control to the map.
        
        Args:
            position: Position for the control ('topleft', 'topright', 'bottomleft', 'bottomright')
            
        Returns:
            self for method chaining
        """
        if self.feature_groups:
            folium.LayerControl(
                position=position,
                collapsed=False
            ).add_to(self.map)
        
        return self
    
    def add_title(self, title: str, position: str = 'topright', **kwargs) -> 'UnemploymentMap':
        """Add a title to the map.
        
        Args:
            title: Title text
            position: Position for the title ('topleft', 'topright', 'bottomleft', 'bottomright')
            **kwargs: Additional arguments to pass to DivIcon
            
        Returns:
            self for method chaining
        """
        title_html = f'''
            <div style="position: fixed; 
                        {position}: 10px; 
                        z-index:1000; 
                        font-size: 20px; 
                        font-weight: bold;
                        background-color: rgba(255, 255, 255, 0.8);
                        padding: 5px 10px;
                        border-radius: 5px;
                        ">
                {title}
            </div>
        '''
        
        self.map.get_root().html.add_child(folium.Element(title_html))
        return self
    
    def add_legend(self, title: str, colors: List[str], labels: List[str], 
                  position: str = 'bottomright') -> 'UnemploymentMap':
        """Add a legend to the map.
        
        Args:
            title: Title for the legend
            colors: List of colors
            labels: List of labels corresponding to the colors
            position: Position for the legend
            
        Returns:
            self for method chaining
        """
        if len(colors) != len(labels):
            raise ValueError("Number of colors must match number of labels")
        
        # Create the HTML for the legend
        legend_html = f'''
            <div style="position: fixed; 
                        {position}: 10px; 
                        z-index:1000; 
                        background-color: rgba(255, 255, 255, 0.8);
                        padding: 10px;
                        border-radius: 5px;
                        font-family: Arial, sans-serif;
                        font-size: 12px;
                        ">
                <div style="font-weight: bold; margin-bottom: 5px; text-align: center;">
                    {title}
                </div>
        '''
        
        for color, label in zip(colors, labels):
            legend_html += f'''
                <div style="margin: 2px 0;">
                    <i style="background:{color}; width: 12px; height: 12px; 
                            display: inline-block; margin-right: 5px;"></i>
                    {label}
                </div>
            '''
        
        legend_html += "</div>"
        
        self.map.get_root().html.add_child(folium.Element(legend_html))
        return self
    
    def save(self, filepath: str) -> None:
        """Save the map to an HTML file.
        
        Args:
            filepath: Path to save the HTML file
        """
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        # Add layer control if we have multiple layers
        if len(self.feature_groups) > 1:
            self.add_layers_control()
        
        # Save the map
        self.map.save(filepath)
        print(f"Map saved to {filepath}")
    
    def _repr_html_(self) -> str:
        """Display the map in Jupyter notebooks."""
        if self.map._parent is None:
            self.map.add_to(folium.Figure())
        return self.map._parent._repr_html_()
    
    def show(self) -> folium.Map:
        """Display the map in Jupyter notebooks."""
        return self.map
