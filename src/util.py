from typing import Any, Dict, List

from consts import COLORS, SPAN_TEMPLATE, VALNUM_TO_COLOR


def insertValues(text: str, values: List[Any]) -> Dict[str, Any]:
    obj = {}
    obj['text'] = text
    obj['inserted'] = False

    while '{' in obj['text']:
        index = obj['text'].index('{')
        valIndex = int(obj['text'][index + 1])
        color = COLORS[VALNUM_TO_COLOR[values[valIndex][1]]]
        obj['text'] = (
            obj['text'][:index]
            + SPAN_TEMPLATE.format(color, values[valIndex][0])
            + obj['text'][index + 3 :]
        )
        obj['inserted'] = True

    return obj
