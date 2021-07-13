from util import ValInfo, insertValues

from consts import COLORS, SPAN_TEMPLATE, VALNUM_TO_COLOR


class Requirement:
    """Class to represent an item requirement."""

    def __init__(self, reqInfo: ValInfo):
        self.name = reqInfo['name']
        self.values = reqInfo['vals']
        self.tooltip = None

    def description(self) -> str:
        """Get colorized description used in the requirements tooltip."""
        if self.tooltip is not None:
            return self.tooltip

        obj = insertValues(self.name, self.values)
        name = SPAN_TEMPLATE.format(COLORS['grey'], obj['text'])

        if obj['inserted']:
            self.tooltip = name
        else:
            valnum = self.values[0][1]
            assert isinstance(valnum, int)
            color = COLORS[VALNUM_TO_COLOR[valnum]]
            value = SPAN_TEMPLATE.format(color, self.values[0][0])

            # "Level 20" vs "100 Str"
            if obj['text'] == 'Level':
                self.tooltip = f'{name} {value}'
            else:
                self.tooltip = f'{value} {name}'

        return self.tooltip
