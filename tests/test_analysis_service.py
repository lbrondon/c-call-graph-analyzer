"""Test orchestration, partial failures, and duplicate preservation."""

import csv
import tempfile
import unittest
from pathlib import Path

from analysis_service import CallGraphAnalysisService
from c_file_scanner import CFileScanner
from call_occurrence import CallOccurrence
from exceptions import SrcMLExecutionError
from project_discovery import ProjectDiscovery


class SelectiveConverter:
    """Test converter that fails only for a file named bad.c."""

    def convert(self, c_file: Path) -> bytes:
        """Return minimal XML or raise the planned conversion error."""

        if c_file.name == "bad.c":
            raise SrcMLExecutionError("conversion failed")
        return b"<unit />"


class DuplicateCallParser:
    """Test parser that returns the same occurrence twice."""

    def parse(
        self,
        xml_content: bytes,
        project: str,
        file: str,
    ) -> tuple[CallOccurrence, ...]:
        """Return two equal occurrences for duplicate-preservation tests."""

        occurrence = CallOccurrence(project, file, "caller", "callee")
        return occurrence, occurrence


class CallGraphAnalysisServiceTests(unittest.TestCase):
    """Verify the complete analysis orchestration service."""

    def test_continues_after_file_failure_and_preserves_duplicates(self) -> None:
        """Keep valid rows when another source file fails conversion."""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "projects" / "sample"
            project.mkdir(parents=True)
            (project / "good.c").write_text("void good(void) {}")
            (project / "bad.c").write_text("invalid")
            output_csv = root / "output" / "calls.csv"

            service = CallGraphAnalysisService(
                project_discovery=ProjectDiscovery(),
                file_scanner=CFileScanner(),
                xml_converter=SelectiveConverter(),
                call_parser=DuplicateCallParser(),
            )
            with self.assertLogs("analysis_service", level="DEBUG") as captured:
                result = service.analyze(root / "projects", output_csv)

            with output_csv.open(newline="", encoding="utf-8") as csv_file:
                rows = list(csv.reader(csv_file))

        self.assertEqual(1, result.projects)
        self.assertEqual(2, result.discovered_files)
        self.assertEqual(1, result.analyzed_files)
        self.assertEqual(2, result.occurrences)
        self.assertEqual(1, len(result.failures))
        self.assertEqual("bad.c", result.failures[0].file)
        self.assertEqual(rows[1], rows[2])
        messages = "\n".join(captured.output)
        self.assertIn("Projects discovered: 1", messages)
        self.assertIn("Project 'sample': C files found: 2", messages)
        self.assertIn("analyzing bad.c", messages)
        self.assertIn("bad.c (conversion failed)", messages)
        self.assertIn("Overall progress: 2/2 files processed (100%)", messages)
        self.assertIn("Completed project 1/1 'sample'", messages)


if __name__ == "__main__":
    unittest.main()
