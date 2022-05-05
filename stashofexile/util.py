"""
Utility classes and functions.
"""

import os
import pathlib

from typing import Generator, List, Optional, TypedDict

from stashofexile import consts, log

logger = log.get_logger(__name__)


class ModifiedStr(TypedDict):
    """Class to represent a string and whether it has been modified."""

    text: str
    inserted: bool


class ValInfo(TypedDict):
    """Class to represent a property or requirement from the API."""

    name: str
    vals: List[List[str | int]]


def colorize(text: str, color_name: str) -> str:
    """Colorizes text using span."""
    return consts.SPAN_TEMPLATE.format(consts.COLORS[color_name], text)


def insert_values(text: str, values: List[List[str | int]]) -> ModifiedStr:
    """Inserts the colorized values into description text provided by the API."""
    obj: ModifiedStr = {'text': text, 'inserted': False}

    while '{' in obj['text']:
        index = obj['text'].index('{')
        val_index = int(obj['text'][index + 1])
        val_num = values[val_index][1]
        assert isinstance(val_num, int)
        if val_num not in consts.VALNUM_TO_COLOR:
            logger.error('Color not found: %s for text %s', val_num, text)
        text = str(values[val_index][0])
        obj['text'] = (
            obj['text'][:index]
            + colorize(text, consts.VALNUM_TO_COLOR.get(val_num, 'white'))
            + obj['text'][index + 3 :]
        )
        obj['inserted'] = True

    return obj


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
