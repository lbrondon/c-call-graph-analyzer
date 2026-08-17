"""Test analyzer configuration validation."""

import unittest
from pathlib import Path

from config import AnalyzerConfig


class AnalyzerConfigTests(unittest.TestCase):
    """Verify accepted and rejected analyzer settings."""

    def test_accepts_valid_configuration(self) -> None:
        """Keep a non-empty srcML executable value."""

        config = AnalyzerConfig(Path("projects"), Path("output.csv"), "srcml")

        self.assertEqual("srcml", config.srcml_executable)

    def test_rejects_empty_srcml_executable(self) -> None:
        """Reject executable values that contain only whitespace."""

        with self.assertRaisesRegex(ValueError, "cannot be empty"):
            AnalyzerConfig(Path("projects"), Path("output.csv"), "  ")


if __name__ == "__main__":
    unittest.main()
