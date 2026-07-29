from pathlib import Path


def find_project_root(start=None):
    """Find the nearest parent directory containing data/raw."""
    current = Path.cwd() if start is None else Path(start).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "data" / "raw").is_dir():
            return candidate
    raise FileNotFoundError("Could not find a project root containing data/raw.")

    