"""
Stores dataclasses used to save and cache data.
"""

import dataclasses
from typing import Any, Dict, List, NamedTuple


class TabId(NamedTuple):
    """Uniquely represents a tab (name and id)."""

    name: str
    id: str


@dataclasses.dataclass
class League:
    """Represents a league."""

    tab_ids: List[TabId] = dataclasses.field(default_factory=list)
    characters: Dict[str, Any] = dataclasses.field(default_factory=dict)
    character_names: List[str] = dataclasses.field(default_factory=list)
    uid: str = ''

    def has_tabs(self):
        """Returns whether tab list has been set."""
        return self.tab_ids

    def has_characters(self):
        """Returns whether the character list has been set."""
        return self.character_names


@dataclasses.dataclass
class Account:
    """Represents an account with tabs and characters."""

    username: str = ''
    poesessid: str = ''
    leagues: Dict[str, League] = dataclasses.field(default_factory=dict)

    def __repr__(self) -> str:
        return self.username


@dataclasses.dataclass
class SavedData:
    """Represents all saved data, including leagues and accounts."""

    leagues: List[str] = dataclasses.field(default_factory=list)
    accounts: List[Account] = dataclasses.field(default_factory=list)
