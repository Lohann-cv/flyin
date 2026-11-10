"""The classes that represent the drone network: zones, connections and the graph."""

from dataclasses import dataclass
from enum import Enum

class ZoneType(Enum):
    """The types of zone and the price to enter them"""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

    @property
    def entry_cost(self) -> int:
        """The number of turn that is needed to enter in a zone.

        Return:
            1 for the priority and normal zone, 2 for the restricted ones.

        Raises:
            ValueError: If the zone if blocked.
        """
        if self is ZoneType.BLOCKED:
            raise ValueError("a blocked zone cannot be entered")
        if self is ZoneType.NORMAL or ZoneType.PRIORITY:
            return 1
        if self is ZoneType.RESTRICTED:
            return 2
