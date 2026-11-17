# the eight places' points as the pipeline used them (out/destinations.json, from scripts/destinations.mjs)
import json, os, sys
_B = sys.argv[1]
def points_of(d):
    m = json.load(open(os.path.join(_B, 'out/destinations.json')))
    return [tuple(p['ll']) for p in m[d]['points']]
