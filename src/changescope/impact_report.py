from dataclasses import dataclass
from pathlib import Path

from changescope.change_detector import analyze_change_impact, detect_changed_functions


@dataclass(frozen=True, slots=True)
class ImpactReport:
    changed_functions: list[str]
    affected_functions: list[str]
    recommended_tests: list[str]


def create_impact_report(
    changed_functions: set[str],
    affected_functions: set[str],
    test_files: dict[str, set[str]],
) -> ImpactReport:
    impacted = changed_functions | affected_functions
    recommended_tests = sorted(
        test_file
        for test_file, covered_functions in test_files.items()
        if impacted & covered_functions
    )

    return ImpactReport(
        changed_functions=sorted(changed_functions),
        affected_functions=sorted(affected_functions - changed_functions),
        recommended_tests=recommended_tests,
    )


def analyze_repository(
    repository_path: str | Path,
    base_ref: str,
    target_ref: str = "HEAD",
) -> ImpactReport:
    repository = Path(repository_path)
    changed_functions = detect_changed_functions(
        repository, base_ref, target_ref
    )
    affected_functions = analyze_change_impact(
        repository, base_ref, target_ref
    )

    test_files = {}
    for test_file in repository.rglob("test_*.py"):
        if ".venv" in test_file.parts or ".git" in test_file.parts:
            continue

        try:
            source = test_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        covered = {
            function.name
            for function in changed_functions
            if function.name in source
        }
        covered.update(
            name for name in affected_functions if name in source
        )
        test_files[str(test_file.relative_to(repository))] = covered

    return create_impact_report(
        {function.name for function in changed_functions},
        affected_functions,
        test_files,
    )
