"""
Defines parsing of requirements.
"""

from stashofexile import consts, util


class Requirement:
    """Class to represent an item requirement."""

    def __init__(self, req_info: util.ValInfo):
        self.name = req_info['name']
        self.values = req_info['vals']
        self.tooltip = None

    @property
    def description(self) -> str:
        """Gets colorized description used in the requirements tooltip."""
        if self.tooltip is not None:
            return self.tooltip

        obj = util.insert_values(self.name, self.values)
        name = consts.SPAN_TEMPLATE.format(consts.COLORS['grey'], obj['text'])

        if obj['inserted']:
            self.tooltip = name
        else:
            valnum = self.values[0][1]
            assert isinstance(valnum, int)
            color = consts.COLORS[consts.VALNUM_TO_COLOR.get(valnum, 'white')]
            value = consts.SPAN_TEMPLATE.format(color, self.values[0][0])

            # "Level 20" vs "100 Str"
            if obj['text'] in ('Level', 'Class:'):
                self.tooltip = f'{name} {value}'
            else:
                self.tooltip = f'{value} {name}'

        return self.tooltip
