from typing import Any, Dict
from util import insertValues

from consts import COLORS, SPAN_TEMPLATE, VALNUM_TO_COLOR


class Property:
    def __init__(self, propInfo):
        self.name = propInfo.get('name')
        self.values = propInfo.get('values')
        self.tooltip = None

    def description(self) -> str:
        if self.tooltip is not None:
            return self.tooltip

        # Resonator text
        name = self.name
        if '<unmet>' in self.name:
            index = self.name.index('<')
            name = (
                self.name[0:index]
                + SPAN_TEMPLATE.format(COLORS['red'], self.name[index + 8])
                + self.name[index + 10 :]
            )

        # Insert property arguments
        obj = insertValues(name, self.values)

        if obj['inserted'] or len(self.values) == 0 or self.values[0][0] == '':
            # Property without label
            self.tooltip = SPAN_TEMPLATE.format(COLORS['grey'], obj['text'])
        else:
            # Property with label
            color = COLORS[VALNUM_TO_COLOR[self.values[0][1]]]
            label = SPAN_TEMPLATE.format(COLORS['grey'], obj['text'] + ': ')
            value = SPAN_TEMPLATE.format(color, self.values[0][0])
            self.tooltip = label + value

        return self.tooltip
