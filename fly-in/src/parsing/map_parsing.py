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

