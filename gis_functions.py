from pathlib import Path
import geopandas as gpd
from shapely.geometry import Point
from geopandas import GeoDataFrame
from viktor.views import MapLegend, Color


#Dictionary welches jeder Klimazone eine Farbe zuweist (in Hex)
climate_colors = {
    'Af Tropical-Rainforest': '#0000ff',
    'Am Tropical-Monsoon': '#0078ff',
    'Aw Tropical-Savanna': '#46aafa',
    'BSh Arid-Steppe-Hot': '#f5a500',
    'BWh Arid-Desert-Hot': '#ff0000',
    'BWk Arid-Desert-Cold': '#ff9696',
    'BSk Arid-Steppe-Cold': '#ffdc64',
    'Cfa Temperate-Withouth_dry_season-Hot_Summer': '#c8ff50',
    'Cfb Temperate-Withouth_dry_season-Warm_Summer': '#64ff50',
    'Cfc Temperate-Withouth_dry_season-Cold_Summer': '#32c800',
    'Csa Temperate-Dry_Summer-Hot_Summer': '#ffff00',
    'Csb Temperate-Dry_Summer-Warm_Summer': '#c8c800',
    'Csc Temperate-Dry_Summer-Cold_Summer': '#969600',
    'Cwa Temperate-Dry_Winter-Hot_Summer': '#96ff96',
    'Cwb Temperate-Dry_Winter-Warm_Summer': '#64c864',
    'Cwc Temperate-Dry_Winter-Cold_Summer': '#329632',
    'Dfa Cold-Withouth_dry_season-Hot_Summer': '#00ffff',
    'Dfb Cold-Withouth_dry_season-Warm_Summer': '#37c8ff',
    'Dfc Cold-Withouth_dry_season-Cold_Summer': '#007d7d',
    'Dfd Cold-Withouth_dry_season-Very_Cold_Winter': '#004a5f',
    'Dsa Cold-Dry_Summer-Hot_Summer': '#ff00ff',
    'Dsb Cold-Dry_Summer-Warm_Summer': '#c800c8',
    'Dsc Cold-Dry_Summer-Cold_Summer': '#963296',
    'Dsd Cold-Dry_Summer-Very_Cold_Winter': '#966496',
    'Dwa Cold-Dry_Winter-Hot_Summer': '#aabfff',
    'Dwb Cold-Dry_Winter-Warm_Summer': '#5a78dc',
    'Dwc Cold-Dry_Winter-Cold_Summer': '#4b50b4',
    'Dwd Cold-Dry_Winter-Very_Cold_Winter': '#320087',
    'EF Polar-Frost': '#666666',
    'ET Polar-Tundra': '#b2b2b2'
    }

def get_gdf(styling) -> GeoDataFrame:
    # Aus GeoJSON eine Geodataframe bilden der dann angezgit werden kann
    #Unter verwendung von verschidenen Styleparametern
    gdf = gpd.read_file(Path(__file__).parent / "files/raw-data.json", crs=4326)
    gdf = gdf.to_crs("EPSG:4326")
    field_names = gdf.columns.drop(["geometry"])
    gdf["fill-opacity"] = styling.opacity
    gdf["stroke-width"] = styling.line_width

    gdf_description = ""
    for field_name in field_names:
        gdf_description = ""
        if 'climate' in gdf.columns:
            gdf_description = "Klimazone: " + gdf['climate'].astype(str) + "  \n  "
        else:
            gdf_description = "Klimazone nicht gefunden  \n  "
    gdf["description"] = gdf_description
    gdf.fillna("")
    
    #Farben aus Dicitionary zu dem gdf hinzufügen
    gdf['fill'] = gdf['climate'].map(climate_colors)
    return gdf

'''
def get_climate_zones():
    """Methode die alle Einzigartigen Klimazonen auflisted, verwendet um Farb Dictionary zu erstellen"""
    gdf = gpd.read_file(Path(__file__).parent / "files/raw-data.json", crs=4326)
    gdf = gdf.to_crs("EPSG:4326")
    climate_list = sorted(gdf['climate'].unique().tolist())
    return climate_list
'''

def create_legend():
    #Baut eine Legende basierend auf dem Farb Dictionary

    legend_items = []

    for climate_zone, color_hex in climate_colors.items():
        color = Color.from_hex(color_hex)
        legend_items.append((color, climate_zone))

    legend = MapLegend(legend_items)
    return legend

def find_climate_zone(gdf, latitude, longitude):
    #indet die Klimazone auf basis von Längen und Breitengrad im GDF
    
    point = Point(longitude, latitude)

    selected_zone = None
    for idx, row in gdf.iterrows():
        if row['geometry'].contains(point):
            selected_zone = row['climate']
            break

    return selected_zone