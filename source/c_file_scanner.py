"""Find C source files inside one project directory."""

from pathlib import Path

from exceptions import ProjectScanError
from project import Project


class CFileScanner:
    """Find regular .c files recursively inside a project."""

    def scan(self, project: Project) -> tuple[Path, ...]:
        """Return regular .c files in stable relative-path order."""

        try:
            files = sorted(
                (
                    path
                    for path in project.root.rglob("*.c")
                    if path.is_file() and not path.is_symlink()
                ),
                key=lambda path: path.relative_to(project.root).as_posix(),
            )
        except OSError as exc:
            raise ProjectScanError(
                f"cannot scan project '{project.name}': {exc}"
            ) from exc

        return tuple(files)
