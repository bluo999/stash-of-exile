"""
Utility classes and functions.
"""

from typing import List, TypedDict

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


def valnum_to_color(val_num: int, text: str = '') -> str:
    """Returns color string given value number."""
    if val_num not in consts.VALNUM_TO_COLOR:
        logger.error('Color not found: %s for text %s', val_num, text)

    return consts.VALNUM_TO_COLOR.get(val_num, 'white')


def insert_values(text: str, values: List[List[str | int]]) -> ModifiedStr:
    """Inserts the colorized values into description text provided by the API."""
    obj: ModifiedStr = {'text': text, 'inserted': False}

    while '{' in obj['text']:
        index = obj['text'].index('{')
        val_index = int(obj['text'][index + 1])
        val_num = values[val_index][1]
        assert isinstance(val_num, int)
        text = str(values[val_index][0])
        obj['text'] = (
            obj['text'][:index]
            + colorize(text, valnum_to_color(val_num, text))
            + obj['text'][index + 3 :]
        )
        obj['inserted'] = True

    return obj
