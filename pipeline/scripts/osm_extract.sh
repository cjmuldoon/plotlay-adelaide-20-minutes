#!/bin/bash
# The OpenStreetMap inputs for Greater Adelaide (ABS GCCSA 4GADE, its mesh blocks span -35.350 to -34.500,
# 138.443 to 139.044; the box adds about 6 km all round) from Geofabrik's Australia extract of 13 Nov 2026
# (osmosis_replication_timestamp 2026-11-13T21:22:20Z):
#   raw/osm/roads.opl     drivable ways (core/drivetime.js DRIVABLE), traffic signal nodes, turn restriction relations
#   raw/osm/places.geojsonseq  beaches, shopping centres, hospitals, universities (for the destinations)
#   bash scripts/osm_extract.sh <australia-latest.osm.pbf>
set -euo pipefail
cd "$(dirname "$0")/../raw/osm"
PBF="$1"; BOX=138.37,-35.41,139.11,-34.44
osmium extract -b "$BOX" "$PBF" -o adelaide-box.pbf --overwrite -s smart
osmium tags-filter adelaide-box.pbf w/highway=motorway,motorway_link,trunk,trunk_link,primary,primary_link,secondary,secondary_link,tertiary,tertiary_link,unclassified,residential,living_street,service,road n/highway=traffic_signals r/type=restriction -o roads.pbf --overwrite
osmium cat roads.pbf -f opl -o roads.opl --overwrite
osmium tags-filter adelaide-box.pbf nwr/natural=beach nwr/shop=mall nwr/amenity=hospital nwr/amenity=university nwr/leisure=stadium nwr/aeroway=terminal -o places.pbf --overwrite
osmium export places.pbf -f geojsonseq -a type,id -o places.geojsonseq --overwrite
ls -la roads.opl places.geojsonseq
