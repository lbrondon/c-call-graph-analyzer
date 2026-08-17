"""Test recursive and deterministic C source discovery."""

import tempfile
import unittest
from pathlib import Path

from c_file_scanner import CFileScanner
from project import Project


class CFileScannerTests(unittest.TestCase):
    """Verify CFileScanner filtering and ordering rules."""

    def test_finds_only_c_files_recursively_and_in_order(self) -> None:
        """Return only regular .c files in relative-path order."""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project"
            nested = root / "src"
            nested.mkdir(parents=True)
            (root / "z.c").write_text("void z(void) {}")
            (nested / "a.c").write_text("void a(void) {}")
            (nested / "a.h").write_text("void a(void);")
            (nested / "a.cpp").write_text("void a() {}")

            files = CFileScanner().scan(Project("project", root))

        self.assertEqual(
            ["src/a.c", "z.c"],
            [path.relative_to(root).as_posix() for path in files],
        )


if __name__ == "__main__":
    unittest.main()
