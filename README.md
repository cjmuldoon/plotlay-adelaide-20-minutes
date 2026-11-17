# Is everything in Adelaide 20 minutes away?

For every resident of Greater Adelaide (1,386,882 people in 15,797 ABS mesh blocks), the drive
to eight places: the city (the GPO), the nearest beach, Adelaide Airport, the nearest public emergency department, the
nearest university campus, Adelaide Oval, the Hills (Hahndorf or Mount Lofty) and the nearest shopping centre. Driving
at the speed limit with no traffic, in TomTom's 2025 rush-hour slowdown, and by public transport for contrast.

The showcase: https://www.getplotlay.com/showcase/adelaide-20-minutes/ . Made with [Plotlay](https://www.getplotlay.com)'s
How far by car (with road rules) and How far by public transport.

## The answer

Within 20 minutes of all eight: **10.1%** of residents at the speed limit with no traffic,
**0.0%** in the morning rush hour, **0.0%** by public transport.

| Within 20 minutes of | Car, speed limit | Car, rush hour | Public transport |
|---|---|---|---|
| A shopping centre | 99.4% | 97.6% | 37.4% |
| An emergency department | 93.5% | 79.1% | 4.7% |
| A university campus | 92.3% | 64.9% | 5.0% |
| A beach | 61.9% | 40.9% | 7.1% |
| Adelaide Oval | 51.3% | 23.9% | 1.2% |
| The city | 48.3% | 21.5% | 2.1% |
| The airport | 39.6% | 15.1% | 0.3% |
| The Hills | 24.6% | 8.6% | 0.2% |
| All eight | 10.1% | 0.0% | 0.0% |

## Method

- **Roads**: OpenStreetMap (Geofabrik extract of 13 November 2026), 19,489 km, with one-way streets,
  4,167 turn bans (restrictions with a via node; 1,465 with a via way left out)
  and 2,511 traffic-signal nodes joined into 782 sets of lights.
- **Speeds**: the mapped speed limit, else 50 km/h in built-up areas and 100 km/h outside them.
- **Waits** (stated assumptions): 12 s per set of lights (Webster's uniform delay for a 100 s cycle at half green); 4 to
  10 s to give way at a junction by the turn; 4 s at a roundabout.
- **Rush hour**: TomTom Traffic Index 2025, Adelaide metro area: the morning peak 58.5% longer than free flow on
  ordinary roads and 24.6% on motorways; the evening peak 62.7% and 9.8%. A city-wide average applied to every road of
  its kind. Not a traffic forecast.
- **Trips**: from the middle of each mesh block to the nearest place of each kind, quickest route, edge-based Dijkstra.
- **Public transport**: Adelaide Metro GTFS (feed version 1718), arriving 08:00 to 09:00 on Tuesday
  17 November 2026, the median trip, walking at 5.1 km/h up to 1,200 m to the first stop, at most 3 changes.

## Files

- `data/mesh_block_minutes.csv`: minutes per mesh block. Columns `<run>_<place>`, runs `free` (speed limit, no traffic),
  `am`, `pm` (rush hours), `typical` (Plotlay's older typical speeds, no lights or turn bans), `pt` (public transport);
  `free_hospital9`, `am_hospital9`: emergency departments with the Women's and Children's, Gawler and Mount Barker. Empty: not reached.
- `data/sa2.csv`: by ABS SA2 area. `data/shares_by_place.csv`: the shares. `data/places.csv`: the places used. `data/numbers.json`: every number on the page.
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
