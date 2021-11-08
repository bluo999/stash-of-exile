"""
Utility classes and functions.
"""

from typing import List, TypedDict, Union

from consts import COLORS, SPAN_TEMPLATE, VALNUM_TO_COLOR


class ModifiedStr(TypedDict):
    """Class to represent a string and whether it has been modified."""

    text: str
    inserted: bool


class ValInfo(TypedDict):
    """Class to represent a property or requirement from the API."""

    name: str
    vals: List[List[Union[str, int]]]


def insert_values(text: str, values: List[List[Union[str, int]]]) -> ModifiedStr:
    """Inserts the colorized values into description text provided by the API."""
    obj: ModifiedStr = {'text': text, 'inserted': False}

    while '{' in obj['text']:
        index = obj['text'].index('{')
        val_index = int(obj['text'][index + 1])
        val_num = values[val_index][1]
        assert isinstance(val_num, int)
        color = COLORS[VALNUM_TO_COLOR[val_num]]
        obj['text'] = (
            obj['text'][:index]
            + SPAN_TEMPLATE.format(color, values[val_index][0])
            + obj['text'][index + 3 :]
        )
        obj['inserted'] = True

    return obj
