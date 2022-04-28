"""
Defines parsing of requirements.
"""

from stashofexile import consts, log, util

logger = log.get_logger(__name__)


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
        name = util.colorize(obj['text'], 'grey')

        if obj['inserted']:
            self.tooltip = name
        else:
            valnum = self.values[0][1]
            val = str(self.values[0][0])
            assert isinstance(valnum, int)
            if valnum not in consts.VALNUM_TO_COLOR:
                logger.error('Color not found: %s for text %s', valnum, val)
            color = consts.VALNUM_TO_COLOR.get(valnum, 'white')
            value = util.colorize(val, color)

            # "Level 20" vs "100 Str"
            if obj['text'] in ('Level', 'Class:'):
                self.tooltip = f'{name} {value}'
            else:
                self.tooltip = f'{value} {name}'

        return self.tooltip
