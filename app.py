import json

from viktor import ViktorController
from viktor.views import DataGroup, DataItem

import json
import rhino3dm
from munch import unmunchify

from viktor import ViktorController
from viktor.views import DataGroup
from viktor.views import DataItem
from viktor.views import GeoJSONAndDataResult
from viktor.views import GeoJSONAndDataView
from viktor.views import MapLabel
from viktor.views import MapPoint
from shapely.geometry import Point
from viktor.external.grasshopper import GrasshopperAnalysis
from viktor.external.generic import GenericAnalysis
from viktor.views import GeometryView
from viktor import File
from pathlib import Path
from viktor.views import GeometryResult

from gis_functions import get_gdf, create_legend
from gis_functions import get_climate_zones
from parametrization import Parametrization, Step


class Controller(ViktorController):
    label = 'My Entity Type'
    parametrization = Parametrization(width=20)

#######################################################
# Views für Step 1 Beinhalten GIS und deren Funktionen#
#######################################################

    @GeoJSONAndDataView("Map", duration_guess=1)
    def get_geojson_view(self, params, **kwargs) -> GeoJSONAndDataResult:
        """Show all the map elements and data results"""
        gdf = get_gdf(params.step_1.styling)
        geojson = json.loads(gdf.to_json())
        gdf_labels = gdf.copy()
        gdf_labels["label_geometry"] = gdf_labels.representative_point()
        labels = [MapLabel(gdf_labels.label_geometry[0].x, gdf_labels.label_geometry[0].x, " ", 20)]

        if 'GeoPointField' in params.step_1.point:
            latitude = params.step_1.point.GeoPointField.lat
            longitude = params.step_1.point.GeoPointField.lon
            point_geojson = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [longitude,latitude]
                },
                "properties": {
                    "marker-symbol": "pin",
                    "marker-color": "#ff0000"
                    # You can add more properties here as needed
                }
            }
        else:
            # Handle case where params.point or GeoPointField does not exist or is None
            print("No valid point information found in params.")    
            
        longitude = round(params.step_1.point.GeoPointField.lon, 3)  # Rundet auf 3 Nachkommastellen (nach norm)
        latitude = round(params.step_1.point.GeoPointField.lat, 2)   # Rundet auf 2 Nachkommastellen (nach norm)

        # Erstellen eines Shapely Point Objekts für den Pin
        point = Point(longitude, latitude)

        # Finde das Polygon im GeoDataFrame 'gdf', das den Punkt enthält
        selected_zone = None
        for idx, row in gdf.iterrows():
            if row['geometry'].contains(point):
                selected_zone = row['climate']
                break

        if selected_zone:
            climate_zone= f"Klimazone am Punkt ({latitude}, {longitude}): {selected_zone}"
        else:
            climate_zone= f"Keine Klimazone am Punkt ({latitude}, {longitude} gefunden)"

        # Add the point_geojson to the features list of geojson_data
        geojson['features'].append(point_geojson)
        data_items = DataItem("", climate_zone)
        attribute_results = DataGroup(data_items)

        legend = create_legend()
        return GeoJSONAndDataResult(geojson, attribute_results, labels, legend)
    

    ################################################
    # Views für Step 2 Beinhaltet Gebäude Geometrie#
    ################################################

    @GeometryView("Modell", duration_guess=10, x_axis_to_right=True, update_label='Run Grasshopper')
    def run_grasshopper(self, params, **kwargs):
        grasshopper_script_path = Path(__file__).parent / "files/Tinyhouse Generator.gh"
        script = File.from_path(grasshopper_script_path)

        input_parameters = unmunchify(params.step_2)

        # Funktion zur Überprüfung und Korrektur der input_parameters
        def ensure_list(value):
            if isinstance(value, (int, float)):
                return [value]
            return value

        # Anwenden der Korrektur auf alle input_parameters
        def format_parameters(parameters):
            formatted_params = {}
            for key, value in parameters.items():
                if isinstance(value, dict):
                    formatted_params[key] = format_parameters(value)
                else:
                    formatted_params[key] = ensure_list(value)
            return formatted_params

        formatted_input_parameters = format_parameters(input_parameters)

        # Grasshopper analyse laufen lassen
        analysis = GrasshopperAnalysis(script=script, input_parameters=formatted_input_parameters)
        analysis.execute(timeout=30)
        output = analysis.get_output()

        # Convert output data to mesh
        file3dm = rhino3dm.File3dm()
        obj = rhino3dm.CommonObject.Decode(json.loads(output["values"][0]["InnerTree"]['{0}'][0]["data"]))
        file3dm.Objects.Add(obj)
        
        # Write to geometry_file
        geometry_file = File()
        file3dm.Write(geometry_file.source, version=7)
        return GeometryResult(geometry=geometry_file, geometry_type="3dm")