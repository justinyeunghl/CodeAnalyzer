"""Traverses a file or directory path and returns a list of file content records."""

import os

SIZE_LIMIT = 51_200  # 50 KB

# Directories that are always skipped during traversal.
IGNORED_DIRS = {
    ".git", ".vs", ".vscode", ".idea",
    "__pycache__", ".venv", "venv", "node_modules",
    ".bob", "dist", "build",
}


def walk(path: str) -> list[dict]:
    """Collect readable text files under `path`.

    Args:
        path: A file path or directory path to traverse.

    Returns:
        A list of dicts with keys ``"path"`` (str) and ``"content"`` (str),
        one entry per accepted file.  Files larger than 50 KB are skipped with
        a printed warning; binary files are skipped silently.
        Hidden directories and IDE/tooling folders listed in IGNORED_DIRS are
        never entered.
    """
    if os.path.isfile(path):
        targets = [path]
    else:
        targets = []
        for dirpath, dirnames, filenames in os.walk(path):
            # Prune ignored directories in-place so os.walk won't descend into them.
            dirnames[:] = [
                d for d in dirnames
                if d not in IGNORED_DIRS and not d.startswith(".")
            ]
            for filename in filenames:
                if not filename.startswith("."):
                    targets.append(os.path.join(dirpath, filename))

    results = []
    for filepath in targets:
        try:
            size = os.path.getsize(filepath)
        except OSError as exc:
            print(f"[SKIP] {filepath} — cannot read file: {exc}")
            continue
        if size > SIZE_LIMIT:
            print(f"[SKIP] {filepath} — file exceeds 50 KB limit")
            continue
        try:
            with open(filepath, encoding="utf-8") as fh:
                results.append({"path": filepath, "content": fh.read()})
        except UnicodeDecodeError:
            pass
        except OSError as exc:
            print(f"[SKIP] {filepath} — cannot read file: {exc}")

    return results
