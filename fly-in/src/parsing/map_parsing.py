"""All the parsing code for the maps

The parsing follow a chain of steps:

"""

import re
from collections.abc import Iterable
from pathlib import Path
from errors import ParseError
from models import Connection, Network, Zone, ZoneRole, ZoneType

_ZONE_KEYS = frozenset({"zone", "color", "max_drones"})
_CONNECTION_KEYS = frozenset({"max_link_capacity"})
_ZONE_PREFIXES: dict[str, ZoneRole] = {
    "start_hub": ZoneRole.START,
    "end_hub": ZoneRole.END,
    "hub": ZoneRole.REGULAR
}
_FORBIDDEN_NAME_CHARS = frozenset("-[]:#")
_INTEGER = re.compile(r"-?[0-9]+")
_POSITIVE_DIGITS = re.compile(r"[0-9]+")
