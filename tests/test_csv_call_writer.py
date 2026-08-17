"""Test CSV formatting, duplicate rows, and atomic publication."""

import csv
import tempfile
import unittest
from pathlib import Path

from call_occurrence import CallOccurrence
from csv_call_writer import CsvCallOccurrenceWriter


class CsvCallOccurrenceWriterTests(unittest.TestCase):
    """Verify CsvCallOccurrenceWriter output guarantees."""

    def test_writes_header_and_preserves_duplicate_occurrences(self) -> None:
        """Write the header and every repeated occurrence."""

        occurrence = CallOccurrence("project", "file.c", "caller", "callee")

        with tempfile.TemporaryDirectory() as directory:
            output_csv = Path(directory) / "output" / "calls.csv"
            with self.assertLogs("csv_call_writer", level="INFO") as captured:
                with CsvCallOccurrenceWriter(output_csv) as writer:
                    writer.write_all((occurrence, occurrence))

            with output_csv.open(newline="", encoding="utf-8") as csv_file:
                rows = list(csv.reader(csv_file))

        self.assertEqual(
            [
                ["Project", "File", "Caller", "Callee"],
                ["project", "file.c", "caller", "callee"],
                ["project", "file.c", "caller", "callee"],
            ],
            rows,
        )
        messages = "\n".join(captured.output)
        self.assertIn("Preparing output CSV", messages)
        self.assertIn("Published output CSV", messages)

    def test_does_not_publish_csv_when_context_fails(self) -> None:
        """Remove temporary output when the writer context fails."""

        with tempfile.TemporaryDirectory() as directory:
            output_csv = Path(directory) / "calls.csv"
            with self.assertRaisesRegex(RuntimeError, "stop"):
                with CsvCallOccurrenceWriter(output_csv):
                    raise RuntimeError("stop")

            self.assertFalse(output_csv.exists())
            self.assertFalse((Path(directory) / ".calls.csv.tmp").exists())


if __name__ == "__main__":
    unittest.main()
