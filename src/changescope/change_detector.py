import re
from pathlib import Path

from changescope.dependency_graph import (
    build_dependency_graph,
    find_affected_functions,
)
from changescope.function_parser import FunctionInfo, extract_functions
from changescope.git_diff import read_git_diff


def find_functions_at_lines(
    source_code: str,
    changed_lines: set[int],
) -> list[FunctionInfo]:
    return [
        function
        for function in extract_functions(source_code)
        if any(
            function.line_number <= line <= function.end_line_number
            for line in changed_lines
        )
    ]


def extract_changed_lines(diff_text: str) -> set[int]:
    changed_lines = set()
    current_line = None

    for line in diff_text.splitlines():
        if line.startswith("@@"):
            match = re.search(r"\+(\d+)(?:,(\d+))?", line)
            current_line = int(match.group(1)) if match else None
            continue

        if current_line is None:
            continue

        if line.startswith("+++"):
            continue
        if line.startswith("---"):
            continue
        if line.startswith("+"):
            changed_lines.add(current_line)
            current_line += 1
        elif line.startswith("-"):
            continue
        elif line.startswith(" "):
            current_line += 1

    return changed_lines


def extract_changed_lines_by_file(diff_text: str) -> dict[str, set[int]]:
    changed_by_file = {}
    current_file = None
    current_line = None

    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            changed_by_file.setdefault(current_file, set())
            current_line = None
            continue

        if line.startswith("+++ ") or line.startswith("--- "):
            continue

        if line.startswith("@@"):
            match = re.search(r"\+(\d+)(?:,(\d+))?", line)
            current_line = int(match.group(1)) if match else None
            continue

        if current_file is None or current_line is None:
            continue

        if line.startswith("+"):
            changed_by_file[current_file].add(current_line)
            current_line += 1
        elif line.startswith("-"):
            continue
        elif line.startswith(" "):
            current_line += 1

    return changed_by_file


def detect_changed_functions(
    repository_path: str | Path,
    base_ref: str,
    target_ref: str = "HEAD",
) -> list[FunctionInfo]:
    repository = Path(repository_path)
    diff_text = read_git_diff(repository, base_ref, target_ref)
    changed_by_file = extract_changed_lines_by_file(diff_text)
    affected_functions = []

    for file_path, changed_lines in changed_by_file.items():
        if not file_path.endswith(".py") or not changed_lines:
            continue

        full_path = repository / file_path
        if not full_path.is_file():
            continue

        source_code = full_path.read_text(encoding="utf-8")
        affected_functions.extend(
            find_functions_at_lines(source_code, changed_lines)
        )

    return affected_functions


def analyze_change_impact(
    repository_path: str | Path,
    base_ref: str,
    target_ref: str = "HEAD",
) -> set[str]:
    changed_functions = detect_changed_functions(
        repository_path,
        base_ref,
        target_ref,
    )
    changed_names = {function.name for function in changed_functions}
    repository = Path(repository_path)
    graph = {}

    for source_file in repository.rglob("*.py"):
        if ".venv" in source_file.parts or ".git" in source_file.parts:
            continue

        try:
            source_code = source_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        file_graph = build_dependency_graph(source_code)

        for function, callees in file_graph.items():
            graph.setdefault(function, set()).update(callees)

    return find_affected_functions(graph, changed_names)
