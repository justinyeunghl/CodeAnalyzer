"""Traverses a file or directory path and returns a list of file content records."""

import os

SIZE_LIMIT = 51_200  # 50 KB


def walk(path: str) -> list[dict]:
    """Collect readable text files under `path`.

    Args:
        path: A file path or directory path to traverse.

    Returns:
        A list of dicts with keys ``"path"`` (str) and ``"content"`` (str),
        one entry per accepted file.  Files larger than 50 KB are skipped with
        a printed warning; binary files are skipped silently.
    """
    if os.path.isfile(path):
        targets = [path]
    else:
        targets = [
            os.path.join(dirpath, filename)
            for dirpath, _dirnames, filenames in os.walk(path)
            for filename in filenames
        ]

    results = []
    for filepath in targets:
        if os.path.getsize(filepath) > SIZE_LIMIT:
            print(f"[SKIP] {filepath} — file exceeds 50 KB limit")
            continue
        try:
            with open(filepath, encoding="utf-8") as fh:
                results.append({"path": filepath, "content": fh.read()})
        except UnicodeDecodeError:
            pass

    return results
