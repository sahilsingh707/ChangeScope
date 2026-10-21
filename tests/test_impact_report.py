import subprocess

from changescope.impact_report import (
    analyze_repository,
    create_impact_report,
    extract_test_references,
)


def test_creates_impact_report():
    report = create_impact_report(
        changed_functions={"calculate_total"},
        affected_functions={"calculate_total", "create_invoice"},
        test_files={
            "tests/test_calculator.py": {"calculate_total"},
            "tests/test_invoice.py": {"create_invoice"},
            "tests/test_auth.py": {"login"},
        },
    )

    assert report.changed_functions == ["calculate_total"]
    assert report.affected_functions == ["create_invoice"]
    assert report.recommended_tests == [
        "tests/test_calculator.py",
        "tests/test_invoice.py",
    ]


def test_returns_empty_report_when_no_functions_are_affected():
    report = create_impact_report(set(), set(), {})

    assert report.changed_functions == []
    assert report.affected_functions == []
    assert report.recommended_tests == []


def test_analyzes_repository_and_returns_impact_report(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.name", "ChangeScope Tests"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "tests@example.com"],
        cwd=tmp_path,
        check=True,
    )

    source = tmp_path / "calculator.py"
    source.write_text(
        "def calculate_total(price):\n"
        "    return price\n\n"
        "def create_invoice(price):\n"
        "    return calculate_total(price)\n",
        encoding="utf-8",
    )

    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial version"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    source.write_text(
        "def calculate_total(price):\n"
        "    return price * 1.18\n\n"
        "def create_invoice(price):\n"
        "    return calculate_total(price)\n",
        encoding="utf-8",
    )

    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Update calculation"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    report = analyze_repository(tmp_path, "HEAD~1", "HEAD")

    assert "calculate_total" in report.changed_functions
    assert "create_invoice" in report.affected_functions




def test_impact_report_preserves_duplicate_function_identities():
    from changescope.impact_report import create_impact_report

    report = create_impact_report(
        changed_functions={"process_data"},
        affected_functions={"process_data", "create_invoice"},
        test_files={
            "tests/test_billing.py": {"process_data", "create_invoice"},
            "tests/test_analytics.py": {"process_data"},
        },
        changed_function_ids={
            "billing.py::process_data",
            "analytics.py::process_data",
        },
        affected_function_ids={
            "billing.py::process_data",
            "billing.py::create_invoice",
            "analytics.py::process_data",
        },
    )

    assert report.changed_function_ids == [
        "analytics.py::process_data",
        "billing.py::process_data",
    ]
    assert report.affected_function_ids == [
        "billing.py::create_invoice",
    ]
    assert report.changed_functions == ["process_data"]
    assert report.affected_functions == ["create_invoice"]




def test_does_not_recommend_test_for_unrelated_name_mention():
    report = create_impact_report(
        changed_functions={"calculate_total"},
        affected_functions=set(),
        test_files={
            "tests/test_billing.py": {"calculate_total"},
            "tests/test_documentation.py": set(),
        },
    )

    assert report.recommended_tests == ["tests/test_billing.py"]



def test_extract_test_references_finds_function_and_attribute_names():
    references = extract_test_references(
        "from billing import calculate_total\n"
        "invoice.calculate_total()\n"
    )

    assert "calculate_total" in references
    assert "invoice" in references


def test_extract_test_references_ignores_comments_and_strings():
    references = extract_test_references(
        "# calculate_total\n"
        "message = 'create_invoice'\n"
    )

    assert "calculate_total" not in references
    assert "create_invoice" not in references


def test_extract_test_references_handles_invalid_python():
    assert extract_test_references("def broken(:") == set()




def test_extract_test_references_distinguishes_class_method_calls():
    references = extract_test_references(
        "invoice.calculate_total()\n"
        "cart.calculate_total()\n"
    )

    assert "invoice.calculate_total" in references
    assert "cart.calculate_total" in references


def test_extract_test_references_keeps_same_method_names_distinct():
    references = extract_test_references(
        "invoice.calculate_total()\n"
        "cart.calculate_total()\n"
    )

    assert "invoice.calculate_total" in references
    assert "cart.calculate_total" in references
    assert "calculate_total" in references
