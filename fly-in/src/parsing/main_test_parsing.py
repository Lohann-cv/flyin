import sys
from errors import ParseError
from map_parsing import MapParser

argvs = sys.argv[1:]
try:
    network = MapParser().parse_file(argvs[0])
except ParseError as exc:
    print(f"Error: {exc}", file=sys.stderr)
    exit(1)
print(network.describe())
exit(0)
