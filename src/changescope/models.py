
from dataclasses import dataclass
from enum import StrEnum


class ChangeType(StrEnum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


@dataclass(frozen=True, slots=True)
class FileChange:
    change_type: ChangeType
    old_path: str | None = None
    new_path: str | None = None

    def __post_init__(self) -> None:
        if self.change_type == ChangeType.ADDED:
            if not self.new_path or self.old_path is not None:
                raise ValueError("Invalid added file paths.")

        elif self.change_type == ChangeType.DELETED:
            if not self.old_path or self.new_path is not None:
                raise ValueError("Invalid deleted file paths.")

        elif self.change_type == ChangeType.MODIFIED:
            if not self.old_path or not self.new_path:
                raise ValueError("Both paths are required.")
            if self.old_path != self.new_path:
                raise ValueError("Modified file paths must match.")

        elif self.change_type == ChangeType.RENAMED:
            if not self.old_path or not self.new_path:
                raise ValueError("Both paths are required.")
            if self.old_path == self.new_path:
                raise ValueError("Renamed paths must differ.")
