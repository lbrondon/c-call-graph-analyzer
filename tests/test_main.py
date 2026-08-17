"""Test command-line parsing and repository-relative path handling."""

import io
import unittest
from contextlib import redirect_stderr
from pathlib import Path

import main


class MainTests(unittest.TestCase):
    """Verify command-line helper behavior."""

    def test_project_root_is_parent_of_source(self) -> None:
        """Derive the repository root from the main module location."""

        expected_root = Path(main.__file__).resolve().parent.parent

        self.assertEqual(expected_root, main.PROJECT_ROOT)

    def test_requires_projects_directory_argument(self) -> None:
        """Reject a command without the required projects directory."""

        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                main.build_parser().parse_args([])

        self.assertEqual(2, raised.exception.code)

    def test_parses_projects_directory_as_positional_argument(self) -> None:
        """Parse the projects directory into a Path value."""

        arguments = main.build_parser().parse_args(["/data/projects"])

        self.assertEqual(Path("/data/projects"), arguments.projects_dir)

    def test_resolves_relative_output_from_project_root(self) -> None:
        """Resolve relative paths independently of the working directory."""

        self.assertEqual(
            main.PROJECT_ROOT / "output" / "calls.csv",
            main.resolve_project_path(Path("output/calls.csv")),
        )


if __name__ == "__main__":
    unittest.main()
