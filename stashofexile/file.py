"""
File functions.
"""

import os
import pathlib

from typing import Generator, Optional


def get_subdirectories(directory: str) -> Generator[str, None, None]:
    """Returns a list of subdirectories of the given directory."""
    return (f.path for f in os.scandir(directory) if f.is_dir())


def get_jsons(directory: str) -> Optional[Generator[str, None, None]]:
    """Returns a list of json files in the given directory."""
    if not os.path.isdir(directory):
        return None
    return (
        f.path
        for f in os.scandir(directory)
        if f.is_file() and os.path.splitext(f)[1] == '.json'
    )


def get_file_name(filepath: str) -> str:
    """Returns the file name (without extension) given its path."""
    return os.path.splitext(os.path.basename(filepath))[0]


def create_directories(filename: str) -> None:
    """Creates the directories for a given filename."""
    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
