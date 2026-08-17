"""Store validated configuration for one analyzer execution."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AnalyzerConfig:
    """Immutable configuration for one analyzer execution."""

    projects_dir: Path
    output_csv: Path
    srcml_executable: str = "srcml"

    def __post_init__(self) -> None:
        """Reject an empty srcML executable name."""

        if not self.srcml_executable.strip():
            raise ValueError("srcml_executable cannot be empty")
