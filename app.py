import json
import os
import rhino3dm

from viktor import ViktorController
from viktor.views import DataGroup, DataItem

from viktor.views import GeoJSONAndDataResult, GeometryResult, TableView, TableResult, WebResult
from viktor.views import GeoJSONAndDataView, GeometryView, WebView
from viktor.views import MapLabel

from viktor.external.grasshopper import GrasshopperAnalysis
from viktor import File
from pathlib import Path

from gis_functions import get_gdf, create_legend,find_climate_zone
from json_utils import parse_data_string, read_json_file
from parametrization import Parametrization


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

    @GeometryView("3D Modell", duration_guess=10, x_axis_to_right=True, update_label='Simulation starten')
    def run_grasshopper(self, params, **kwargs):
        grasshopper_script_path = Path(__file__).parent / "files/Tinyhouse Generator.gh"
        script = File.from_path(grasshopper_script_path)

        # Extracting values from the Munch object
        gdf = get_gdf(params.step_1.styling)
        latitude = params.step_1.point.GeoPointField.lat
        longitude = params.step_1.point.GeoPointField.lon
        raumhoehe = params.step_2.geometrie.Raumhöhe
        azimutRichtungEingang = params.step_2.geometrie.AzimutRichtungEingang
        klimazone = find_climate_zone(gdf, latitude, longitude)

        # Creating the dictionary in the required format
        formatted_params = dict(
            Raumhöhe=raumhoehe,
            Längengrad=longitude,
            Breitangrad=latitude,
            Klimazone=klimazone,
            AzimutRichtungEingang=azimutRichtungEingang
        )      

        print(formatted_params)  

        # Run Grasshopper analysis
        analysis = GrasshopperAnalysis(script=script, input_parameters=formatted_params)
        analysis.execute(timeout=240)
        output = analysis.get_output()

        # Save output to a file for later use
        output_path = Path(__file__).parent / "files/grasshopper_output.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=4)
        print(f"Output zwischengespeichert in {output_path}")

        # Convert output data to mesh
        file3dm = rhino3dm.File3dm()
        geometry_inner_tree = output["values"][0]["InnerTree"]
        
        # Format the Text and write to Storage       
        text_inner_tree = output["values"][1]["InnerTree"]
        text_data = text_inner_tree["{0}"][0]["data"]
        formatted_text = text_data.replace("\\r\\n", "\n")
        file_path = os.path.join('files', 'text_data.json')
        text_dict = {"text_lines": formatted_text.split("\n")}
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(text_dict, json_file, ensure_ascii=False, indent=4)
        print(f"Parameter Text information geschrieben in {file_path}")

        # Add Geometry to the model
        def add_objects_to_model(inner_tree):
            for key in inner_tree:
                for data_item in inner_tree[key]:
                    # Decode the object from the JSON data
                    obj = rhino3dm.CommonObject.Decode(json.loads(data_item["data"]))
                    
                    # Add the decoded object to the 3dm file
                    file3dm.Objects.Add(obj)

        add_objects_to_model(geometry_inner_tree)

        # Write to geometry_file
        geometry_file = File()
        file3dm.Write(geometry_file.source, version=7)
        return GeometryResult(geometry=geometry_file, geometry_type="3dm")
    
    @GeometryView("Grundriss", duration_guess=10, x_axis_to_right=True, update_label='Zeige Grundriss',view_mode="2D")
    def view_floorplan(self, params, **kwargs):
        # Load saved Grasshopper output
        output_path = Path(__file__).parent / "files/grasshopper_output.json"
        with open(output_path, 'r', encoding='utf-8') as f:
            output = json.load(f)
        print(f"Output geladen aus {output_path}")

        file3dm = rhino3dm.File3dm()
        floorplan_inner_tree = output["values"][2]["InnerTree"]

        def add_objects_to_model(inner_tree):
            for key in inner_tree:
                for data_item in inner_tree[key]:
                    # Decode the object from the JSON data
                    obj = rhino3dm.CommonObject.Decode(json.loads(data_item["data"]))
                    
                    # Add the decoded object to the 3dm file
                    file3dm.Objects.Add(obj)

        add_objects_to_model(floorplan_inner_tree)

        # Write to geometry_file
        geometry_file = File()
        file3dm.Write(geometry_file.source, version=7)
        return GeometryResult(geometry=geometry_file, geometry_type="3dm")
    
   
    ################################################
    # Views für Step 3 Beinhaltet Datenverarbeitung#
    ################################################



    # Erste Tabelle: Parameter, Werte und Begründungen
    @TableView("Information", duration_guess=1)
    def run_data_analysis(self, params, **kwargs):
        # Parse den String in Parameter- und Wetterdaten
        text_lines = read_json_file(os.path.join('files', 'text_data.json'))
        parameter_data, wetterdaten = parse_data_string(text_lines)

        # Erstelle die Daten für die Tabelle (Parameter/Werte/Begründung)
        table_data = []
        row_headers = []
        for key, value_dict in parameter_data.items():
            row_headers.append(key)  # Füge den Parameternamen als Zeilen-Header hinzu
            table_data.append([value_dict["value"], value_dict["begründung"]])

        # Rückgabe des TableView mit den Daten
        return TableResult(table_data, column_headers=["Wert", "Begründung"], row_headers=row_headers)


    # Zweite Tabelle: Wetterdaten (Schneefall und Niederschlag nach Monaten sortiert)
    @TableView("Wetterdaten", duration_guess=1)
    def run_weather_data(self, params, **kwargs):
        # Parse den String in Parameter- und Wetterdaten
        text_lines = read_json_file(os.path.join('files', 'text_data.json'))
        parameter_data, wetterdaten = parse_data_string(text_lines)

        # Erstelle die Daten für die Wetterdatentabelle
        table_data = []
        row_headers = []
        for monat, daten in wetterdaten.items():
            row_headers.append(monat)
            table_data.append([daten.get("Schneefall [mm]", 0), daten.get("Niederschlag [mm]", 0)])

        # Rückgabe des TableView mit den Wetterdaten
        return TableResult(table_data, column_headers=["Schneefall [mm]", "Niederschlag [mm]"], row_headers=row_headers)
