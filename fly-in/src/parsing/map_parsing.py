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


class MetadataParser:
    """Parses a metadata block, '[key=value key=value]'."""

    def parse(
            self, raw: str, allowed: frozenset[str], line_no: int
    ) -> dict[str, str]:
        """Parse a metadaat block into a dictionary of strings.

        We only check the syntax here, therefore [zone=blue] would work.
        The ValueError isn't check here.

        Args:
            raw: Text inside the '[]'.
            allowed: The accepted keys.
            line_no: The line number, used for raising errors.

        Return:
            The value in a dictionary of strings.

        Raise:
            ParseError: For any syntax error.
        """
        raw = raw.strip()
        if not raw:
            return {}
        if not (raw.startswith("[") and raw.endswith("]")):
            raise ParseError(
                "Malformed metadata: expected '[key=value ...]'",
                line_no,
            )
        inner = raw[1:-1]
        if "[" in inner or "]" in inner:
            raise ParseError("Unexpected '[' or ']' in metadata", line_no)
        meta: dict[str, str] = {}
        for token in inner.split():
            key, sep, value = token.partition("=")
            if not sep or not key or not value or "=" in value:
                raise ParseError(
                    f"Invalide metadata '{token}' (expected key=value)",
                    line_no
                )
            if key not in allowed:
                raise ParseError(f"Unknow metadata key '{key}'", line_no)
            if key in meta:
                raise ParseError(f"Duplicate metadata key '{key}'", line_no)
            meta[key] = value
        return meta

class MapParser:
    """Turns a map file into a graph ('Network')."""

    def __init__(self) -> None:
        """Create the instence"""
        self._metadata = MetadataParser()

    def parse_file(self, path: str | Path) -> Network:
        """Read and parse a map file.

        Arg:
            path: Path of the map file.

        Return:
            ParseError: If the file is unreadable or invalid.
        """
        try:
            with open(path, encoding="utf-8-sig") as handle:
                return self.parse_lines(handle)
        except UnicodeDecodeError as exc:
            raise ParseError(f"'{path}' is not valid UTF-8 text") from exc
        except OSError as exc:
            raise ParseError(f"Cannot read '{path}': {exc.strerror}") from exc

    def parse_lines(self, lines: Iterable[str]) -> Network:
        """Parse the lines of a map.

        Arg:
            lines: The raw lines.

        Returns:
            A 'Network' instence wich is the parsed graph.

        Raise:
            ParseError: If the map is invalid.
        """
        network: Network | None = None
        for line_no, raw in enumerate(lines, start=1):
            content = self._strip_comment(raw)
            if not content:
                continue
            key, sep, rest = content.partition(":")
            key = key.strip()
            rest = rest.strip()
            if not sep:
                raise ParseError("Missing ':' after the line type", line_no)
            if network is None:
                if key != "nb_drones":
                    raise ParseError(
                        "The first line must be 'nb_drones: <number>'",
                        line_no
                    )
                nb_drones = self._parse_int(
                    rest, "nb_drones", line_no
                )
                network = Network(nb_drones)
                continue
            self._parse_line(network, key, rest, line_no)
        return self._finalize(network)

    def _parse_line(
        self, network: Network, key: str, rest: str, line_no: int
    ) -> None:
        """Clean a line to put it in the zone or connection register"""
        if key == "nb_drones":
            raise ParseError("'nb_drones' is defined more than once", line_no)
        if key in _ZONE_PREFIXES:
            zone = self._parse_zone(rest, _ZONE_PREFIXES[key], line_no)
            self._register_zone(network, zone, line_no)
        elif key == "connection":
            network.add_connection(
                self._parse_connection(network, rest, line_no)
            )
        else:
            raise ParseError(f"Unknow line type '{key}'", line_no)

    def _finalize(self, network: Network | None) -> Network:
        """A global check for when the file has been parsed."""
        if network is None:
            raise ParseError("The map is empty")
        if not network.has_start:
            raise ParseError("No 'start_hub'")
        if not network.has_end:
            raise ParseError("No 'end_hub'")
        return network

    def _strip_comment(self, raw: str) -> str:
        """Remove the '#' comment"""
        return raw.partition("#")[0].strip()

    def _split_metadata(self, rest: str) -> tuple[str, str]:
        """Split 'head [metadata]' into a tuple of ('head', '[metadata]')."""
        head, bracket, tail = rest.partition("[")
        return head, bracket + tail

    def _parse_int(self, text: str, label: str, line_no: int) -> int:
        """Parse an ASCII integer."""
        if not _INTEGER.fullmatch(text):
            raise ParseError(
                f"{label} must be an integer, got '{text}'", line_no
            )
        return int(text)

    def _parse_zone(self, rest: str, role: ZoneRole, line_no: int) -> Zone:
        """Parse the zone infos : '<name> <x> <y> [metadata]' into a Zone."""
        head, meta_raw = self._split_metadata(rest)
        tokens = head.split()
        if len(tokens) != 3:
            raise ParseError(
                f"expected '<name> <x> <y>', got {len(tokens)} value(s)",
                line_no
            )
        name, x_text, y_text = tokens
        self._check_zone_name(name, line_no)
        x = self._parse_int(x_text, "x coordinate", line_no)
        y = self._parse_int(y_text, "y coordinate", line_no)
        meta = self._metadata.parse(meta_raw, _ZONE_KEYS, line_no)
        type_text = meta.get("zone", ZoneType.NORMAL.value)
        try:
            zone_type = ZoneType(type_text)
        except ValueError:
            valid = ", ".join(kind.value for kind in ZoneType)
            raise ParseError(
                f"Invalid zone type '{type_text}' (expected: {valid})",
                line_no
            ) from None
        max_drones = 1
        if role is ZoneRole.REGULAR and "max_drones" in meta:
            max_drones = self._parse_int(
                meta["max_drones"], "max_drones", line_no
            )
        return Zone(
            name=name,
            x=x,
            y=y,
            zone_type=zone_type,
            color=meta.get("color"),
            max_drones=max_drones,
            role=role,
        )

    def _check_zone_name(self, name: str, line_no: int) -> None:
        """Check if the name follow the syntax rule"""
        for char in name:
            if char in _FORBIDDEN_NAME_CHARS:
                raise ParseError(
                    f"Invalide character '{char}' in zone name '{name}'",
                    line_no
                )

    def _register_zone(
        self, network: Network, zone: Zone, line_no: int
    ) -> None:
        """Add a zone to the network"""
        if network.has_zone(zone.name):
            raise ParseError(f"Zone '{zone.name}' is already defined", line_no)
        if zone.role is ZoneRole.START and network.has_start:
            raise ParseError("'start_hub' is defined more than once", line_no)
        if zone.role is ZoneRole.END and network.has_end:
            raise ParseError("'end_hub' is defined more than once", line_no)
        network.add_zone(zone)

    def _parse_connection(
        self, network: Network, rest: str, line_no: int
    ) -> Connection:
        """Parse '<zone1>-<zone2> [metadata]' into a Connection."""
        head, meta_raw = self._split_metadata(rest)
        tokens = head.split()
        if len(tokens) != 1:
            raise ParseError("Expected '<zone1>-<zone2>'", line_no)
        names = tokens[0].split("-")
        if len(names) != 2 or not all(names):
            raise ParseError(
                f"'{tokens[0]}' must be exactly '<zone1>-<zone2>'", line_no
            )
        first, second = names
        meta = self._metadata.parse(meta_raw, _CONNECTION_KEYS, line_no)
        if first == second:
            raise ParseError(f"Zone '{first}' linked to itself", line_no)
        for name in names:
            if not network.has_zone(name):
                raise ParseError(f"Unknown zone '{name}'", line_no)
        if network.has_connection(first, second):
            raise ParseError(
                f"Connection '{first}-{second}' is already defined",
                line_no
            )
        capacity = 1
        if "max_link_capacity" in meta:
            capacity = self._parse_int(
                meta["max_link_capacity"], "max_link_capacity", line_no
            )
        return Connection(first, second, capacity)
