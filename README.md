# C Call Graph Analyzer

C Call Graph Analyzer scans collections of C projects, converts each `.c` file
to XML with srcML, and produces a CSV containing caller-to-callee occurrences.

This repository is the analysis stage of a larger mining workflow. It expects
projects to exist locally and does not download repositories or access the
network.

## Features

- Discovers each immediate subdirectory of the input directory as a project.
- Finds regular `.c` files recursively and ignores other source extensions.
- Converts one file at a time with the `srcml` command-line program.
- Assigns each `<call>` element to its nearest lexical function, including GNU
  C nested functions.
- Rebuilds compound names such as `callbacks->run` from srcML elements.
- Writes one CSV row per source occurrence and preserves repeated calls.
- Continues after a conversion or XML parsing failure in an individual file.
- Reports discovery, project, file, percentage, failure, and output progress.
- Publishes the final CSV atomically to avoid incomplete output files.

## Requirements

- Python 3.10 or later
- srcML available on `PATH`, or provided through `--srcml-executable`
- A directory whose immediate subdirectories contain the C projects

The analyzer uses only the Python standard library.

## How It Works

The processing flow is:

```text
Command line
    -> project discovery
    -> recursive .c file scan
    -> srcML conversion
    -> caller/callee extraction
    -> atomic CSV writer
```

Each C file is converted independently. Its XML remains in memory and is not
written into the analyzed project. This avoids stale XML files and filename
collisions between source files in different directories.

## Module Responsibilities

| Module | Responsibility |
| --- | --- |
| `main.py` | Parse command-line options, assemble components, and report results. |
| `config.py` | Store validated settings for one execution. |
| `project.py` | Represent one discovered C project. |
| `project_discovery.py` | Validate the input directory and discover projects. |
| `c_file_scanner.py` | Find regular `.c` files in deterministic order. |
| `srcml_runner.py` | Invoke srcML and return XML bytes. |
| `srcml_call_parser.py` | Extract caller-to-callee occurrences from srcML XML. |
| `call_occurrence.py` | Represent one CSV occurrence. |
| `csv_call_writer.py` | Write and atomically publish the CSV file. |
| `analysis_service.py` | Coordinate the complete analysis workflow. |
| `analysis_result.py` | Report counts and file-level failures. |
| `ports.py` | Define replaceable converter and parser interfaces. |
| `exceptions.py` | Define expected application errors. |

## Input Layout

The required positional argument points to a directory containing one
subdirectory per project:

```text
projects/
├── curl/
│   ├── lib/
│   │   └── hash.c
│   └── src/
│       └── tool.c
└── openvpn/
    └── src/
        └── openvpn.c
```

Hidden directories and symbolic-link project directories are ignored.

## Usage

Run the analyzer from the repository root:

```bash
python3 source/main.py /path/to/projects
```

Choose a different output file:

```bash
python3 source/main.py /path/to/projects \
  --output output/calls.csv
```

Use a srcML executable that is not on `PATH`:

```bash
python3 source/main.py /path/to/projects \
  --srcml-executable /path/to/srcml
```

Relative input and output paths are resolved from the repository root, so the
command behaves consistently from different working directories.

### Progress Logging

Normal execution prints timestamped progress from startup to CSV publication.
It reports discovered projects and files, project start and completion,
overall percentage changes, file-level failures, elapsed time, and the final
summary.

```text
2026-08-16 20:15:00 [INFO] Projects discovered: 5
2026-08-16 20:15:03 [INFO] Overall progress: 289/28818 files processed (1%); project 'gcc': 42/27777
2026-08-16 20:20:00 [INFO] Published output CSV: /path/to/function_call_graph.csv
```

Use `--verbose` to also print the path of every C file before it is converted:

```bash
python3 source/main.py /path/to/projects --verbose
```

### Exit Codes

| Code | Meaning |
| --- | --- |
| `0` | Every discovered C file was analyzed successfully. |
| `1` | The CSV was generated, but one or more files failed. |
| `2` | Configuration, input discovery, srcML startup, or CSV output failed. |

## CSV Contract

The output contains exactly four columns:

```csv
Project,File,Caller,Callee
curl,lib/hash.c,Curl_hash_add,Curl_hash_pick
```

- `Project`: name of the immediate project directory.
- `File`: POSIX path relative to the project root.
- `Caller`: function that contains the call.
- `Callee`: called expression represented by srcML.

The output is a directed syntactic multigraph. If the same caller invokes the
same callee three times in one file, the CSV contains three rows.

## Error Handling

A srcML conversion or XML parsing error is logged immediately, recorded for
the affected file, and does not stop other files. The final log reports
discovered files, analyzed files, occurrences, failures, and elapsed time.
Fatal output errors discard the temporary CSV and leave an existing final CSV
unchanged.

## Interpretation Limits

This tool extracts syntax; it does not perform semantic symbol resolution.
Consequently:

- macros and preprocessor expressions may appear as callees;
- indirect calls are not linked to the concrete function used at runtime;
- identical callee text may refer to different symbols;
- conditional compilation branches reflect the srcML representation;
- a `<call>` without a direct `<name>` child uses `<unknown>` as its callee.

## Tests

The test suite does not require network access:

```bash
PYTHONPATH=source python3 -m unittest discover -s tests -v
```

Tests cover configuration, project discovery, C file scanning, srcML process
handling, XML parsing, duplicate preservation, partial failures, atomic CSV
publication, and command-line path handling.
