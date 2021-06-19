from typing import Any, Dict
from util import insertValues

from consts import COLORS, SPAN_TEMPLATE, VALNUM_TO_COLOR


class Requirement:
    def __init__(self, reqInfo: Dict[str, Any]):
        self.name = reqInfo['name']
        self.values = reqInfo['values']
        self.tooltip = None

    def description(self) -> str:
        if self.tooltip is not None:
            return self.tooltip

        obj = insertValues(self.name, self.values)
        name = SPAN_TEMPLATE.format(COLORS['grey'], obj['text'])

        if obj['inserted']:
            self.tooltip = name
        else:
            color = COLORS[VALNUM_TO_COLOR[self.values[0][1]]]
            value = SPAN_TEMPLATE.format(color, self.values[0][0])

            # "Level 20" vs "100 Str"
            if obj['text'] == 'Level':
                self.tooltip = f'{name} {value}'
            else:
                self.tooltip = f'{value} {name}'

        return self.tooltip
