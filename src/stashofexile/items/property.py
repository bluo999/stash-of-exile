"""
Defines parsing of properties.
"""

from stashofexile import log, util

logger = log.get_logger(__name__)


class Property:
    """Class to represent an item property."""

    def __init__(self, name: str, vals: util.ValInfo) -> None:
        self.name = name
        self.values = vals
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
            color = util.valnum_to_color(valnum, str(val))
            tooltip.append(util.colorize(str(val).replace('\n', '<br />'), color))
            first = False

        self.tooltip = ''.join(tooltip)
        return self.tooltip
