"""Define immutable result objects returned by an analysis run."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FileAnalysisFailure:
    """Describe one source file that could not be analyzed."""

    project: str
    file: str
    message: str


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """Summarize processed projects, files, calls, and failures."""

    projects: int
    discovered_files: int
    analyzed_files: int
    occurrences: int
    failures: tuple[FileAnalysisFailure, ...]

    @property
    def succeeded(self) -> bool:
        """Return whether the run finished without file-level failures."""

        return not self.failures
