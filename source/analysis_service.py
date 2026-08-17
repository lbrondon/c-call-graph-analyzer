"""Orchestrate project discovery, srcML parsing, and CSV generation."""

import logging
from pathlib import Path
from time import monotonic

from analysis_result import AnalysisResult, FileAnalysisFailure
from c_file_scanner import CFileScanner
from csv_call_writer import CsvCallOccurrenceWriter
from exceptions import ProjectScanError, SrcMLExecutionError, SrcMLParseError
from ports import CallOccurrenceParser, SourceToXmlConverter
from project import Project
from project_discovery import ProjectDiscovery

LOGGER = logging.getLogger(__name__)


class CallGraphAnalysisService:
    """Coordinate project scanning, srcML conversion and CSV generation."""

    def __init__(
        self,
        project_discovery: ProjectDiscovery,
        file_scanner: CFileScanner,
        xml_converter: SourceToXmlConverter,
        call_parser: CallOccurrenceParser,
    ) -> None:
        """Create the service with replaceable analysis components."""

        self._project_discovery = project_discovery
        self._file_scanner = file_scanner
        self._xml_converter = xml_converter
        self._call_parser = call_parser

    def analyze(self, projects_dir: Path, output_csv: Path) -> AnalysisResult:
        """Analyze every C file and return an execution summary."""

        projects = self._project_discovery.discover(projects_dir)
        LOGGER.info("Projects discovered: %d", len(projects))

        discovered_files = 0
        analyzed_files = 0
        occurrence_count = 0
        failures: list[FileAnalysisFailure] = []
        project_files: list[tuple[Project, tuple[Path, ...] | None]] = []

        for project_number, project in enumerate(projects, start=1):
            LOGGER.info(
                "Scanning project %d/%d: %s",
                project_number,
                len(projects),
                project.name,
            )
            try:
                c_files = self._file_scanner.scan(project)
            except ProjectScanError as exc:
                failures.append(
                    FileAnalysisFailure(
                        project=project.name,
                        file="<project>",
                        message=str(exc),
                    )
                )
                LOGGER.error("Cannot scan project '%s': %s", project.name, exc)
                project_files.append((project, None))
                continue

            project_files.append((project, c_files))
            discovered_files += len(c_files)
            LOGGER.info(
                "Project '%s': C files found: %d",
                project.name,
                len(c_files),
            )

        LOGGER.info(
            "C files found across all projects: %d (projects: %d)",
            discovered_files,
            len(projects),
        )

        with CsvCallOccurrenceWriter(output_csv) as writer:
            processed_files = 0
            last_reported_percentage = -1

            for project_number, (project, c_files) in enumerate(
                project_files,
                start=1,
            ):
                if c_files is None:
                    LOGGER.info(
                        "Skipping project %d/%d '%s' after its scan failure",
                        project_number,
                        len(projects),
                        project.name,
                    )
                    continue
                if not c_files:
                    LOGGER.info(
                        "Project %d/%d '%s': no C files to analyze",
                        project_number,
                        len(projects),
                        project.name,
                    )
                    continue

                project_started_at = monotonic()
                project_analyzed_files = 0
                project_occurrences = 0
                project_failures = 0
                LOGGER.info(
                    "Analyzing project %d/%d '%s' (C files: %d)",
                    project_number,
                    len(projects),
                    project.name,
                    len(c_files),
                )

                for file_number, c_file in enumerate(c_files, start=1):
                    relative_file = c_file.relative_to(project.root).as_posix()
                    LOGGER.debug(
                        "Project '%s' file %d/%d: analyzing %s",
                        project.name,
                        file_number,
                        len(c_files),
                        relative_file,
                    )
                    try:
                        xml_content = self._xml_converter.convert(c_file)
                        occurrences = self._call_parser.parse(
                            xml_content=xml_content,
                            project=project.name,
                            file=relative_file,
                        )
                    except (SrcMLExecutionError, SrcMLParseError) as exc:
                        failures.append(
                            FileAnalysisFailure(
                                project=project.name,
                                file=relative_file,
                                message=str(exc),
                            )
                        )
                        project_failures += 1
                        LOGGER.warning(
                            "Project '%s' file %d/%d failed: %s (%s)",
                            project.name,
                            file_number,
                            len(c_files),
                            relative_file,
                            exc,
                        )
                    else:
                        writer.write_all(occurrences)
                        analyzed_files += 1
                        occurrence_count += len(occurrences)
                        project_analyzed_files += 1
                        project_occurrences += len(occurrences)

                    processed_files += 1
                    percentage = (
                        processed_files * 100 // discovered_files
                        if discovered_files
                        else 100
                    )
                    if percentage != last_reported_percentage:
                        LOGGER.info(
                            "Overall progress: %d/%d files processed (%d%%); "
                            "project '%s': %d/%d",
                            processed_files,
                            discovered_files,
                            percentage,
                            project.name,
                            file_number,
                            len(c_files),
                        )
                        last_reported_percentage = percentage

                LOGGER.info(
                    "Completed project %d/%d '%s' in %.1f seconds: "
                    "%d/%d files analyzed, %d occurrences, %d failures",
                    project_number,
                    len(projects),
                    project.name,
                    monotonic() - project_started_at,
                    project_analyzed_files,
                    len(c_files),
                    project_occurrences,
                    project_failures,
                )

        return AnalysisResult(
            projects=len(projects),
            discovered_files=discovered_files,
            analyzed_files=analyzed_files,
            occurrences=occurrence_count,
            failures=tuple(failures),
        )
