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


class ZoneRole(Enum):
    """The role of a zone in the network"""

    START = "start"
    END = "end"
    REGULAR = "regular"



@dataclass(frozen=True)
class Zone:
    """A zone in the graph

    Attributes:
        name: The id of the zone.
        x: Integer x coordinate.
        y: Integer y coordinate.
        zone_type: Kind of zone (cost of entering it).
        color: Optional color of the zone.
        max_drones: Occupancy limit, the capacity property is used to get it.
        role: Start, end or regular zone.
    """

    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    color: str | None = None
    max_drones: int = 1
    role: ZoneRole = ZoneRole.REGULAR

    @property
    def capacity(self) -> int | None:
        """The getter for the capacity of the zone

        Return:
            'None' for the start and end since it can hold as many drone as eeded
            'max_drones' for the regular zones
        """
        if self.role is not ZoneRole.REGULAR:
            return None
        return self.max_drones
