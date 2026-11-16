"""The Move and Plan model, a Plan hold a list of all
the move per turn, and is able tu format them for printing."""

from dataclasses import dataclass
from enum import Enum


class MoveKind(Enum):
    """The three kinds of move a drone can make in one turn."""

    STEP = "step"
    """Move to a zone that costs one turn."""

    DEPART = "depart"
    """First turn of a crossing towards a restricted
    zone (it takes 2 turns)."""

    ARRIVE = "arrive"
    """Second turn of the crossing: the drone reaches the zone."""


@dataclass(frozen=True)
class Move:
    """What one drone does during one turn.

    Attributes:
        drone: Identifier of the drone.
        kind: Step, depart, or arrival.
        origin: Zone the drone leaves.
        destination: Zone the drone moves into.
    """

    drone: int
    kind: MoveKind
    origin: str
    destination: str

    def label(self) -> str:
        """Return the text printed for this move.

        `D<id>-<zone>` for a step or an arrival, and
        `D<id>-<connection>` while the drone is in flight.
        """
        if self.kind is MoveKind.DEPART:
            return f"D{self.drone}-{self.origin}-{self.destination}"
        return f"D{self.drone}-{self.destination}"


@dataclass(frozen=True)
class Plan:
    """The moves of all the drones, turn after turn.

    Attribute:
        turns: For each turn, the moves made during that turn.
    """

    turns: tuple[tuple[Move, ...], ...]

    @property
    def nb_turns(self) -> int:
        """Number of simulation turn."""
        return len(self.turns)

    def lines(self) -> list[str]:
        """Return the output of the program: one line per turn."""
        return [
            " ".join(move.label() for move in turn) for turn in self.turns
        ]
