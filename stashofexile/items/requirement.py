"""
Defines parsing of requirements.
"""

from stashofexile import log, util

logger = log.get_logger(__name__)


class Requirement:
    """Class to represent an item requirement."""

    def __init__(self, name: str, vals: util.ValInfo) -> None:
        self.name = name
        self.values = vals
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
            logger.error('Unexpected inserted: %s', self.tooltip)
        else:
            valnum = self.values[0][1]
            val = str(self.values[0][0])
            assert isinstance(valnum, int)
            color = util.valnum_to_color(valnum, val)
            value = util.colorize(val, color)

            # "Level 20" vs "100 Str"
            if obj['text'] in ('Level', 'Class:'):
                self.tooltip = f'{name} {value}'
            else:
                self.tooltip = f'{value} {name}'

        return self.tooltip
