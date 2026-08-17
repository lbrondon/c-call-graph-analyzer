"""Test project directory validation and deterministic discovery."""

import tempfile
import unittest
from pathlib import Path

from exceptions import ProjectsDirectoryError
from project_discovery import ProjectDiscovery


class ProjectDiscoveryTests(unittest.TestCase):
    """Verify ProjectDiscovery input and filtering rules."""

    def test_discovers_projects_in_deterministic_order(self) -> None:
        """Return visible directories in case-insensitive name order."""

        with tempfile.TemporaryDirectory() as directory:
            projects_dir = Path(directory)
            (projects_dir / "zeta").mkdir()
            (projects_dir / "Alpha").mkdir()
            (projects_dir / ".hidden").mkdir()
            (projects_dir / "README.txt").write_text("not a project")

            projects = ProjectDiscovery().discover(projects_dir)

        self.assertEqual(["Alpha", "zeta"], [project.name for project in projects])

    def test_rejects_missing_projects_directory(self) -> None:
        """Report a projects directory that does not exist."""

        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"

            with self.assertRaisesRegex(ProjectsDirectoryError, "does not exist"):
                ProjectDiscovery().discover(missing)

    def test_rejects_projects_directory_without_projects(self) -> None:
        """Report an input directory without project subdirectories."""

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ProjectsDirectoryError, "no project"):
                ProjectDiscovery().discover(Path(directory))


if __name__ == "__main__":
    unittest.main()
