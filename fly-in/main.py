"""Entry point: reads a map and prints the moves of the drones."""

import os
import sys
import time

from src.errors import NoPathError, ParseError
from src.map_parsing import MapParser
from src.planner import Planner
from src.visual import Painter, TerminalView

USAGE = "Usage: python3 main.py <map_file> [--visual] [--delay=SECONDS]"

if __name__ == "__main__":
    argv = sys.argv[1:]
    files = [arg for arg in argv if not arg.startswith("--")]
    options = [arg for arg in argv if arg.startswith("--")]

    visual = False
    delay = 0.0
    valid_options = True

    for option in options:
        if option == "--visual":
            visual = True
        elif option.startswith("--delay="):
            try:
                delay = float(option.removeprefix("--delay="))
                if delay < 0:
                    valid_options = False
                    break
            except ValueError:
                valid_options = False
                break
        else:
            valid_options = False
            break

    if len(files) != 1 or not valid_options:
        print(USAGE, file=sys.stderr)
        sys.exit(2)

    try:
        network = MapParser().parse_file(files[0])
        plan = Planner(network).plan()
    except ParseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except NoPathError as exc:
        print(f"Error: the map cannot be solved: {exc}", file=sys.stderr)
        sys.exit(1)

    if not visual:
        for line in plan.lines():
            print(line)
        sys.exit(0)

    colors = sys.stdout.isatty() and "NO_COLOR" not in os.environ # Check if color can be outputed, to be fair I don't know if it will be tested
    frames = TerminalView(network, plan, Painter(colors)).frames()
    try:
        for number, frame in enumerate(frames):
            if number > 0:
                print()
                time.sleep(delay)
            print(frame, flush=True)
    except KeyboardInterrupt:
        print()
        sys.exit(130)
    sys.exit(0)
