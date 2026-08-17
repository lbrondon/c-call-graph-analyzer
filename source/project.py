"""Represent a project discovered below the configured input directory."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Project:
    """A C project stored below the configured projects directory."""

    name: str
    root: Path
