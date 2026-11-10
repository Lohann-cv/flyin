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


@dataclass(frozen=True)
class Connection:
    """A bidirectional edge between two zones.

    Attributes:
        zone_a: Name of the first zone.
        zone_b: Name of the second zone.
        max_link_capacity: Max dones on a link, 1 by default.
    """

    zone_a: str
    zone_b: str
    max_link_capacity: int = 1

    @property
    def key(self) -> frozenset[str]:
        """Getter for zones name of a connecton"""
        return frozenset((self.zone_a, self.zone_b))

    @property
    def name(self) -> str:
        """use to print the connection"""
        return f"{self.zone_a} - {self.zone_b}"

    def other(self, zone_name: str) -> str:
        """Return the other end of the connection.

        Arg:
            zone_name: One of the two point of the connection.

        Return:
            The name of the other point of the connection.

        Raises:
            ValueError: If 'zone_name' is not a point of the instence.
        """
        if zone_name == self.zone_a:
            return self.zone_b
        if zone_name == self.zone_b:
            return self.zone_a
        raise ValueError(f"'{zone_name}' is not an end of '{self.name}'")


class Network:
    """The graph of zones.

    The graph is bidirectional, the zone are store and accesible by their name in a dict, so are the connections.
    A adjaceny dict is used to be able to know wich zone are acceible by another zone.
    """

    def __init__(self, nb_drones: int) -> None:
        """Create an empty network.

        Args:
            nb_drones: The number of drones.

        Raises:
            ValueError: If the 'nb_drones' is not strictly positive.
        """
        if nb_drones <= 0:
            raise ValueError("There must be at least one drone")
        self._nb_drones: int = nb_drones
        self._zones: dict[str, Zone] = {}
        self._connections: dict[frozenset[str], Connection] = {}
        self._adjacency: dict[str, list[Connection]] = {}
        self._start: Zone | None = None
        self._end: Zone | None = None

    @property
    def nb_drones(self) -> int:
        """Getter for the '_nb_drones'."""
        return self._nb_drones

    @property
    def zones(self) -> list[Zone]:
        """Getter for Zone infos"""
        return list(self._zones.values())

    @property
    def connections(self) -> list[Connection]:
        """Getter for connections info"""
        return list(self._connections.values())

    @property
    def has_start(self) -> bool:
        """Check if there's a start zone"""
        return self._start is not None

    @property
    def has_end(self) -> bool:
        """Check if there's an end zone"""
        return self._end is not None

    @property
    def start(self) -> Zone:
        """Getter for the start zone

        Raises:
            LookupError: If no start zone has been added yet.
        """
        if self._start is None:
            raise LookupError("There's no start zone")
        return self._start

    @property
    def end(self) -> Zone:
        """Getter for the end zone

        Raises:
            LookupError: If no end zone has been added yet.
        """
        if self._end is None:
            raise LookupError("THere's no end zone")
        return self._end

    def add_zone(self, zone: Zone) -> None:
        """Add a given zone to the network.

        Arg:
            zone: The zone to add.

        Raises:
            ValueError: If the name is taken, or a second start/end is added.
        """
        if zone.name in self._zones:
            raise ValueError(f"zone '{zone.name}' already exists")
        if zone.role is ZoneRole.START:
            if self._start is not None:
                raise ValueError("A start zone already exists")
            self._start = zone
        elif zone.role is ZoneRole.END:
            if self._end is not None:
                raise ValueError("An end zone already exists")
            self._end = zone
        self._zones[zone.name] = zone
        self._adjacency[zone.name] = []

    def add_connection(self, connection: Connection) -> None:
        """Add a connection between two existing zones.

        Arg:
            connection: The connections to add.

        Raise:
            ValueError: If the second point is unknow, is the point or that the connection already exist.
        """
        for name in (connection.zone_a, connection.zone_b):
            if name not in self._zones:
                raise ValueError(f"Unknow zone '{name}'")
        if connection.zone_a == connection.zone_b:
            raise ValueError("A connection cannot loop on one zone")
        if connection.key in self._connections:
            raise ValueError(f"the connection '{connection.name}' already exists")
        self._connections[connection.key] = connection
        self._adjacency[connection.zone_a].append(connection)
        self._adjacency[connection.zone_b].append(connection)

    def has_zone(self, name: str) -> bool:
        """Check if a zone with the given name already exists."""
        return name in self._zones

    def get_zone(self, name: str) -> Zone:
        """Getter of a zone by it's name.

        Raises:
            KeyError: If there is no zone with such name.
        """
        return self._zones[name]

    def has_connection(self, name_a: str, name_b: str) -> bool:
        """Check if the two zones share a connection"""
        return frozenset((name_a, name_b)) in self._connections

    def get_connection(self, name_a: str, name_b: str) -> Connection:
        """Getter for the connection between two zones.

        Raise:
            KeyError: If the zones are not linked.
        """
        return self._connections[frozenset((name_a, name_b))]

    def connections_of(self, name:str) -> list[Connection]:
        """Return the connections of a zone.

        Raise:
            KeyError: If the zone doesn't exists.
        """
        return list(self._adjacency[name])

    def neighbors(self, name: str) -> list[Zone]:
        """Return zones linked to a given zone in a list.

        Raise:
            KeyError: If the zone doesn't exists.
        """
        return [self._zones[connected.other(name)] for connected in self._adjacency[name]]

    def zone_type_counts(self) -> dict[ZoneType, int]:
        """Count the zones of each type."""
        counts: dict[ZoneType, int] = {kind: 0 for kind in ZoneType}
        for zone in self._zones.values():
            counts[zone.zone_type] += 1
        return counts

