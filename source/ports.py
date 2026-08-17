"""Declare protocols for external conversion and XML parsing services."""

from pathlib import Path
from typing import Protocol

from call_occurrence import CallOccurrence


class SourceToXmlConverter(Protocol):
    """Port for converting one C source file to srcML XML."""

    def convert(self, c_file: Path) -> bytes:
        """Convert one C source file and return its XML bytes."""

        ...


class CallOccurrenceParser(Protocol):
    """Port for extracting call occurrences from srcML XML."""

    def parse(
        self,
        xml_content: bytes,
        project: str,
        file: str,
    ) -> tuple[CallOccurrence, ...]:
        """Extract caller-callee occurrences from srcML XML."""

        ...
