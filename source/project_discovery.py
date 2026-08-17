"""Discover analyzable project directories from the input path."""

from pathlib import Path

from exceptions import ProjectsDirectoryError
from project import Project


class ProjectDiscovery:
    """Discover immediate project directories in deterministic order."""

    def discover(self, projects_dir: Path) -> tuple[Project, ...]:
        """Return visible project directories in stable name order."""

        if not projects_dir.exists():
            raise ProjectsDirectoryError(
                f"projects directory does not exist: {projects_dir}"
            )
        if not projects_dir.is_dir():
            raise ProjectsDirectoryError(
                f"projects path is not a directory: {projects_dir}"
            )

        try:
            directories = sorted(
                (
                    path
                    for path in projects_dir.iterdir()
                    if path.is_dir()
                    and not path.is_symlink()
                    and not path.name.startswith(".")
                ),
                key=lambda path: path.name.casefold(),
            )
        except OSError as exc:
            raise ProjectsDirectoryError(
                f"cannot list projects directory '{projects_dir}': {exc}"
            ) from exc

        if not directories:
            raise ProjectsDirectoryError(
                f"no project directories found in: {projects_dir}"
            )

        return tuple(Project(name=path.name, root=path) for path in directories)
