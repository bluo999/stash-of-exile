from typing import Dict, List

import pytest

from pytestqt.qtbot import QtBot
from PyQt6.QtWidgets import QLineEdit
from stashofexile import gamedata

from stashofexile.items import filter as m_filter, item as m_item
from stashofexile.widgets import editcombo


ItemDict = Dict[str, m_item.Item]
FilterDict = Dict[str, m_filter.Filter]


@pytest.fixture(name="filters", scope='session')
def fixture_filters() -> FilterDict:
    filters: List[m_filter.Filter] = []
    for filt in m_filter.FILTERS:
        match filt:
            case m_filter.Filter():
                filters.append(filt)
            case m_filter.FilterGroup(_, filts, _):
                filters.extend(filts)

    return {filt.name: filt for filt in filters}


@pytest.fixture(name="lineedit", scope='function')
def fixture_lineedit(qtbot: QtBot) -> QLineEdit:
    widget = QLineEdit()
    qtbot.addWidget(widget)
    return widget


@pytest.fixture(name="combobox", scope='function')
def fixture_editcombo(qtbot: QtBot) -> editcombo.ECBox:
    widget = editcombo.ECBox()
    widget.addItems(('a', 'b', 'c', 'd'))
    qtbot.addWidget(widget)
    return widget


@pytest.fixture(name="influence", scope='function')
def fixture_influence(qtbot: QtBot) -> m_filter.InfluenceFilter:
    widget = m_filter.InfluenceFilter()
    qtbot.addWidget(widget)
    return widget


def false_func() -> bool:
    return False


def test_value_lineedit(lineedit: QLineEdit):
    lineedit.setText('test')
    assert m_filter.get_widget_value(lineedit) == 'test'


def test_value_combobox(combobox: editcombo.ECBox):
    combobox.setCurrentIndex(combobox.findText('d'))
    assert m_filter.get_widget_value(combobox) == 'd'


def test_value_influence(influence: m_filter.InfluenceFilter):
    influence.set_values('redeemer warlord')
    assert m_filter.get_widget_value(influence) == 'redeemer warlord'


def test_filter_lineedit(lineedit: QLineEdit):
    filt = m_filter.Filter('', QLineEdit, false_func, None, [lineedit])
    assert not filt.is_active()

    filt.set_values(['test'])
    assert filt.is_active()
    assert m_filter.get_widget_value(lineedit) == 'test'
    assert filt.to_json() == ['test']

    filt.clear_filter()
    assert m_filter.get_widget_value(lineedit) == ''


def test_filter_combobox(combobox: editcombo.ECBox):
    filt = m_filter.Filter('', editcombo.ECBox, false_func, None, [combobox])
    assert not filt.is_active()

    filt.set_values(['c'])
    assert filt.is_active()
    assert m_filter.get_widget_value(combobox) == 'c'
    assert filt.to_json() == ['c']

    filt.clear_filter()
    assert m_filter.get_widget_value(combobox) == ''


def test_filter_influence(influence: m_filter.InfluenceFilter):
    filt = m_filter.Filter('', m_filter.InfluenceFilter, false_func, None, [influence])
    assert not filt.is_active()

    filt.set_values(['on'])
    assert filt.is_active()
    assert m_filter.get_widget_value(influence) == 'on'
    assert filt.to_json() == ['on']

    filt.set_values(['shaper crusader'])
    assert m_filter.get_widget_value(influence) == 'shaper crusader'
    assert filt.to_json() == ['shaper crusader']

    filt.clear_filter()
    assert m_filter.get_widget_value(influence) == ''


def test_filter_group(
    lineedit: QLineEdit, combobox: editcombo.ECBox, influence: m_filter.InfluenceFilter
):
    filters = [
        m_filter.Filter('A', QLineEdit, false_func, None, [lineedit]),
        m_filter.Filter('B', editcombo.ECBox, false_func, None, [combobox]),
        m_filter.Filter('C', m_filter.InfluenceFilter, false_func, None, [influence]),
    ]
    group = m_filter.FilterGroup('Group', filters)
    test_values = {
        'A': ['test2'],
        'B': ['b'],
        'C': ['elder hunter'],
    }
    group.set_values(test_values)
    assert m_filter.get_widget_value(lineedit) == 'test2'
    assert m_filter.get_widget_value(combobox) == 'b'
    assert m_filter.get_widget_value(influence) == 'elder hunter'
    assert group.to_json() == test_values


def test_between_filter():
    bot = QLineEdit()
    top = QLineEdit()

    assert m_filter.between_filter(5.01, float, bot, top)
    # Empty overrules out of bounds
    assert m_filter.between_filter(5.01, float, bot, top, min_val=10)

    bot.setText('-10.5')
    # Check default val
    assert not m_filter.between_filter(0, float, bot, top, default_val=0)
    assert m_filter.between_filter(-10.5, float, bot, top)
    assert not m_filter.between_filter(-20, float, bot, top)
    assert m_filter.between_filter(50, float, bot, top, max_val=100)
    assert not m_filter.between_filter(150, float, bot, top, max_val=100)

    top.setText('100')
    assert m_filter.between_filter(20, float, bot, top)
    assert not m_filter.between_filter(200, float, bot, top)

    bot.setText('.')
    assert m_filter.between_filter(-20, float, bot, top)
    assert not m_filter.between_filter(200, float, bot, top)
    assert m_filter.between_filter(-20, float, bot, top, min_val=-30)
    assert not m_filter.between_filter(-40, float, bot, top, min_val=-30)


def test_filter_name(example_items: ItemDict, filters: FilterDict, lineedit: QLineEdit):
    filt = filters['Name']
    filt.widgets.append(lineedit)
    leaguestone = example_items['Leaguestone']

    lineedit.setText('Ambush Leaguestone')
    assert filt.filter_func(leaguestone, lineedit)
    lineedit.setText('amb')
    assert filt.filter_func(leaguestone, lineedit)
    lineedit.setText(' amb')
    assert not filt.filter_func(leaguestone, lineedit)


def test_filter_category(example_items: ItemDict, filters: FilterDict):
    combobox = editcombo.ECBox()
    combobox.addItems(gamedata.COMBO_ITEMS['Category'])

    filt = filters['Category']
    filt.widgets.append(combobox)

    bow = example_items['Bow']
    wand = example_items['Wand']

    combobox.setCurrentIndex(combobox.findText('Bow'))
    assert filt.filter_func(bow, combobox)
    assert not filt.filter_func(wand, combobox)
