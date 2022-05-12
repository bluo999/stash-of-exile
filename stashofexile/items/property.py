"""
Defines parsing of properties.
"""

from stashofexile import consts, log, util

logger = log.get_logger(__name__)


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

        if self.name == '':
            self.tooltip = str(self.values[0][0])
            return self.tooltip

        # Resonator text
        name = self.name
        if '<unmet>' in self.name:
            index = self.name.index('<')
            name = (
                self.name[0:index]
                + util.colorize(self.name[index + 8], 'red')
                + self.name[index + 10 :]
            )

        # Insert property arguments
        obj = util.insert_values(name, self.values)

        if obj['inserted'] or not self.values or self.values[0][0] == '':
            # Property without label
            self.tooltip = util.colorize(obj['text'], 'grey')
            return self.tooltip

        tooltip = []
        tooltip.append(util.colorize(obj['text'] + ': ', 'grey'))
        first = True
        for val, valnum in self.values:
            # Property with label
            assert isinstance(valnum, int)
            if not first:
                tooltip.append(util.colorize(', ', 'grey'))
            if valnum not in consts.VALNUM_TO_COLOR:
                logger.error('Color not found: %s for text %s', valnum, val)
            color = consts.VALNUM_TO_COLOR.get(valnum, 'white')
            tooltip.append(util.colorize(str(val).replace('\n', '<br />'), color))
            first = False

        self.tooltip = ''.join(tooltip)
        return self.tooltip
