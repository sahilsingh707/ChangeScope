import subprocess

import pytest

from changescope.git_diff import read_git_diff


def create_repository(path):
    subprocess.run(["git", "init"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.name", "ChangeScope Tests"],
        cwd=path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "tests@example.com"],
        cwd=path,
        check=True,
    )


def commit_all(path, message):
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def test_reads_changes_between_commits(tmp_path):
    create_repository(tmp_path)

    source = tmp_path / "payment.py"
    source.write_text(
        "def calculate_total(price):\n    return price\n",
        encoding="utf-8",
    )
    commit_all(tmp_path, "Initial version")

    source.write_text(
        "def calculate_total(price):\n    return price * 1.18\n",
        encoding="utf-8",
    )
    commit_all(tmp_path, "Update total calculation")

    diff = read_git_diff(tmp_path, "HEAD~1", "HEAD")

    assert "-    return price" in diff
    assert "+    return price * 1.18" in diff


def test_invalid_git_reference_raises_error(tmp_path):
    create_repository(tmp_path)

    with pytest.raises(RuntimeError):
        read_git_diff(tmp_path, "nonexistent-reference")
