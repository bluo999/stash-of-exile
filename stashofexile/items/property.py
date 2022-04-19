"""
Defines parsing of properties.
"""

from stashofexile import consts, util


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

        if obj['inserted'] or not self.values or self.values[0][0] == '':
            # Property without label
            self.tooltip = consts.SPAN_TEMPLATE.format(
                consts.COLORS['grey'], obj['text']
            )
        else:
            self.tooltip = consts.SPAN_TEMPLATE.format(
                consts.COLORS['grey'], obj['text'] + ': '
            )
            for val, valnum in self.values:
                # Property with label
                assert isinstance(valnum, int)
                color = consts.COLORS[consts.VALNUM_TO_COLOR.get(valnum, 'white')]
                self.tooltip += consts.SPAN_TEMPLATE.format(
                    color, str(val).replace('\n', '<br />')
                )

        return self.tooltip
