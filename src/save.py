"""
Stores dataclasses used to save and cache data.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Account:
    """Represents an account with tabs and characters."""

    username: str = ''
    poesessid: str = ''
    tabs: List[Dict[str, Any]] = field(default_factory=list)
    characters: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    character_names: List[str] = field(default_factory=list)
    tabs_length: int = 0


@dataclass
class SavedData:
    """Represents all saved data, including leagues and accounts."""

    leagues: List[str] = field(default_factory=list)
    accounts: List[Account] = field(default_factory=list)
