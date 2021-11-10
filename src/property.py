"""
Defines parsing of properties.
"""

from consts import COLORS, SPAN_TEMPLATE, VALNUM_TO_COLOR
from util import ValInfo, insert_values


# TODO: Add multiline values (The Feared)
class Property:
    """Class to represent an item property."""

    def __init__(self, prop_info: ValInfo) -> None:
        self.name = prop_info.get('name')
        self.values = prop_info.get('vals')
        self.tooltip = None

    def description(self) -> str:
        """Get colorized description used in the properties tooltip."""
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
        obj = insert_values(name, self.values)

        if obj['inserted'] or len(self.values) == 0 or self.values[0][0] == '':
            # Property without label
            self.tooltip = SPAN_TEMPLATE.format(COLORS['grey'], obj['text'])
        else:
            # Property with label
            valnum = self.values[0][1]
            assert isinstance(valnum, int)
            color = COLORS[VALNUM_TO_COLOR.get(valnum, 'white')]
            label = SPAN_TEMPLATE.format(COLORS['grey'], obj['text'] + ': ')
            value = SPAN_TEMPLATE.format(color, self.values[0][0])
            self.tooltip = label + value

        return self.tooltip
