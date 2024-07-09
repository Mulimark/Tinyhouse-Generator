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


from viktor.parametrization import NumberField
from viktor.parametrization import ViktorParametrization

from munch import Munch
from viktor.errors import UserError
from viktor.geometry import GeoPoint
from viktor.parametrization import (
    GeoPointField,
    NumberField,
    OptionField,
    Parametrization,
    Step,
    Text,
    ToggleButton,
)
from viktor.parametrization import (
    NumberField,
    Section,
    NumberField,
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

    step_2 = Step('Step - 2 Gebäude', views=["run_grasshopper"])
    
    step_2.geometrie = Section("Geometrie")
    step_2.geometrie.Raumhöhe = NumberField("Raumhöhe", variant="slider", min=2, max=5, step=0.1, default=2.5)


    Step('Step 2', previous_label='Go to step 1', next_label='Go to step 3')