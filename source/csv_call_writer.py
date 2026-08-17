"""Write call occurrences to an atomic UTF-8 CSV file."""

import csv
import logging
import os
from pathlib import Path
from types import TracebackType
from typing import Any, TextIO

from call_occurrence import CallOccurrence
from exceptions import OutputCsvError

CSV_HEADER = ("Project", "File", "Caller", "Callee")
LOGGER = logging.getLogger(__name__)


class CsvCallOccurrenceWriter:
    """Write call occurrences atomically without removing duplicates."""

    def __init__(self, output_csv: Path) -> None:
        """Prepare final and temporary output paths."""

        self._output_csv = output_csv
        self._temporary_csv = output_csv.with_name(f".{output_csv.name}.tmp")
        self._file: TextIO | None = None
        self._writer: Any | None = None

    def __enter__(self) -> "CsvCallOccurrenceWriter":
        """Open the temporary CSV and write its header."""

        LOGGER.info("Preparing output CSV: %s", self._output_csv)
        LOGGER.debug("Temporary CSV: %s", self._temporary_csv)
        try:
            self._output_csv.parent.mkdir(parents=True, exist_ok=True)
            self._file = self._temporary_csv.open(
                mode="w",
                newline="",
                encoding="utf-8",
            )
            self._writer = csv.writer(self._file)
            self._writer.writerow(CSV_HEADER)
        except (OSError, csv.Error) as exc:
            self._close_file()
            self._remove_temporary_file()
            raise OutputCsvError(
                f"cannot initialize output CSV '{self._output_csv}': {exc}"
            ) from exc
        return self

    def write_all(self, occurrences: tuple[CallOccurrence, ...]) -> None:
        """Append every occurrence without removing duplicates."""

        if self._writer is None:
            raise OutputCsvError("CSV writer is not open")
        try:
            for occurrence in occurrences:
                self._writer.writerow(occurrence.to_csv_row())
        except (OSError, csv.Error) as exc:
            raise OutputCsvError(
                f"cannot write output CSV '{self._output_csv}': {exc}"
            ) from exc

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        """Publish the completed CSV or discard the temporary file."""

        self._close_file()
        if exception_type is not None:
            self._remove_temporary_file()
            return False

        try:
            os.replace(self._temporary_csv, self._output_csv)
        except OSError as exc:
            self._remove_temporary_file()
            raise OutputCsvError(
                f"cannot publish output CSV '{self._output_csv}': {exc}"
            ) from exc
        LOGGER.info("Published output CSV: %s", self._output_csv)
        return False

    def _close_file(self) -> None:
        """Close the active stream when one exists."""

        if self._file is not None:
            self._file.close()
            self._file = None
        self._writer = None

    def _remove_temporary_file(self) -> None:
        """Best-effort cleanup for an unpublished temporary CSV."""

        try:
            self._temporary_csv.unlink(missing_ok=True)
        except OSError:
            pass
