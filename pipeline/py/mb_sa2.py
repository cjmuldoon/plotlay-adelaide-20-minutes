# Mesh block -> SA2 code (ASGS 2021) for Greater Adelaide, from the ABS mesh block pages fetched for the
# transit-45-minutes showcase (fetch_mb.py there: geo.abs.gov.au ASGS2021 MB service, CC BY 4.0), and the SA2
# outlines and names of Greater Adelaide from the ABS ASGS 2021 SA2 file (sa-abs/au_asgs3_sa2.fgb).
#   nbvenv/bin/python -I py/mb_sa2.py <build dir>
import sys, os, json, glob
import geopandas as gpd
B = sys.argv[1]
SRC = os.path.join(B, '../transit-45-minutes-build/raw/abs/mb_4GADE')
m = {}
for f in sorted(glob.glob(os.path.join(SRC, 'page_*.json'))):
    for ft in json.load(open(f))['features']:
        p = ft['properties']; m[str(p['mb_code_2021'])] = {'sa2': str(p['sa2_code_2021']), 'cat': p.get('mb_category_2021')}
json.dump(m, open(os.path.join(B, 'raw/abs/mb_sa2.json'), 'w'))
sa2s = sorted({v['sa2'] for v in m.values()})
g = gpd.read_file(os.path.join(B, '../sa-abs/au_asgs3_sa2.fgb'))
print(g.columns.tolist()[:12])
g = g[g['gccsa_code'] == '4GADE'].copy()
g['code'] = g['code'].astype(str)
g = g.to_crs(4326)
g['geometry'] = g.geometry.simplify(0.0002, preserve_topology=True)
missing = [s for s in sa2s if s not in set(g['code'])]
print('SA2s in Greater Adelaide', len(g), 'with mesh blocks', len(sa2s), 'missing', missing[:5])
g[['code', 'name', 'sa3_code', 'area_km2', 'geometry']].to_file(os.path.join(B, 'raw/abs/sa2-adelaide.geojson'), driver='GeoJSON')
