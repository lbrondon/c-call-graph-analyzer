"""Test srcML executable discovery and subprocess error handling."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from exceptions import SrcMLExecutionError, SrcMLNotAvailableError
from srcml_runner import SrcMLRunner


class SrcMLRunnerTests(unittest.TestCase):
    """Verify SrcMLRunner command execution behavior."""

    @patch("srcml_runner.subprocess.run")
    @patch("srcml_runner.shutil.which")
    def test_converts_source_file_to_xml(self, which, run) -> None:
        """Return stdout when srcML converts a file successfully."""

        which.return_value = "/usr/bin/srcml"
        run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=b"<unit />",
            stderr=b"",
        )
        source_file = Path("project/example.c")

        xml_content = SrcMLRunner().convert(source_file)

        self.assertEqual(b"<unit />", xml_content)
        run.assert_called_once_with(
            ["/usr/bin/srcml", str(source_file)],
            check=False,
            capture_output=True,
        )

    @patch("srcml_runner.shutil.which")
    def test_reports_missing_srcml(self, which) -> None:
        """Report an executable that cannot be resolved."""

        which.return_value = None

        with self.assertRaises(SrcMLNotAvailableError):
            SrcMLRunner()

    @patch("srcml_runner.subprocess.run")
    @patch("srcml_runner.shutil.which")
    def test_reports_srcml_failure(self, which, run) -> None:
        """Include srcML stderr when conversion fails."""

        which.return_value = "/usr/bin/srcml"
        run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout=b"",
            stderr=b"parse failure",
        )

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(SrcMLExecutionError, "parse failure"):
                SrcMLRunner().convert(Path(directory) / "invalid.c")


if __name__ == "__main__":
    unittest.main()
