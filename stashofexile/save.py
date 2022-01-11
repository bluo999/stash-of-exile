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
class Account:
    """Represents an account with tabs and characters."""

    username: str = ''
    poesessid: str = ''
    tabs: List[Dict[str, Any]] = dataclasses.field(default_factory=list)
    tab_ids: List[TabId] = dataclasses.field(default_factory=list)
    characters: Dict[str, List[Dict[str, Any]]] = dataclasses.field(default_factory=dict)
    character_names: List[str] = dataclasses.field(default_factory=list)

    def has_characters(self):
        """Returns whether the character list has been set."""
        return len(self.character_names) != 0

    def has_tabs(self):
        """Returns whether tab list has been set."""
        return len(self.tab_ids) != 0


@dataclasses.dataclass
class SavedData:
    """Represents all saved data, including leagues and accounts."""

    leagues: List[str] = dataclasses.field(default_factory=list)
    accounts: List[Account] = dataclasses.field(default_factory=list)
