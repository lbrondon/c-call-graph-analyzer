"""Provide the command-line entry point for call graph analysis."""

import argparse
import logging
from pathlib import Path
from time import monotonic
from typing import Sequence

from analysis_service import CallGraphAnalysisService
from c_file_scanner import CFileScanner
from config import AnalyzerConfig
from exceptions import CallGraphAnalyzerError
from project_discovery import ProjectDiscovery
from srcml_call_parser import SrcMLCallParser
from srcml_runner import SrcMLRunner

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def resolve_project_path(path: Path) -> Path:
    """Resolve relative CLI paths from this repository root."""
    expanded_path = path.expanduser()
    if expanded_path.is_absolute():
        return expanded_path.resolve()
    return (PROJECT_ROOT / expanded_path).resolve()


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(
        prog="call-graph-analyzer",
        description=(
            "Extract every caller-callee occurrence from C projects with srcML."
        ),
    )
    parser.add_argument(
        "projects_dir",
        metavar="PROJECTS_DIR",
        type=Path,
        help="path to the directory containing all downloaded repositories",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "output" / "function_call_graph.csv",
        help="destination CSV file",
    )
    parser.add_argument(
        "--srcml-executable",
        default="srcml",
        help="srcML executable name or path (default: srcml)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="log every C file in addition to regular progress updates",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the analyzer and return a process exit code."""

    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    started_at = monotonic()

    try:
        config = AnalyzerConfig(
            projects_dir=resolve_project_path(args.projects_dir),
            output_csv=resolve_project_path(args.output),
            srcml_executable=args.srcml_executable,
        )
        LOGGER.info("Starting C call graph analysis")
        LOGGER.info("Projects directory: %s", config.projects_dir)
        LOGGER.info("Output CSV: %s", config.output_csv)
        LOGGER.info("srcML executable: %s", config.srcml_executable)
        service = CallGraphAnalysisService(
            project_discovery=ProjectDiscovery(),
            file_scanner=CFileScanner(),
            xml_converter=SrcMLRunner(config.srcml_executable),
            call_parser=SrcMLCallParser(),
        )
        result = service.analyze(config.projects_dir, config.output_csv)
    except (CallGraphAnalyzerError, ValueError) as exc:
        LOGGER.error(
            "Analysis stopped after %.1f seconds: %s",
            monotonic() - started_at,
            exc,
        )
        return 2

    LOGGER.info(
        "Analysis finished in %.1f seconds: %d projects, "
        "%d/%d files analyzed, %d occurrences, %d failures",
        monotonic() - started_at,
        result.projects,
        result.analyzed_files,
        result.discovered_files,
        result.occurrences,
        len(result.failures),
    )
    LOGGER.info("CSV available at: %s", config.output_csv)
    return 0 if result.succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
