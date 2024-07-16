import json

from viktor import ViktorController
from viktor.views import DataGroup, DataItem

import json
import rhino3dm
import time
from munch import unmunchify, Munch

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
from io import BytesIO

from gis_functions import get_gdf, create_legend
from gis_functions import find_climate_zone
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

        selected_zone = find_climate_zone(gdf, latitude, longitude)

        # Create the message based on the result
        if selected_zone:
            climate_zone = f"Klimazone am Punkt ({latitude}, {longitude}): {selected_zone}"
        else:
            climate_zone = f"Keine Klimazone am Punkt ({latitude}, {longitude}) gefunden"

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


        # Extracting values from the Munch object
        gdf = gdf = get_gdf(params.step_1.styling)
        latitude = params.step_1.point.GeoPointField.lat
        longitude = params.step_1.point.GeoPointField.lon
        raumhoehe = params.step_2.geometrie.Raumhöhe
        klimazone = find_climate_zone(gdf, latitude, longitude)

        # Creating the dictionary in the required format
        formatted_params = dict(
            Raumhöhe = raumhoehe,
            Längengrad = longitude,
            Breitangrad = latitude,
            Klimazone = klimazone
        )      

        print(formatted_params)  

        # Grasshopper analyse laufen lassen
        analysis = GrasshopperAnalysis(script=script, input_parameters=formatted_params)
        analysis.execute(timeout=180)
        output = analysis.get_output()

        # Convert output data to mesh
        file3dm = rhino3dm.File3dm()
        inner_tree = output["values"][0]["InnerTree"]


        # Iterate through each key in InnerTree
        for key in inner_tree:
            for data_item in inner_tree[key]:
                # Decode the mesh from the JSON data
                obj = rhino3dm.CommonObject.Decode(json.loads(data_item["data"]))
                
                # Add the decoded object to the file3dm
                file3dm.Objects.Add(obj)

        print(output)
        
        # Write to geometry_file
        geometry_file = File()
        file3dm.Write(geometry_file.source, version=7)
        return GeometryResult(geometry=geometry_file, geometry_type="3dm")