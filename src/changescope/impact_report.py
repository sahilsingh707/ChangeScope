
import ast
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


def extract_test_references(source_code: str) -> set[str]:
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return set()

    references = set()

    def get_attribute_chain(node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.Attribute):
            parent = get_attribute_chain(node.value)
            if parent is not None:
                return f"{parent}.{node.attr}"

        return None

    class ReferenceVisitor(ast.NodeVisitor):
        def visit_Name(self, node: ast.Name) -> None:
            references.add(node.id)

        def visit_Attribute(self, node: ast.Attribute) -> None:
            chain = get_attribute_chain(node)
            if chain is not None:
                references.add(chain)
            references.add(node.attr)
            self.generic_visit(node)

    ReferenceVisitor().visit(tree)

    return references


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
        identifier.split("::", maxsplit=1)[1].split(".")[-1]
        for identifier in changed_ids
    }
    affected_names = {
        identifier.split("::", maxsplit=1)[1].split(".")[-1]
        for identifier in affected_ids
    }

    impacted_qualified_names = {
        identifier.split("::", maxsplit=1)[1]
        for identifier in changed_ids | affected_ids
        if "." in identifier.split("::", maxsplit=1)[1]
    }

    test_files = {}

    for test_file in repository.rglob("test_*.py"):
        if ".venv" in test_file.parts or ".git" in test_file.parts:
            continue

        try:
            source = test_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        test_references = extract_test_references(source)

        covered = {
            name
            for name in changed_names | affected_names
            if name in test_references
        }

        for qualified_name in impacted_qualified_names:
            if qualified_name in test_references:
                covered.add(qualified_name.split(".")[-1])

        test_files[test_file.relative_to(repository).as_posix()] = covered

    return create_impact_report(
        changed_names,
        affected_names,
        test_files,
        changed_ids,
        affected_ids,
    )
