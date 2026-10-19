import subprocess
from pathlib import Path


def read_git_diff(
    repository_path: str | Path,
    base_ref: str,
    target_ref: str = "HEAD",
) -> str:
    result = subprocess.run(
        [
            "git",
            "diff",
            "--no-ext-diff",
            "--no-color",
            f"{base_ref}...{target_ref}",
            "--",
        ],
        cwd=repository_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    if result.returncode != 0:
        message = result.stderr.strip() or "Git diff failed."
        raise RuntimeError(message)

    return result.stdout


def read_git_file(
    repository_path: str | Path,
    revision: str,
    file_path: str,
) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{revision}:{file_path}"],
        cwd=repository_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    if result.returncode != 0:
        return None

    return result.stdout