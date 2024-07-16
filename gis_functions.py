"""Copyright (c) 2024 VIKTOR B.V.
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.
VIKTOR B.V. PROVIDES THIS SOFTWARE ON AN "AS IS" BASIS, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point
from geopandas import GeoDataFrame
from viktor.views import MapLegend, Color

climate_colors = {
        'ET Polar-Tundra': '#1f78b4',
        'EF Polar-Frost': '#a6cee3',
        'Aw Tropical-Savanna': '#33a02c',
        'BSh Arid-Steppe-Hot': '#e31a1c',
        'BWh Arid-Desert-Hot': '#ff7f00',
        'Af Tropical-Rainforest': '#b2df8a',
        'Dsa Cold-Dry_Summer-Hot_Summer': '#6a3d9a',
        'Am Tropical-Monsoon': '#fb9a99',
        'Dwa Cold-Dry_Winter-Hot_Summer': '#cab2d6',
        'BSk Arid-Steppe-Cold': '#fdbf6f',
        'Dwb Cold-Dry_Winter-Warm_Summer': '#ff7f00',
        'Dfa Cold-Withouth_dry_season-Hot_Summer': '#b15928',
        'Dfb Cold-Withouth_dry_season-Warm_Summer': '#ffff99',
        'Csb Temperate-Dry_Summer-Warm_Summer': '#a6cee3',
        'Dfc Cold-Withouth_dry_season-Cold_Summer': '#1f78b4',
        'Cfc Temperate-Withouth_dry_season-Cold_Summer': '#b2df8a',
        'BWk Arid-Desert-Cold': '#ff7f00',
        'Cfa Temperate-Withouth_dry_season-Hot_Summer': '#e31a1c',
        'Cfb Temperate-Withouth_dry_season-Warm_Summer': '#33a02c',
        'Csa Temperate-Dry_Summer-Hot_Summer': '#fb9a99',
        'Dwc Cold-Dry_Winter-Cold_Summer': '#6a3d9a',
        'Dsb Cold-Dry_Summer-Warm_Summer': '#ffff99',
        'Cwa Temperate-Dry_Winter-Hot_Summer': '#ff7f00',
        'Dsc Cold-Dry_Summer-Cold_Summer': '#cab2d6',
        'Cwb Temperate-Dry_Winter-Warm_Summer': '#fdbf6f',
        'Cwc Temperate-Dry_Winter-Cold_Summer': '#1f78b4',
        'Dfd Cold-Withouth_dry_season-Very_Cold_Winter': '#b15928',
        'Dsd Cold-Dry_Summer-Very_Cold_Winter': '#cab2d6',
        'Dwd Cold-Dry_Winter-Very_Cold_Winter': '#6a3d9a'
    }

def get_gdf(styling) -> GeoDataFrame:
    # Add attribute table to the geodataframe as a string, so it can be added to the map as a click-event
    gdf = gpd.read_file(Path(__file__).parent / "files/raw-data.json", crs=4326)
    gdf = gdf.to_crs("EPSG:4326")
    field_names = gdf.columns.drop(["geometry"])
    gdf["fill-opacity"] = styling.opacity
    gdf["stroke-width"] = styling.line_width

    # Add attribute table to the geodataframe as a string, so it can be added to the map as a click-event
    gdf_description = ""
    for field_name in field_names:
        gdf_description = ""
        if 'climate' in gdf.columns:
            gdf_description = "Klimazone: " + gdf['climate'].astype(str) + "  \n  "
        else:
            gdf_description = "Klimazone nicht gefunden  \n  "
    gdf["description"] = gdf_description
    gdf.fillna("")  # Get rid of NaN-values, which can cause problems with some calculations
    
    # Assign colors based on climate zones
    gdf['fill'] = gdf['climate'].map(climate_colors)
    return gdf


def get_climate_zones():
    """Returns a list of unique climate zones in the GeoDataFrame."""
    gdf = gpd.read_file(Path(__file__).parent / "files/raw-data.json", crs=4326)
    gdf = gdf.to_crs("EPSG:4326")
    climate_list = sorted(gdf['climate'].unique().tolist())
    return climate_list

def create_legend():
    """Creates a map legend based on climate zones and their colors."""
    legend_items = []

    for climate_zone, color_hex in climate_colors.items():
        color = Color.from_hex(color_hex)
        legend_items.append((color, climate_zone))

    legend = MapLegend(legend_items)
    return legend

def find_climate_zone(gdf, latitude, longitude):
    """
    Find the climate zone for a given latitude and longitude.

    Parameters:
    gdf (GeoDataFrame): A GeoDataFrame containing climate zone geometries.
    latitude (float): The latitude of the point.
    longitude (float): The longitude of the point.

    Returns:
    str: The name of the climate zone or None if not found.
    """
    point = Point(longitude, latitude)  # Note the order: (longitude, latitude)

    selected_zone = None
    for idx, row in gdf.iterrows():
        if row['geometry'].contains(point):
            selected_zone = row['climate']
            break

    return selected_zone  # Return the climate zone name or None if not found