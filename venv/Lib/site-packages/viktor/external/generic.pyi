from ..core import File as File
from ..errors import ExecutionError as ExecutionError, LicenseError as LicenseError
from .external_program import ExternalProgram as ExternalProgram
from io import BytesIO

class GenericAnalysis(ExternalProgram):
    def __init__(self, files: list[tuple[str, BytesIO | File]] = None, executable_key: str = None, output_filenames: list[str] = None) -> None: ...
    def get_output_file(self, filename: str, *, as_file: bool = False) -> BytesIO | File | None: ...
