# The public repository (repo-src/) and the page's data download: the minutes for every mesh block to each of the eight
# places (car at the speed limit, morning and evening rush hour, typical speeds; public transport), the areas table,
# the places, the numbers, the pipeline's own code, a narrated notebook (executed afterwards), README and licences.
#   python3 -I py/package.py <build dir> <page dir>
import sys, os, json, csv, shutil, zipfile
B, PAGE = sys.argv[1:3]
R = os.path.join(B, 'repo-src'); shutil.rmtree(R, ignore_errors=True)
for d in ('data', 'python', 'pipeline/scripts', 'pipeline/py'): os.makedirs(os.path.join(R, d), exist_ok=True)
T = json.load(open(os.path.join(B, 'out/times.json'))); N = json.load(open(os.path.join(B, 'numbers.json')))
IDS = ['cbd', 'beach', 'airport', 'hospital', 'uni', 'oval', 'hills', 'shops']
RUNS = ['free', 'am', 'pm', 'typical', 'pt']
key = lambda run, d: f'pt_{d}' if run == 'pt' else f'car_{run}_{d}'
cols = [f'{run}_{d}' for run in RUNS for d in IDS]
with open(os.path.join(R, 'data/mesh_block_minutes.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['mb_code', 'sa2_code', 'residents', 'lat', 'lng', *cols, 'free_hospital9', 'am_hospital9'])
    for i, h in enumerate(T['homes']):
        vals = [T['runs'][key(run, d)][i] for run in RUNS for d in IDS] + [T['runs']['car_free_hospital9'][i], T['runs']['car_am_hospital9'][i]]
        w.writerow([h['code'], h['sa2'], round(h['people'], 2), h['ll'][0], h['ll'][1], *['' if v is None else v for v in vals]])
for f in ('sa2.csv', 'destinations.csv'): shutil.copy(os.path.join(B, 'tables', f), os.path.join(R, 'data', 'shares_by_place.csv' if f == 'destinations.csv' else f))
dest = json.load(open(os.path.join(B, 'out/destinations.json')))
with open(os.path.join(R, 'data/places.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['kind', 'name', 'lat', 'lng'])
    for d in IDS:
        for p in dest[d]['points']: w.writerow([d, p['name'], round(p['ll'][0], 6), round(p['ll'][1], 6)])
json.dump({k: v for k, v in N.items() if k not in ('counter', 'hist_cbd')}, open(os.path.join(R, 'data/numbers.json'), 'w'), indent=1)
import re
def scrub(src, dst):
    # the public copy names no local folders: the Plotlay repo and the outputs folder become variables
    t = open(src).read(); P = 'Projects' + '_Local'
    t = re.sub(r'\$HOME/' + P + r'/plotlay-worktrees/[a-z0-9-]+', '$PLOTLAY_REPO', t)
    t = re.sub(r'\$HOME/' + P + r'/plotlay-outputs', '$OUTPUTS', t).replace('~/' + P + '/plotlay-outputs', '$OUTPUTS')
    assert P not in t and '/Us' + 'ers/' not in t, src
    open(dst, 'w').write(t); shutil.copymode(src, dst)
for f in ('opl.mjs', 'destinations.mjs', 'run.mjs', 'grid.mjs', 'bases.mjs', 'osm_extract.sh', 'encode.sh'): scrub(os.path.join(B, 'scripts', f), os.path.join(R, 'pipeline/scripts', f))
for f in ('numbers.py', 'hero.py', 'mb_sa2.py', 'destinations_py.py', 'page.py', 'package.py', 'gen_notebook.py', 'mbmap.py'): scrub(os.path.join(B, 'py', f), os.path.join(R, 'pipeline/py', f))
for f in ('make_example.mjs', 'pipeline.sh'):
    if os.path.exists(os.path.join(B, f)): scrub(os.path.join(B, f), os.path.join(R, 'pipeline', f))
pc = lambda x: f'{x * 100:.1f}%'
A, D = N['all'], N['destinations']
rows = '\n'.join(f"| {D[d]['short']} | {pc(D[d]['runs']['free']['within_20'])} | {pc(D[d]['runs']['am']['within_20'])} | {pc(D[d]['runs']['pt']['within_20'])} |" for d in ['shops', 'hospital', 'uni', 'beach', 'oval', 'cbd', 'airport', 'hills'])
readme = f"""# Is everything in Adelaide 20 minutes away?

For every resident of Greater Adelaide ({N['residents']:,} people in {N['mesh_block_parts']:,} ABS mesh blocks), the drive
to eight places: the city (the GPO), the nearest beach, Adelaide Airport, the nearest public emergency department, the
nearest university campus, Adelaide Oval, the Hills (Hahndorf or Mount Lofty) and the nearest shopping centre. Driving
at the speed limit with no traffic, in TomTom's 2025 rush-hour slowdown, and by public transport for contrast.

The showcase: https://www.getplotlay.com/showcase/adelaide-20-minutes/ . Made with [Plotlay](https://www.getplotlay.com)'s
How far by car (with road rules) and How far by public transport.

## The answer

Read as a general saying, the test is whether at least half the places (4 of the 8) are within 20 minutes:
**{pc(A['free']['half_20'])}** of residents at the speed limit with no traffic (the typical resident has {A['free']['median_count']:.0f} of the 8),
**{pc(A['am']['half_20'])}** in the morning rush hour (typical {A['am']['median_count']:.0f}), **{pc(A['pt']['half_20'])}** by public transport.
Thresholds either side: 3 or more {pc(A['free']['at_least_3'])} / {pc(A['am']['at_least_3'])} / {pc(A['pt']['at_least_3'])}; 5 or more
{pc(A['free']['at_least_5'])} / {pc(A['am']['at_least_5'])} / {pc(A['pt']['at_least_5'])} (speed limit / rush hour / public transport).
Read literally, all eight: {pc(A['free']['within_20'])}, {pc(A['am']['within_20'])} and {pc(A['pt']['within_20'])}.

Residents by how many of the 8 are within 20 minutes (0 to 8), at the speed limit: {', '.join(f'{x * 100:.1f}%' for x in A['free']['count_dist'])}.

| Within 20 minutes of | Car, speed limit | Car, rush hour | Public transport |
|---|---|---|---|
{rows}
| Half or more (4 of 8) | {pc(A['free']['half_20'])} | {pc(A['am']['half_20'])} | {pc(A['pt']['half_20'])} |
| All eight | {pc(A['free']['within_20'])} | {pc(A['am']['within_20'])} | {pc(A['pt']['within_20'])} |

## Method

- **Roads**: OpenStreetMap (Geofabrik extract of 13 November 2026), {N['network']['km']:,} km, with one-way streets,
  {N['network']['turn_bans']:,} turn bans (restrictions with a via node; {N['network']['turn_bans_left_out']['via_way']:,} with a via way left out)
  and {N['network']['signal_nodes']:,} traffic-signal nodes joined into {N['network']['sets_of_lights']:,} sets of lights.
- **Speeds**: the mapped speed limit, else 50 km/h in built-up areas and 100 km/h outside them.
- **Waits** (stated assumptions): 12 s per set of lights (Webster's uniform delay for a 100 s cycle at half green); 4 to
  10 s to give way at a junction by the turn; 4 s at a roundabout.
- **Rush hour**: TomTom Traffic Index 2025, Adelaide metro area: the morning peak 58.5% longer than free flow on
  ordinary roads and 24.6% on motorways; the evening peak 62.7% and 9.8%. A city-wide average applied to every road of
  its kind. Not a traffic forecast.
- **Trips**: from the middle of each mesh block to the nearest place of each kind, quickest route, edge-based Dijkstra.
- **Public transport**: Adelaide Metro GTFS (feed version {N['pt']['feed_version']}), arriving 08:00 to 09:00 on Tuesday
  17 November 2026, the median trip, walking at 5.1 km/h up to {N['pt']['walk_max_m']:,} m to the first stop, at most {N['pt']['transfers']} changes.

## Files

- `data/mesh_block_minutes.csv`: minutes per mesh block. Columns `<run>_<place>`, runs `free` (speed limit, no traffic),
  `am`, `pm` (rush hours), `typical` (Plotlay's older typical speeds, no lights or turn bans), `pt` (public transport);
  `free_hospital9`, `am_hospital9`: emergency departments with the Women's and Children's, Gawler and Mount Barker. Empty: not reached.
- `data/sa2.csv`: by ABS SA2 area (`share_half_free`, `share_half_am`, `share_half_pt`: residents with 4 or more of the 8). `data/shares_by_place.csv`: the shares. `data/places.csv`: the places used. `data/numbers.json`: every number on the page.
- `python/adelaide_20_minutes.ipynb`: reads `../data` and gets the shares again.
- `pipeline/`: the code that made it (Node with Plotlay's engine, Python for the numbers and pictures).

Power BI: `mesh_block_minutes.csv` and `sa2.csv` open with Get data, Text/CSV; `lat` and `lng` place each mesh block on a map visual.

## Read it carefully

The nearest place of each kind, not the one people use; door to door without parking; speed limits as mapped; the
waits are assumptions; residents from the 2021 Census. See the showcase for the rest.

## Licences

Data made from OpenStreetMap: Open Database Licence (`LICENSE-DATA`); ABS data CC BY 4.0; Adelaide Metro timetable CC BY 4.0;
TomTom figures cited, not redistributed. Code: MIT (`LICENSE`). Independent work using open data, not endorsed by the
South Australian Government, Adelaide Metro or TomTom.
"""
assert '\u2014' not in readme
open(os.path.join(R, 'README.md'), 'w').write(readme)
open(os.path.join(R, 'LICENSE'), 'w').write("""MIT License

Copyright (c) 2026 Plotlay

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
""")
open(os.path.join(R, 'LICENSE-DATA'), 'w').write("""The tables in data/ are made from OpenStreetMap data, (c) OpenStreetMap contributors, and are made available under
the Open Database License (ODbL) 1.0: https://opendatacommons.org/licenses/odbl/1-0/ . If you publish a database
made from them, offer it under the same licence and credit OpenStreetMap.

Residents, mesh blocks and SA2 areas: Australian Bureau of Statistics, 2021 Census and ASGS Edition 3, CC BY 4.0.
Public transport times: made from Adelaide Metro's GTFS timetable, CC BY 4.0.
Rush-hour slowdown: TomTom Traffic Index 2025 (Adelaide), cited from tomtom.com/traffic-index; the figures are TomTom's.
""")
print('repo-src', sum(len(fs) for _, _, fs in os.walk(R)), 'files')
