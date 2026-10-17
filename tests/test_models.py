
import pytest

from changescope.models import ChangeType, FileChange


def test_added_file():
    change = FileChange(
        change_type=ChangeType.ADDED,
        new_path="src/payment.py",
    )
    assert change.new_path == "src/payment.py"
    assert change.old_path is None


def test_modified_file():
    change = FileChange(
        change_type=ChangeType.MODIFIED,
        old_path="src/payment.py",
        new_path="src/payment.py",
    )
    assert change.change_type == ChangeType.MODIFIED


def test_deleted_file():
    change = FileChange(
        change_type=ChangeType.DELETED,
        old_path="src/payment.py",
    )
    assert change.old_path == "src/payment.py"
    assert change.new_path is None


def test_renamed_file():
    change = FileChange(
        change_type=ChangeType.RENAMED,
        old_path="src/payment.py",
        new_path="src/billing.py",
    )
    assert change.old_path != change.new_path


def test_added_file_rejects_old_path():
    with pytest.raises(ValueError):
        FileChange(
            change_type=ChangeType.ADDED,
            old_path="src/old.py",
            new_path="src/new.py",
        )
