from viktor.geometry import GeoPoint
from viktor.parametrization import (
    GeoPointField,
    NumberField,
    Step,
    Section,
    ViktorParametrization,
)


DEFAULT_LOCATION = GeoPoint(49.8728, 8.6512)



class Parametrization(ViktorParametrization):

#Step 1 Ist auswahl von Location und Übergabe von Klimazone in GH Modell

    step_1 = Step('Step 1 - Map',  views=["get_geojson_view"])
    step_1.point = Section("Loctaion")
    step_1.point.GeoPointField= GeoPointField("Enter a Location",
    description="Click a place on the map to select it. Delete the old Location beforehand",
    default=DEFAULT_LOCATION,)
  
    step_1.styling = Section("Styling")
    step_1.styling.opacity = NumberField("Opacity", variant="slider", min=0, max=1, step=0.1, default=0.5)
    step_1.styling.line_width = NumberField("Line width", variant="slider", min=0, max=5, default=1)

#Step 2 Ist Festlegen von Parametern für Das Gebäude

    step_2 = Step('Step - 2 Gebäude', views=["run_grasshopper", "view_floorplan"])
    
    step_2.geometrie = Section("Geometrie")
    step_2.geometrie.Raumhöhe = NumberField("Raumhöhe", variant="slider", min=2.3, max=4, step=0.1, default=2.5)
    step_2.geometrie.AzimutRichtungEingang = NumberField('Azimut Richtung Eingang', min=0, max=360, default=90, variant='slider', description="Richtung des Eingangs in Grad. 0° = Norden 90° = Osten etc.")


    Step('Step 2', previous_label='Go to step 1', next_label='Go to step 3')

#Step 3 Ist Festlegen von Parametern für Das Gebäude

    step_3 = Step('Step - 3 Daten', views=["run_data_analysis", "run_weather_data"])