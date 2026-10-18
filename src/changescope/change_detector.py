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
    functions = extract_functions(source_code)

    affected_functions = [
        function
        for function in functions
        if any(
            function.line_number <= line <= function.end_line_number
            for line in changed_lines
        )
    ]

    return affected_functions



def extract_changed_lines(diff_text: str) -> set[int]:
    
    import re

    changed_lines = set()
    current_line = None

    for line in diff_text.splitlines():
        if line.startswith("@@"):
            match = re.search(r"\+(\d+)(?:,(\d+))?", line)

            if match:
                current_line = int(match.group(1))

            continue

        if current_line is None:
            continue

        if line.startswith("+") and not line.startswith("+++"):
            changed_lines.add(current_line)
            current_line += 1

        elif line.startswith("-") and not line.startswith("---"):
            continue

        elif line.startswith(" "):
            current_line += 1

    return changed_lines



def detect_changed_functions(
    repository_path: str | Path,
    base_ref: str,
    target_ref: str = "HEAD",
) -> list[FunctionInfo]:
    diff_text = read_git_diff(repository_path, base_ref, target_ref)
    changed_lines = extract_changed_lines(diff_text)

    if not changed_lines:
        return []

    changed_files = set()

    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            changed_files.add(line[6:])

    affected_functions = []

    for file_path in changed_files:
        if not file_path.endswith(".py"):
            continue

        full_path = Path(repository_path) / file_path

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
    source_files = Path(repository_path).rglob("*.py")
    graph: dict[str, set[str]] = {}

    for source_file in source_files:
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