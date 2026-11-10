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

