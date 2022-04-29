"""
Defines item sockets and groups.
"""

import enum

from typing import Any, Dict, List, Optional


class Socket(enum.Enum):
    """Represents an item's socket."""

    R = 0  # Red
    G = 1  # Green
    B = 2  # Blue
    W = 3  # White
    A = 4  # Abyssal
    DV = 9  # Resonator


SocketGroup = List[Socket]


def format_socket_group(socket_group: SocketGroup) -> str:
    """Returns string representation of a socket group."""
    strs = [str(socket) for socket in socket_group]
    return '-'.join(strs)


def create_sockets(sockets_list: Optional[List[Dict[str, Any]]]) -> List[SocketGroup]:
    """Creates socket groups from API json."""
    if sockets_list is None:
        return []

    sockets: List[SocketGroup] = [[]]
    cur_group = 0
    for socket in sockets_list:
        group = socket['group']
        if cur_group != group:
            sockets.append([])
            group += 1
        sockets[-1].append(Socket[socket['sColour']])

    return sockets
