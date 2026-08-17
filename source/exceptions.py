"""Define expected failures raised by the call graph analyzer."""


class CallGraphAnalyzerError(Exception):
    """Base exception for expected call graph analyzer failures."""


class ProjectsDirectoryError(CallGraphAnalyzerError):
    """Raised when the projects directory cannot be used."""


class ProjectScanError(CallGraphAnalyzerError):
    """Raised when C files cannot be discovered in a project."""


class SrcMLNotAvailableError(CallGraphAnalyzerError):
    """Raised when the srcML executable is unavailable."""


class SrcMLExecutionError(CallGraphAnalyzerError):
    """Raised when srcML cannot convert a C source file."""


class SrcMLParseError(CallGraphAnalyzerError):
    """Raised when srcML XML cannot be parsed."""


class OutputCsvError(CallGraphAnalyzerError):
    """Raised when the output CSV cannot be created or written."""
