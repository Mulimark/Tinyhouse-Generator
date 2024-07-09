from ..core import File as File
from .external_program import ExternalProgram as ExternalProgram
from _typeshed import Incomplete
from io import BytesIO

class DGeoStabilityAnalysis(ExternalProgram):
    input_file: Incomplete
    def __init__(self, input_file: BytesIO | File) -> None: ...
    def get_output_file(self, extension: str = '.sto', *, as_file: bool = False) -> BytesIO | File | None: ...
