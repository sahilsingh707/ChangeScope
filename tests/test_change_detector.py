import subprocess

from changescope.change_detector import (
    analyze_change_impact,
    detect_changed_functions,
    extract_changed_lines,
    find_functions_at_lines,
)


def test_finds_function_containing_changed_line():
    source_code = """\
def calculate_total(price):
    tax = price * 0.18
    return price + tax

def greet_user(name):
    return f"Hello, {name}"
"""

    result = find_functions_at_lines(source_code, {2})

    assert len(result) == 1
    assert result[0].name == "calculate_total"


def test_returns_empty_list_when_no_lines_changed():
    source_code = """\
def calculate_total(price):
    return price * 1.18
"""

    result = find_functions_at_lines(source_code, set())

    assert result == []


def test_finds_second_function_when_its_line_changes():
    source_code = """\
def calculate_total(price):
    return price * 1.18

def greet_user(name):
    return f"Hello, {name}"
"""

    result = find_functions_at_lines(source_code, {5})

    assert len(result) == 1
    assert result[0].name == "greet_user"



def test_extracts_added_line_numbers_from_git_diff():
    diff_text = """\
@@ -1,2 +1,3 @@
 def calculate_total(price):
-    return price
+    tax = price * 0.18
+    return price + tax
"""

    result = extract_changed_lines(diff_text)

    assert result == {2, 3}



def test_extract_changed_lines_returns_empty_set_for_empty_diff():
    result = extract_changed_lines("")

    assert result == set()





def test_detects_changed_function_in_git_repository(tmp_path):
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

    source_file = tmp_path / "calculator.py"
    source_file.write_text(
        "def calculate_total(price):\n"
        "    return price\n",
        encoding="utf-8",
    )

    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial version"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    source_file.write_text(
        "def calculate_total(price):\n"
        "    return price * 1.18\n",
        encoding="utf-8",
    )

    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Update calculation"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    result = detect_changed_functions(tmp_path, "HEAD~1", "HEAD")

    assert [function.name for function in result] == ["calculate_total"]



def test_analyze_change_impact_includes_dependent_functions(tmp_path):
    import subprocess

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

    source_file = tmp_path / "calculator.py"
    source_file.write_text(
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

    source_file.write_text(
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

    result = analyze_change_impact(tmp_path, "HEAD~1", "HEAD")

    assert "calculate_total" in result
    assert "create_invoice" in result


def test_extract_changed_lines_by_file_keeps_line_numbers_separate():
    from changescope.change_detector import extract_changed_lines_by_file

    diff_text = """\
diff --git a/first.py b/first.py
--- a/first.py
+++ b/first.py
@@ -1,2 +1,2 @@
 def first():
-    return 1
+    return 2
diff --git a/second.py b/second.py
--- a/second.py
+++ b/second.py
@@ -1,2 +1,2 @@
 def second():
-    return 3
+    return 4
"""

    result = extract_changed_lines_by_file(diff_text)

    assert result == {"first.py": {2}, "second.py": {2}}


def test_extract_changed_lines_by_file_handles_empty_diff():
    from changescope.change_detector import extract_changed_lines_by_file

    assert extract_changed_lines_by_file("") == {}
