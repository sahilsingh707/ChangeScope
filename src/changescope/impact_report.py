from dataclasses import dataclass, field
from pathlib import Path

from changescope.change_detector import (
    analyze_change_impact_ids,
    detect_changed_function_details,
)


@dataclass(frozen=True, slots=True)
class ImpactReport:
    changed_functions: list[str]
    affected_functions: list[str]
    recommended_tests: list[str]
    changed_function_ids: list[str] = field(default_factory=list)
    affected_function_ids: list[str] = field(default_factory=list)


def create_impact_report(
    changed_functions: set[str],
    affected_functions: set[str],
    test_files: dict[str, set[str]],
    changed_function_ids: set[str] | None = None,
    affected_function_ids: set[str] | None = None,
) -> ImpactReport:
    changed_ids = (
        changed_function_ids
        if changed_function_ids is not None
        else set(changed_functions)
    )
    affected_ids = (
        affected_function_ids
        if affected_function_ids is not None
        else set(affected_functions)
    )
    impacted_names = changed_functions | affected_functions

    recommended_tests = sorted(
        test_file
        for test_file, covered_functions in test_files.items()
        if impacted_names & covered_functions
    )

    return ImpactReport(
        changed_functions=sorted(changed_functions),
        affected_functions=sorted(affected_functions - changed_functions),
        recommended_tests=recommended_tests,
        changed_function_ids=sorted(changed_ids),
        affected_function_ids=sorted(affected_ids - changed_ids),
    )


def analyze_repository(
    repository_path: str | Path,
    base_ref: str,
    target_ref: str = "HEAD",
) -> ImpactReport:
    repository = Path(repository_path)
    changed_details = detect_changed_function_details(
        repository,
        base_ref,
        target_ref,
    )
    changed_ids = set(changed_details)
    affected_ids = analyze_change_impact_ids(
        repository,
        base_ref,
        target_ref,
    )

    changed_names = {
        identifier.split("::", maxsplit=1)[1]
        for identifier in changed_ids
    }
    affected_names = {
        identifier.split("::", maxsplit=1)[1]
        for identifier in affected_ids
    }

    test_files = {}

    for test_file in repository.rglob("test_*.py"):
        if ".venv" in test_file.parts or ".git" in test_file.parts:
            continue

        try:
            source = test_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        covered = {
            name
            for name in changed_names | affected_names
            if name in source
        }
        test_files[test_file.relative_to(repository).as_posix()] = covered

    return create_impact_report(
        changed_names,
        affected_names,
        test_files,
        changed_ids,
        affected_ids,
    )