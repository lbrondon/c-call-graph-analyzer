"""Run the srcML command-line program for individual C files."""

import shutil
import subprocess
from pathlib import Path

from exceptions import SrcMLExecutionError, SrcMLNotAvailableError


class SrcMLRunner:
    """Convert C files to XML through the srcML command-line client."""

    def __init__(self, executable: str = "srcml") -> None:
        """Resolve the srcML executable or report that it is missing."""

        resolved_executable = shutil.which(executable)
        if resolved_executable is None:
            raise SrcMLNotAvailableError(f"srcML executable not found: {executable}")
        self._executable = resolved_executable

    def convert(self, c_file: Path) -> bytes:
        """Convert one C file and return srcML XML from standard output."""

        command = [self._executable, str(c_file)]
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
            )
        except OSError as exc:
            raise SrcMLExecutionError(
                f"could not start srcML for '{c_file}': {exc}"
            ) from exc

        if completed.returncode != 0:
            detail = completed.stderr.decode("utf-8", errors="replace").strip()
            raise SrcMLExecutionError(
                f"srcML failed for '{c_file}': {detail or 'unknown error'}"
            )
        if not completed.stdout.strip():
            raise SrcMLExecutionError(f"srcML returned empty XML for '{c_file}'")

        return completed.stdout
