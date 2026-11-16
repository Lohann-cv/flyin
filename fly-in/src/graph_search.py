"""A graph search on a Network: BFS.
   It check if the network
"""

from collections import deque
from src.models import Network, Zone, ZoneRole, ZoneType


class GraphSearch:
    """Searches for ONE drone, without any capacity constraint.

    It is used to check if the graph is solvable
    """

    def __init__(self, network: Network) -> None:
        """Create the searcher.

        Args:
            network: The graph to search in.
        """
        self._network = network

    def reachable_from(self, source: str) -> set[str]:
        """Find every zone a drone can reach (BFS).

        The complexity is of O(V + E):
            E is an edge.
            V a vertex.

        Args:
            source: Name of the zone where the drone starts.

        Returns:
            The names of the reachable zones, the source included.
        """
        self._network.get_zone(source)
        seen = {source}
        queue: deque[str] = deque([source])
        while queue:
            name = queue.popleft()
            for zone in self._moves_from(name):
                if zone.name not in seen:
                    seen.add(zone.name)
                    queue.append(zone.name)
        return seen

    def is_solvable(self) -> bool:
        """Tell if a drone can go from the start to the end zone."""
        network = self._network
        return network.end.name in self.reachable_from(network.start.name)

    def _moves_from(self, name: str) -> list[Zone]:
        """List the zones a drone standing in `name` may move into.
        The blocked zon are ignored
        """
        if self._network.get_zone(name).role is ZoneRole.END:
            return []
        return [
            zone
            for zone in self._network.neighbors(name)
            if zone.zone_type is not ZoneType.BLOCKED
        ]
