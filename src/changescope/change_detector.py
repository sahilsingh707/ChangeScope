import re
from pathlib import Path

from changescope.dependency_graph import (
    find_affected_functions,
)
from changescope.function_parser import FunctionInfo, extract_functions
from changescope.git_diff import read_git_diff, read_git_file


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



def extract_deleted_lines_by_file(diff_text: str) -> dict[str, set[int]]:
    deleted_by_file: dict[str, set[int]] = {}
    current_file = None
    current_line = None

    for line in diff_text.splitlines():
        if line.startswith("--- a/"):
            current_file = line[6:]
            deleted_by_file.setdefault(current_file, set())
            current_line = None
            continue

        if line.startswith("--- ") or line.startswith("+++ "):
            continue

        if line.startswith("@@"):
            match = re.search(r"-(\d+)(?:,(\d+))?", line)
            current_line = int(match.group(1)) if match else None
            continue

        if current_file is None or current_line is None:
            continue

        if line.startswith("-"):
            deleted_by_file[current_file].add(current_line)
            current_line += 1
        elif line.startswith("+"):
            continue
        elif line.startswith(" "):
            current_line += 1

    return deleted_by_file



def detect_changed_functions(
    repository_path: str | Path,
    base_ref: str,
    target_ref: str = "HEAD",
) -> list[FunctionInfo]:
    repository = Path(repository_path)
    diff_text = read_git_diff(repository, base_ref, target_ref)
    added_by_file = extract_changed_lines_by_file(diff_text)
    deleted_by_file = extract_deleted_lines_by_file(diff_text)
    detected: dict[tuple[str, str], FunctionInfo] = {}

    for file_path, changed_lines in added_by_file.items():
        if not file_path.endswith(".py") or not changed_lines:
            continue

        full_path = repository / file_path
        if not full_path.is_file():
            continue

        try:
            source_code = full_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        for function in find_functions_at_lines(source_code, changed_lines):
            detected[(file_path, function.name)] = function

    for file_path, changed_lines in deleted_by_file.items():
        if not file_path.endswith(".py") or not changed_lines:
            continue

        source_code = read_git_file(repository, base_ref, file_path)
        if source_code is None:
            continue

        for function in find_functions_at_lines(source_code, changed_lines):
            detected.setdefault((file_path, function.name), function)

    return sorted(
        detected.values(),
        key=lambda function: (function.line_number, function.name),
    )



def analyze_change_impact(
    repository_path: str | Path,
    base_ref: str,
    target_ref: str = "HEAD",
) -> set[str]:
    from changescope.dependency_graph import build_repository_dependency_graph

    repository = Path(repository_path)
    diff_text = read_git_diff(repository, base_ref, target_ref)
    added_by_file = extract_changed_lines_by_file(diff_text)
    deleted_by_file = extract_deleted_lines_by_file(diff_text)
    changed_ids = set()

    for file_path, changed_lines in added_by_file.items():
        if not file_path.endswith(".py") or not changed_lines:
            continue

        full_path = repository / file_path
        if not full_path.is_file():
            continue

        try:
            source_code = full_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        for function in find_functions_at_lines(source_code, changed_lines):
            changed_ids.add(f"{file_path}::{function.name}")

    for file_path, changed_lines in deleted_by_file.items():
        if not file_path.endswith(".py") or not changed_lines:
            continue

        source_code = read_git_file(repository, base_ref, file_path)
        if source_code is None:
            continue

        for function in find_functions_at_lines(source_code, changed_lines):
            changed_ids.add(f"{file_path}::{function.name}")

    sources = {}

    for source_file in repository.rglob("*.py"):
        if ".venv" in source_file.parts or ".git" in source_file.parts:
            continue

        try:
            sources[source_file.relative_to(repository).as_posix()] = (
                source_file.read_text(encoding="utf-8")
            )
        except (OSError, UnicodeDecodeError):
            continue

    graph = build_repository_dependency_graph(sources)
    affected_ids = find_affected_functions(graph, changed_ids)

    return {
        identifier.split("::", maxsplit=1)[1]
        for identifier in affected_ids
    }
