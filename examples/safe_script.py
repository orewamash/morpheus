"""
examples/safe_script.py — Benign file-reading script.
Used to verify normal, non-anomalous security scans in Morpheus.
"""

import os
from pathlib import Path


def create_temp_file(path: Path) -> None:
    path.write_text("Hello Morpheus! This is a safe file content.")


def read_temp_file(path: Path) -> str:
    return path.read_text()


def main():
    temp_path = Path("temp_safe_file.txt")
    create_temp_file(temp_path)
    content = read_temp_file(temp_path)
    print(f"Read content: {content}")

    # Clean up
    if temp_path.exists():
        os.remove(temp_path)


if __name__ == "__main__":
    main()
