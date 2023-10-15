import json
from pathlib import Path

from typing import Dict

import pytest

from stashofexile import gamedata
from stashofexile.items import item as m_item

ItemDict = Dict[str, m_item.Item]

DATA_PATH = Path(Path(__file__).parent, 'data')


@pytest.fixture(name='example_items', scope='session')
def fixture_example_items() -> ItemDict:
    items = {}
    categories = gamedata.COMBO_ITEMS['Category']
    missing_categories = []
    for i, category in enumerate(categories):
        try:
            with Path(DATA_PATH, f'{category}.json').open('r') as f:
                items[category] = m_item.Item(json.load(f), str(i))
        except FileNotFoundError:
            missing_categories.append(category)

    if missing_categories:
        raise RuntimeError(
            f"Categories {missing_categories} are missing test data files"
        ) from None

    return items
