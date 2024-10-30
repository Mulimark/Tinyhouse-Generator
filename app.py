import json
import rhino3dm
from pathlib import Path

from viktor import ViktorController, File
from viktor.views import DataGroup, DataItem, GeoJSONAndDataResult, GeometryResult, TableResult, TableView, GeoJSONAndDataView, GeometryView, MapLabel
from viktor.external.grasshopper import GrasshopperAnalysis
from viktor.utils import memoize

from gis_functions import get_gdf, create_legend, find_climate_zone
from json_utils import parse_data_string, get_inner_tree_by_param_name
from parametrization import Parametrization

@memoize
def memoized_grasshopper_analysis(json_input):
        #Funktion die die Grasshopper simulation ausführt
        #wird im Arbeitsspeicher zwischengespeichert       
        #Ergebnis kann deswegen mehrfach wieder aufgerufen werden

        formatted_params = json.loads(json_input)


        #Festlegen wo das gh Skript liegt und übergeben der Hops-Parameter an das Skript
        grasshopper_script_path = Path(__file__).parent / "files/Tinyhouse Generator.gh"
        script = File.from_path(grasshopper_script_path)

        analysis = GrasshopperAnalysis(script=script, input_parameters=formatted_params)
        #Analyse wird durchgeführt, sollte sie läger als 240 Sekunden dauern, wird sie angebrochen
        analysis.execute(timeout=240)

        return analysis.get_output()

class Controller(ViktorController):
    label = 'My Entity Type'
    parametrization = Parametrization(width=20)

    #######################################################
    # Views für Step 1 Beinhalten GIS und deren Funktionen#
    #######################################################

    @GeoJSONAndDataView("Kartenansicht - Standortauswahl", duration_guess=1)
    def get_geojson_view(self, params, **kwargs) -> GeoJSONAndDataResult:

        #Kartenansicht mit GroJSON Overlay

        gdf = get_gdf(params.step_1.styling)
        geojson = json.loads(gdf.to_json())
        gdf_labels = gdf.copy()
        gdf_labels["label_geometry"] = gdf_labels.representative_point()
        labels = [MapLabel(gdf_labels.label_geometry[0].x, gdf_labels.label_geometry[0].x, " ", 20)]

        #Festlegen der Position des Pins und das Styling des

        if 'GeoPointField' in params.step_1.point:
            latitude = params.step_1.point.GeoPointField.lat
            longitude = params.step_1.point.GeoPointField.lon
            point_geojson = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [longitude, latitude]
                },
                "properties": {
                    "marker-symbol": "pin",
                    "marker-color": "#ff0000"
                }
            }
        else:
            print("Kein valider Punkt angegeben")

        #Runden des Längen und Breitengrades in übliches Format
        #zur späteren Anzeige in der Webapp

        longitude = round(params.step_1.point.GeoPointField.lon, 3)
        latitude = round(params.step_1.point.GeoPointField.lat, 2)

        selected_zone = find_climate_zone(gdf, latitude, longitude)

        #Wurde eine Korrekte Klimazone ausgewählt?
        if selected_zone:
            climate_zone = f"Klimazone am Punkt ({latitude}, {longitude}): {selected_zone}"
        else:
            climate_zone = f"Keine Klimazone am Punkt ({latitude}, {longitude}) gefunden"

        #Hinzufügen der Information zum View
        geojson['features'].append(point_geojson)
        data_items = DataItem("", climate_zone)
        attribute_results = DataGroup(data_items)
        legend = create_legend()

        #Abrufen der Legende samt Farben
        if params.step_1.styling.showlegend:
            return GeoJSONAndDataResult(geojson, attribute_results, labels, legend)
        else:
            return GeoJSONAndDataResult(geojson, attribute_results, labels)

    ################################################
    # Views für Step 2 Beinhaltet Gebäude Geometrie#
    ################################################



    @GeometryView("3D Modell Ansicht", duration_guess=10, x_axis_to_right=True, update_label='Simulation starten')
    def run_grasshopper(self, params, **kwargs):
        
        #Geometrieanzeige
        #Zunächst initialisierung der Parameter
        gdf = get_gdf(params.step_1.styling)
        latitude = params.step_1.point.GeoPointField.lat
        longitude = params.step_1.point.GeoPointField.lon
        raumhoehe = params.step_2.geometrie.Raumhöhe
        azimutRichtungEingang = params.step_2.geometrie.AzimutRichtungEingang
        klimazone = find_climate_zone(gdf, latitude, longitude)

        formatted_params = dict(
            Raumhöhe=raumhoehe,
            Längengrad=longitude,
            Breitangrad=latitude,
            Klimazone=klimazone,
            AzimutRichtungEingang=azimutRichtungEingang
        )

        #Parameter in ein JSON String damit Hops sie lesen kann
        json_input = json.dumps(formatted_params)

        #memoized Function aufrufen für GH Skript, fragt immer vorher ab ob sich Parameter verändert haben
        output = memoized_grasshopper_analysis(json_input)

        file3dm = rhino3dm.File3dm()
        geometry_inner_tree = get_inner_tree_by_param_name(output, "Geometry")

        #Hinzufügen der Geometrien zum Viewmodel
        def add_objects_to_model(inner_tree):
            if not inner_tree:
                print("Kein InnerTree gefunden.")
                return
            for key in inner_tree:
                for data_item in inner_tree[key]:
                    obj = rhino3dm.CommonObject.Decode(json.loads(data_item["data"]))
                    file3dm.Objects.Add(obj)

        add_objects_to_model(geometry_inner_tree)

        geometry_file = File()
        file3dm.Write(geometry_file.source, version=7)

        return GeometryResult(geometry=geometry_file, geometry_type="3dm")

    @GeometryView("Grundriss und Schnitte", duration_guess=10, x_axis_to_right=True, update_label='Lade aktuellen Grundriss', view_mode="2D")
    def view_floorplan(self, params, **kwargs):

        #2D View für Grundriss und Schnitte
        #Zunächst initialisierung der Parameter
        gdf = get_gdf(params.step_1.styling)
        latitude = params.step_1.point.GeoPointField.lat
        longitude = params.step_1.point.GeoPointField.lon
        raumhoehe = params.step_2.geometrie.Raumhöhe
        azimutRichtungEingang = params.step_2.geometrie.AzimutRichtungEingang
        klimazone = find_climate_zone(gdf, latitude, longitude)

        formatted_params = dict(
            Raumhöhe=raumhoehe,
            Längengrad=longitude,
            Breitangrad=latitude,
            Klimazone=klimazone,
            AzimutRichtungEingang=azimutRichtungEingang
        )

        #Parameter in ein JSON String damit Hops sie lesen kann
        json_input = json.dumps(formatted_params)

        #memoized Function aufrufen für GH Skript, fragt immer vorher ab ob sich Parameter verändert haben
        output = memoized_grasshopper_analysis(json_input)

        file3dm = rhino3dm.File3dm()
        floorplan_inner_tree = output["values"][2]["InnerTree"]

        #Hinzufügen der Geometrien zum Viewmodel
        def add_objects_to_model(inner_tree):
            for key in inner_tree:
                for data_item in inner_tree[key]:
                    obj = rhino3dm.CommonObject.Decode(json.loads(data_item["data"]))
                    file3dm.Objects.Add(obj)

        add_objects_to_model(floorplan_inner_tree)

        geometry_file = File()
        file3dm.Write(geometry_file.source, version=7)
        return GeometryResult(geometry=geometry_file, geometry_type="3dm")

    ################################################
    # Views für Step 3 Beinhaltet Datenverarbeitung#
    ################################################

    @TableView("Informationen zur Parametrisierung", duration_guess=1)
    def run_data_analysis(self, params, **kwargs):

        #Tabelle für Datenansicht
        #Zunächst initialisierung der Parameter
        gdf = get_gdf(params.step_1.styling)
        latitude = params.step_1.point.GeoPointField.lat
        longitude = params.step_1.point.GeoPointField.lon
        raumhoehe = params.step_2.geometrie.Raumhöhe
        azimutRichtungEingang = params.step_2.geometrie.AzimutRichtungEingang
        klimazone = find_climate_zone(gdf, latitude, longitude)

        formatted_params = dict(
            Raumhöhe=raumhoehe,
            Längengrad=longitude,
            Breitangrad=latitude,
            Klimazone=klimazone,
            AzimutRichtungEingang=azimutRichtungEingang
        )

        #Parameter in ein JSON String damit Hops sie lesen kann
        json_input = json.dumps(formatted_params)

        #memoized Function aufrufen für GH Skript, fragt immer vorher ab ob sich Parameter verändert haben
        output = memoized_grasshopper_analysis(json_input)
        text_inner_tree = get_inner_tree_by_param_name(output, "Tx")

        #Hinzufügen der Infos zur richtigen Tabelle
        if text_inner_tree and '{0}' in text_inner_tree:
            #String aus dem Textdata bilden
            text_data = text_inner_tree['{0}'][0]['data']
            formatted_text = text_data.replace("\\r\\n", "\n").splitlines()

            #"Parameter_data" aus dem String herauslesen (erste Ausgabe)
            parameter_data, _ = parse_data_string(formatted_text)

            #Tablle Vorbereiten und hinzufügen der Daten
            table_data = []
            row_headers = []
            for key, value_dict in parameter_data.items():
                row_headers.append(key)
                table_data.append([value_dict["value"], value_dict["begründung"]])

            return TableResult(table_data, column_headers=["Wert", "Begründung"], row_headers=row_headers)
        else:
            print("Keine Daten gefunden")
            return TableResult([], column_headers=["Wert", "Begründung"], row_headers=[])

    @TableView("Wetterdaten", duration_guess=1)
    def run_weather_data(self, params, **kwargs):

        #Tabelle für Wetterdaten
        #Zunächst initialisierung der Parameter
        gdf = get_gdf(params.step_1.styling)
        latitude = params.step_1.point.GeoPointField.lat
        longitude = params.step_1.point.GeoPointField.lon
        raumhoehe = params.step_2.geometrie.Raumhöhe
        azimutRichtungEingang = params.step_2.geometrie.AzimutRichtungEingang
        klimazone = find_climate_zone(gdf, latitude, longitude)

        formatted_params = dict(
            Raumhöhe=raumhoehe,
            Längengrad=longitude,
            Breitangrad=latitude,
            Klimazone=klimazone,
            AzimutRichtungEingang=azimutRichtungEingang
        )

        #Parameter in ein JSON String damit Hops sie lesen kann
        json_input = json.dumps(formatted_params)

        #memoized Function aufrufen für GH Skript, fragt immer vorher ab ob sich Parameter verändert haben
        output = memoized_grasshopper_analysis(json_input)
        text_inner_tree = get_inner_tree_by_param_name(output, "Tx")

        #Hinzufügen der Infos zur richtigen Tabelle
        if text_inner_tree and '{0}' in text_inner_tree:
            #String aus dem Textdata bilden
            text_data = text_inner_tree['{0}'][0]['data']
            formatted_text = text_data.replace("\\r\\n", "\n").splitlines()

            #"wetterdaten" aus dem String herauslesen (zweite Ausgabe)
            _, wetterdaten = parse_data_string(formatted_text)

            #Tablle Vorbereiten und hinzufügen der Daten
            table_data = []
            row_headers = []
            for monat, daten in wetterdaten.items():
                row_headers.append(monat)
                table_data.append([
                    daten.get("Schneefall [mm]", 0),
                    daten.get("Niederschlag [mm]", 0)
                ])

            return TableResult(table_data, column_headers=["Schneefall [mm]", "Niederschlag [mm]"], row_headers=row_headers)
        else:
            print("Keine Daten gefunden")
            return TableResult([], column_headers=["Schneefall [mm]", "Niederschlag [mm]"], row_headers=[])