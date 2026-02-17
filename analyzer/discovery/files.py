import os
from pathlib import Path

# Move these to a set for O(1) lookup speed
SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".rs", ".go", ".java", ".cpp", ".c", ".h"}
EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "dist", "build", ".coderecon", "venv", "lib"}


def _get_file_metadata(full_path, filename):
    """Fast metadata assembly using pre-calculated values."""
    return {
        "path": full_path,
        "name": filename,
        "size": os.path.getsize(full_path)  # Only hit the disk if necessary
    }


def discover_files(root_path: str):
    """
    High-speed discovery using os.scandir to minimize system calls.
    """
    # 1. Handle Single File Input Fast
    if os.path.isfile(root_path):
        if os.path.splitext(root_path)[1].lower() in SUPPORTED_EXTENSIONS:
            return [_get_file_metadata(root_path, os.path.basename(root_path))]
        return []

    files = []
    stack = [root_path]

    # 2. Manual Stack Walk (often faster than os.walk for deep trees)
    while stack:
        current_dir = stack.pop()
        try:
            with os.scandir(current_dir) as it:
                for entry in it:
                    if entry.is_dir():
                        if entry.name not in EXCLUDE_DIRS:
                            stack.append(entry.path)
                    elif entry.is_file():
                        if os.path.splitext(entry.name)[1].lower() in SUPPORTED_EXTENSIONS:
                            files.append(_get_file_metadata(entry.path, entry.name))
        except PermissionError:
            continue

    return files