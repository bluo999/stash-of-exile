"""
Defines parsing of properties.
"""

import consts
import util


# TODO: Add multiline values (The Feared)
class Property:
    """Class to represent an item property."""

    def __init__(self, prop_info: util.ValInfo) -> None:
        self.name = prop_info['name']
        self.values = prop_info['vals']
        self.tooltip = None

    @property
    def description(self) -> str:
        """Gets colorized description used in the properties tooltip."""
        if self.tooltip is not None:
            return self.tooltip

        # Resonator text
        name = self.name
        if '<unmet>' in self.name:
            index = self.name.index('<')
            name = (
                self.name[0:index]
                + consts.SPAN_TEMPLATE.format(
                    consts.COLORS['red'], self.name[index + 8]
                )
                + self.name[index + 10 :]
            )

        # Insert property arguments
        obj = util.insert_values(name, self.values)

        if obj['inserted'] or len(self.values) == 0 or self.values[0][0] == '':
            # Property without label
            self.tooltip = consts.SPAN_TEMPLATE.format(
                consts.COLORS['grey'], obj['text']
            )
        else:
            # Property with label
            valnum = self.values[0][1]
            assert isinstance(valnum, int)
            color = consts.COLORS[consts.VALNUM_TO_COLOR.get(valnum, 'white')]
            label = consts.SPAN_TEMPLATE.format(
                consts.COLORS['grey'], obj['text'] + ': '
            )
            value = consts.SPAN_TEMPLATE.format(color, self.values[0][0])
            self.tooltip = label + value

        return self.tooltip
