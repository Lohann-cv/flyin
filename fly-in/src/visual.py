"""A colored view of the simulation in the terminal. ^^

The view is rebuild turn after turn
"""


import re
from dataclasses import dataclass
from models import Network, Zone, ZoneType
from simulation import Move, MoveKind, Plan

COLOR_CODES: dict[str, int] = {
    "black": 244, "gray": 245, "grey": 245, "silver": 250, "white": 255,
    "red": 196, "crimson": 161, "darkred": 124, "maroon": 88,
    "orange": 208, "gold": 220, "yellow": 226, "brown": 130,
    "green": 34, "lime": 118, "darkgreen": 22, "teal": 30, "olive": 100,
    "cyan": 51, "blue": 33, "darkblue": 18, "navy": 17,
    "purple": 129, "violet": 177, "magenta": 201, "pink": 213,
}
"""A lot of color associated with their code"""

RAINBOW = (196, 208, 226, 46, 51, 33, 201)
"""The colors cycled through the letters of the goal of the chalenging map."""

RESET = "\033[0m"
BAR_WIDTH = 20
LINE_WIDTH = 100
"""Utils"""

ESCAPE_CODES = re.compile(r"\033\[[0-9;]*m")
"""The regex to take the color code we take every number including ';' and it's a style command"""

class Painter:
    """Adds terminal colors to a text."""

    def __init__(self, enabled: bool) -> None:
        """Create the painter (DaVinci).

        Args:
            enabled: False to never add any escape code (no color).
        """
        self._enabled = enabled

    def paint(self, text: str, color: str | None) -> str:
        """Paint a text with the color of a zone.

        Args:
            text: The text to paint.
            color: A color name from the map, or None.

        Returns:
            The painted text, or the text itself if the painter is
            disabled, the color is None, or the name is unknown.
        """
        if not self._enabled or color is None:
            return text
        name = color.lower()
        if name == "rainbow":
            return "".join(
                self._code(RAINBOW[i % len(RAINBOW)], letter)
                for i, letter in enumerate(text)
            )
        code = COLOR_CODES.get(name)
        return text if code is None else self._code(code, text)

    def bold(self, text: str) -> str:
        """Write a text in bold, if the painter is enabled."""
        if not self._enabled:
            return text
        return f"\033[1m{text}{RESET}"

    @staticmethod
    def _code(code: int, text: str) -> str:
        """Wrap a text in the escape code of a 256-color."""
        return f"\033[38;5;{code}m{text}{RESET}"


@dataclass(frozen=True)
class TurnState:
    """What the simulation looks like at the end of one turn.

    Attributes:
        number: Number of the turn (1 is the first one).
        moves: The moves made during this turn.
        delivered: Number of drones that reached the end zone so far.
    """

    number: int
    moves: tuple[Move, ...]
    delivered: int


class TerminalView:
    """Builds the text to show, one frame per step of the simulation."""

    def __init__(self, network: Network, plan: Plan, painter: Painter) -> None:
        """Create the view.

        Args:
            network: The network the plan was made for.
            plan: The plan to show.
            painter: Paints the zone names.
        """
        self._network = network
        self._plan = plan
        self._painter = painter

    def frames(self) -> list[str]:
        """Build everything to show.

        Return:
            The introduction, one frame per turn, then the summary.
        """
        frames = [self._intro()]
        frames.extend(self._frame(state) for state in self._replay())
        frames.append(self._summary())
        return frames

    def _replay(self) -> list[TurnState]:
        """Play the plan, and note the state after each turn."""
        end = self._network.end.name
        delivered = 0
        states: list[TurnState] = []
        for number, turn in enumerate(self._plan.turns, start=1):
            delivered += sum(
                1
                for move in turn
                if move.destination == end and move.kind is not MoveKind.DEPART
            )
            states.append(TurnState(number, turn, delivered))
        return states

    def _intro(self) -> str:
        """The title and the legend."""
        network = self._network
        title = (
            f"Fly-in: {network.nb_drones} drones, {len(network.zones)} "
            f"zones, {self._plan.nb_turns} turns"
        )
        legend = (
            "[R] restricted zone (2 turns)   [P] priority zone   "
            "D1 ⇢ a-b: drone in flight on a connection"
        )
        return f"{self._painter.bold(title)}\n{legend}"

    def _frame(self, state: TurnState) -> str:
        """The text of one turn."""
        total = self._network.nb_drones
        filled = state.delivered * BAR_WIDTH // total
        bar = "█" * filled + "░" * (BAR_WIDTH - filled)
        header = (
            f"Turn {state.number}/{self._plan.nb_turns}  {bar} "
            f"{state.delivered}/{total} delivered"
        )
        moves = [self._move_text(move) for move in state.moves]
        lines = [self._painter.bold(header)]
        lines += self._wrapped("moves", moves)
        return "\n".join(lines)

    @staticmethod
    def _wrapped(label: str, items: list[str]) -> list[str]:
        """Write a labelled list on one or more lines.

        Args:
            label: What the list is move zone....
            items: The items, possibly painted.

        Returns:
            The lines. The items are separated by three spaces, and a new line starts before the line would be wider than `LINE_WIDTH`.
        """
        if not items:
            return []
        prefix = f"  {label + ':':<11}"
        lines: list[str] = []
        current = ""
        width = 0
        for item in items:
            size = len(ESCAPE_CODES.sub("", item))
            if current and width + 3 + size > LINE_WIDTH - len(prefix):
                lines.append(current)
                current, width = item, size
            elif current:
                current, width = f"{current}   {item}", width + 3 + size
            else:
                current, width = item, size
        lines.append(current)
        return [
            (prefix if number == 0 else " " * len(prefix)) + text
            for number, text in enumerate(lines)
        ]

    def _summary(self) -> str:
        """The last line."""
        return self._painter.bold(
            f"All {self._network.nb_drones} drones delivered in "
            f"{self._plan.nb_turns} turns."
        )

    def _move_text(self, move: Move) -> str:
        """One move: ``D1 → zone``, or ``D2 ⇢ a-b`` while in flight."""
        zone = self._network.get_zone(move.destination)
        if move.kind is MoveKind.DEPART:
            link = f"{move.origin}-{move.destination}"
            return f"D{move.drone} ⇢ {self._painter.paint(link, zone.color)}"
        return f"D{move.drone} → {self._zone_label(zone)}"

    def _zone_label(self, zone: Zone) -> str:
        """The name of a zone, painted, with a tag for its type."""
        tags = {ZoneType.RESTRICTED: "[R]", ZoneType.PRIORITY: "[P]"}
        tag = tags.get(zone.zone_type, "")
        return self._painter.paint(zone.name, zone.color) + tag
