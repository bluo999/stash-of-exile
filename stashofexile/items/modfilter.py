"""
Defines mod filter functionality.
"""
import dataclasses
import enum

from typing import Callable, List, Optional

from PyQt6.QtWidgets import QGroupBox, QLineEdit, QVBoxLayout, QWidget

from stashofexile import log
from stashofexile.items import filter as m_filter, item as m_item
from stashofexile.widgets import editcombo


logger = log.get_logger(__name__)


class ModFilterGroupType(enum.Enum):
    """
    Enum for types of mod filter groups.
    """

    AND = 'And'
    NOT = 'Not'


@dataclasses.dataclass
class ModFilterGroup:
    """Represents a group of mod filters."""

    group_type: ModFilterGroupType = ModFilterGroupType.AND
    filters: List[m_filter.Filter] = dataclasses.field(default_factory=list)
    group_box: Optional[QGroupBox] = None
    vlayout: Optional[QVBoxLayout] = None


def filter_mod(
    item: m_item.Item, elem: editcombo.ECBox, range1: QLineEdit, range2: QLineEdit
) -> bool:
    """Filter function that searches for mods."""
    mod_str = elem.currentText()
    if mod_str == '':
        return True

    return mod_str in item.internal_mods and all(
        m_filter.between_filter(value, float, range1, range2)
        for value in item.internal_mods[mod_str]
    )


def _filter_func_group(group: ModFilterGroup) -> Callable[..., bool]:
    """Filter function that determines whether an item fits the group."""
    filters = [
        filt for filt in group.filters if m_filter.filter_is_active(filt.widgets[0])
    ]
    match group.group_type:
        case ModFilterGroupType.AND:
            return lambda item: all(
                filt.filter_func(item, *filt.widgets) for filt in filters
            )
        case ModFilterGroupType.NOT:
            return lambda item: all(
                not filt.filter_func(item, *filt.widgets) for filt in filters
            )
        case group_type:
            logger.error('Unexpected group type %s', group_type)
            return lambda _: False


def filter_group(group: ModFilterGroup) -> m_filter.Filter:
    """Returns mock filter with filter func that uses the whole group."""
    return m_filter.Filter(group.group_type.value, QWidget, _filter_func_group(group))
