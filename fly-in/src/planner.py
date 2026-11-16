"""The planner: the drones leave one after the other, each as fast as it can.

Basicaly they all set a path with the algorithm (it's a copy of dijkstra were you check if the zone/connection isn't full on the turn where the drone need it).
"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from src.errors import NoPathError
from src.graph_search import GraphSearch
from src.models import Connection, Network, Zone, ZoneType
from src.simulation import Move, MoveKind, Plan

MOVE_COST = 2
PRIORITY_MOVE_COST = 1

@dataclass(frozen=True)
class _Step:
    """One move of a drone. A wait is not a step.

    Attributes:
        origin: Zone the drone leaves.
        destination: Zone it enters.
        time: The turn 't' when it leaves.
        duration: Turns taken: 1 for a normal or priority zone, 2 for a
            restricted one.
        link: The connection used.
    """

    origin: str
    destination: str
    time: int
    duration: int
    link: Connection


@dataclass(frozen=True)
class _Arrival:
    """How a drone reached a zone.

    Attributes:
        cost: Cost of the route since here.
        previous: The pair it came from (None at the start).
        step: The move made to get here (None if it waited, or at start).
    """

    cost: int
    previous: tuple[str, int] | None
    step: _Step | None


_Reached = defaultdict[int, dict[str, _Arrival]]
"""For each instant, how the drone can be in each zone."""


@dataclass(frozen=True)
class _Route:
    """The route of a drone.

    Attributes:
        presences: The pairs  where the drone is in a zone, in order.
        steps: Its moves, in order.
    """

    presences: tuple[tuple[Zone, int], ...]
    steps: tuple[_Step, ...]


class Reservations:
    """The places already taken by the drones, it's what is planned before."""

    def __init__(self) -> None:
        """Initialize empty reservations."""
        self._presence: Counter[tuple[str, int]] = Counter()
        self._crossings: Counter[tuple[frozenset[str], int]] = Counter()

    def zone_has_room(self, zone: Zone, instant: int) -> bool:
        """Tell whether one more drone fits in a zone at an instant.

        Args:
            zone: The zone.
            instant: Number of turns done.

        Returns:
            True if the zone has no limit or is not full.
        """
        capacity = zone.capacity
        if capacity is None:
            return True
        return self._presence[(zone.name, instant)] < capacity

    def link_is_free(self, link: Connection, instant: int) -> bool:
        """Tell whether one more drone can start on a connection.

        Args:
            link: The connection.
            instant: The turn.

        Returns:
            True if fewer than `max_link_capacity` drones start on it
            at this turn, in either direction.
        """
        used = self._crossings[(link.key, instant)]
        return used < link.max_link_capacity

    def book(self, route: _Route) -> None:
        """Take the places a route uses.

        Args:
            route: The route to book.
        """
        for zone, instant in route.presences:
            if zone.capacity is not None:
                self._presence[(zone.name, instant)] += 1
        for step in route.steps:
            self._crossings[(step.link.key, step.time + 1)] += 1


class Planner:
    """Finds a plan: one drone by one."""

    def __init__(self, network: Network) -> None:
        """Create the planner.

        Arg:
            network: The network to solve.
        """
        self._network = network

    def plan(self) -> Plan:
        """Compute the plan.

        Return:
            The plan.

        Raise:
            NoPathError: If no path links the start to the end zone.
        """
        network = self._network
        if not GraphSearch(network).is_solvable():
            raise NoPathError(
                f"no path between '{network.start.name}' and "
                f"'{network.end.name}'"
            )
        reserved = Reservations()
        routes: list[tuple[_Step, ...]] = []
        for _ in range(network.nb_drones):
            route = self._fastest_route(reserved)
            reserved.book(route)
            routes.append(route.steps)
        return self._build_plan(routes)

    def _fastest_route(self, reserved: Reservations) -> _Route:
        """Find the route of one drone that arrives first.

        Arg:
            reserved: The places taken by the previous drones.

        Return:
            The route.
        """
        network = self._network
        end = network.end.name
        reached: _Reached = defaultdict(dict)
        reached[0][network.start.name] = _Arrival(0, None, None)
        instant = 0
        while True:
            if end in reached[instant]:
                return self._rebuild(reached, instant)
            for name, arrival in reached[instant].items():
                self._extend(reached, instant, name, arrival, reserved)
            instant += 1

    def _extend(
        self,
        reached: _Reached,
        instant: int,
        name: str,
        arrival: _Arrival,
        reserved: Reservations,
    ) -> None:
        """From (zone, instant), if you cannot move, wait if you can move then move."""
        network = self._network
        zone = network.get_zone(name)
        if reserved.zone_has_room(zone, instant + 1): # Double it and give it to the next persone
            self._offer(
                reached, instant + 1, zone, _Arrival(
                    arrival.cost, (name, instant), None
                )
            )
        for link in network.connections_of(name):
            target = network.get_zone(link.other(name))
            if target.zone_type is ZoneType.BLOCKED:
                continue
            duration = target.zone_type.entry_cost
            if not reserved.zone_has_room(target, instant + duration):
                continue
            if not reserved.link_is_free(link, instant + 1):
                continue
            cost = (
                PRIORITY_MOVE_COST
                if target.zone_type is ZoneType.PRIORITY
                else MOVE_COST
            )
            step = _Step(name, target.name, instant, duration, link)
            self._offer(
                reached, instant + duration, target,
                _Arrival(arrival.cost + cost, (name, instant), step),
            )

    @staticmethod
    def _offer(
        reached: _Reached,
        instant: int,
        zone: Zone,
        arrival: _Arrival,
    ) -> None:
        """Keep an arrival if it cheapest one known for that pair."""
        known = reached[instant].get(zone.name)
        if known is None or arrival.cost < known.cost:
            reached[instant][zone.name] = arrival

    def _rebuild(
        self, reached: _Reached, instant: int
    ) -> _Route:
        """Build the rout by reversing the step."""
        network = self._network
        name = network.end.name
        presences: list[tuple[Zone, int]] = []
        steps: list[_Step] = []
        while True:
            presences.append((network.get_zone(name), instant))
            arrival = reached[instant][name]
            if arrival.previous is None:
                break
            if arrival.step is not None:
                steps.append(arrival.step)
            name, instant = arrival.previous
        presences.reverse()
        steps.reverse()
        return _Route(tuple(presences), tuple(steps))

    def _build_plan(self, routes: list[tuple[_Step, ...]]) -> Plan:
        """Turn the routes into the moves of each turn.

        The drones are numbered in the order they were planned. Each one
        arrives no earlier than the one before, so D1 is delivered first.
        """
        by_turn: dict[int, list[Move]] = {}
        for drone, steps in enumerate(routes, start=1):
            for step in steps:
                turn = step.time + 1
                if step.duration == 1:
                    kind = MoveKind.STEP
                else:
                    kind = MoveKind.DEPART
                    by_turn.setdefault(turn + 1, []).append(
                        Move(drone, MoveKind.ARRIVE, step.origin,
                             step.destination)
                    )
                by_turn.setdefault(turn, []).append(
                    Move(drone, kind, step.origin, step.destination)
                )
        last = max(by_turn)
        return Plan(
            tuple(tuple(by_turn.get(turn, [])) for turn in range(1, last + 1))
        )
