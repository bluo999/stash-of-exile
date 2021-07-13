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


def insertValues(text: str, values: List[List[Union[str, int]]]) -> ModifiedStr:
    """Inserts the colorized values into
    description text provided by the API."""
    obj: ModifiedStr = {'text': text, 'inserted': False}

    while '{' in obj['text']:
        index = obj['text'].index('{')
        valIndex = int(obj['text'][index + 1])
        valNum = values[valIndex][1]
        assert isinstance(valNum, int)
        color = COLORS[VALNUM_TO_COLOR[valNum]]
        obj['text'] = (
            obj['text'][:index]
            + SPAN_TEMPLATE.format(color, values[valIndex][0])
            + obj['text'][index + 3 :]
        )
        obj['inserted'] = True

    return obj
