import json
import os

from typing import Dict

import pytest

from stashofexile import gamedata
from stashofexile.items import item as m_item

ItemDict = Dict[str, m_item.Item]

DATA_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data', 'item_data.json'
)


@pytest.fixture(name='example_items', scope='session')
def fixture_example_items() -> ItemDict:
    with open(DATA_PATH, 'rb') as f:
        items = json.load(f)
    items = [m_item.Item(item, str(i)) for i, item in enumerate(items['items'])]
    categories = gamedata.COMBO_ITEMS['Category']
    return {cat: items[categories.index(cat)] for cat in categories}
