"""
Defines mod filter functionality.
"""
import dataclasses
import enum

from typing import Callable, List, Optional, Tuple

from PyQt6.QtWidgets import QGroupBox, QLineEdit, QVBoxLayout, QWidget

from stashofexile import log
from stashofexile.items import filter as m_filter, item as m_item
from stashofexile.widgets import editcombo


logger = log.get_logger(__name__)


class ModFilterGroupType(enum.Enum):
    """Enum for types of mod filter groups."""

    AND = 'And'
    NOT = 'Not'
    IF = 'If'
    COUNT = 'Count'
    WEIGHTED = 'Weighted Sum'


@dataclasses.dataclass
class ModFilterGroup:
    """
    Represents a group of mod filters.

    Fields:
        group_type (ModFilterGroupType): Type of mod filter group.
        filters (List[Filter]): List of filter objects.
        group_box (QGroupBox, Optional): Corresponding group box.
        vlayout (QVBoxLayout, Optional): Corresponding QVBoxLayout.
        lineedit (QLineEdit, Optional): Corresponding line edit (for count/weighted sum).
    """

    group_type: ModFilterGroupType = ModFilterGroupType.AND
    filters: List[m_filter.Filter] = dataclasses.field(default_factory=list)
    group_box: Optional[QGroupBox] = None
    vlayout: Optional[QVBoxLayout] = None
    min_lineedit: Optional[QLineEdit] = None
    max_lineedit: Optional[QLineEdit] = None


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
            return lambda item, *_: all(
                filt.filter_func(item, *filt.widgets) for filt in filters
            )

        case ModFilterGroupType.NOT:
            return lambda item, *_: all(
                not filt.filter_func(item, *filt.widgets) for filt in filters
            )

        case ModFilterGroupType.IF:
            mods: List[editcombo.ECBox] = []
            widgets: List[Tuple[QLineEdit, QLineEdit]] = []
            for filt in filters:
                assert isinstance(filt.widgets[0], editcombo.ECBox)
                assert isinstance(filt.widgets[1], QLineEdit)
                assert isinstance(filt.widgets[2], QLineEdit)
                mods.append(filt.widgets[0])
                widgets.append((filt.widgets[1], filt.widgets[2]))

            def _filt(item: m_item.Item, *_) -> bool:
                # If mod exists, then ensure mod is within range
                values = [
                    item.internal_mods.get(mod.currentText(), [0])[0] for mod in mods
                ]
                return all(
                    val == 0 or m_filter.between_filter(val, float, bot, top)
                    for val, (bot, top) in zip(values, widgets)
                )

            return _filt

        case ModFilterGroupType.COUNT:

            def _filt(item: m_item.Item, *_) -> bool:
                # Run each filter against the item and count occurences of True
                filts = [filt.filter_func(item, *filt.widgets) for filt in filters]
                return m_filter.between_filter(
                    filts.count(True),
                    float,
                    group.min_lineedit,
                    group.max_lineedit,
                    default_val=-1,
                )

            return _filt

        case ModFilterGroupType.WEIGHTED:
            mods: List[editcombo.ECBox] = []
            weights: List[float] = []
            for filt in filters:
                assert isinstance(filt.widgets[0], editcombo.ECBox)
                assert isinstance(filt.widgets[1], QLineEdit)
                mods.append(filt.widgets[0])
                weight_str = filt.widgets[1].text()
                weights.append(float(weight_str) if weight_str else 1)

            def _filt(item: m_item.Item, *_) -> bool:
                # Perform a weighted sum of the selected mods
                values = [
                    item.internal_mods.get(mod.currentText(), [0])[0] for mod in mods
                ]
                weighteds = (value * weight for value, weight in zip(values, weights))
                return m_filter.between_filter(
                    sum(weighteds),
                    float,
                    group.min_lineedit,
                    group.max_lineedit,
                    default_val=m_filter.MIN_VAL,
                )

            return _filt

        case group_type:
            logger.error('Unexpected group type %s', group_type)
            return lambda *_: False


def filter_group(group: ModFilterGroup) -> m_filter.Filter:
    """Returns mock filter with filter func that uses the whole group."""
    return m_filter.Filter(
        group.group_type.value,
        QWidget,
        _filter_func_group(group),
        None,
        [widget for filt in group.filters for widget in filt.widgets],
    )
