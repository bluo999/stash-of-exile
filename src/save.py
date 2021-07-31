from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Account:
    username: str = ''
    poesessid: str = ''
    tabs: List[Dict[str, Any]] = field(default_factory=list)
    characters: List[Dict[str, Any]] = field(default_factory=list)
    characterNames: List[str] = field(default_factory=list)
    tabsLength: int = 0


@dataclass
class SavedData:
    leagues: List[str] = field(default_factory=list)
    accounts: List[Account] = field(default_factory=list)
