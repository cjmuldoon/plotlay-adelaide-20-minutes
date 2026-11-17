# Every number on the page, README, video and post, from out/times.json (scripts/run.mjs): numbers.json and tables/.
#   python3 -I py/numbers.py <build dir>
import sys, os, json, csv, math
B = sys.argv[1]
T = json.load(open(os.path.join(B, 'out/times.json')))
META = json.load(open(os.path.join(B, 'out/meta.json')))
H = T['homes']; R = T['runs']
W = [h['people'] for h in H]; TOT = sum(W)
IDS = ['cbd', 'beach', 'airport', 'hospital', 'uni', 'oval', 'hills', 'shops']
NAMES = {'cbd': 'The city (GPO)', 'beach': 'The nearest beach', 'airport': 'Adelaide Airport', 'hospital': 'The nearest public emergency department', 'uni': 'The nearest university campus', 'oval': 'Adelaide Oval', 'hills': 'The Hills (Hahndorf or Mount Lofty)', 'shops': 'The nearest shopping centre'}
SHORT = {'cbd': 'The city', 'beach': 'A beach', 'airport': 'The airport', 'hospital': 'An emergency department', 'uni': 'A university campus', 'oval': 'Adelaide Oval', 'hills': 'The Hills', 'shops': 'A shopping centre'}
RUNS = {'free': 'By car, at the speed limit, no traffic', 'am': 'By car, morning rush hour', 'pm': 'By car, evening rush hour', 'typical': 'By car, typical speeds (older model)', 'pt': 'By public transport, arriving 8 to 9 am'}
key = lambda run, d: f'pt_{d}' if run == 'pt' else f'car_{run}_{d}'
INF = float('inf')
def mins(run, d): return [INF if v is None else v for v in R[key(run, d)]]
def share(test): return sum(w for w, t in zip(W, test) if t) / TOT
def wmedian(vals):
    pairs = sorted(zip(vals, W)); acc = 0
    for v, w in pairs:
        acc += w
        if acc >= TOT / 2: return None if v == INF else round(v, 1)
r3 = lambda x: round(x, 3)
N = {'residents': round(TOT), 'mesh_block_parts': len(H), 'threshold_min': 20, 'network': META.get('network'), 'pt': META.get('pt'), 'destinations': {}, 'runs': RUNS}
# per destination and run
for d in IDS + ['hospital9']:
    N['destinations'][d] = {'name': NAMES.get(d, 'Emergency departments with the Women’s and Children’s, Gawler and Mount Barker'), 'short': SHORT.get(d), 'runs': {}}
    for run in RUNS:
        if key(run, d) not in R: continue
        m = mins(run, d)
        N['destinations'][d]['runs'][run] = {'within_20': r3(share([v <= 20 for v in m])), 'people_20': round(sum(w for w, v in zip(W, m) if v <= 20)), 'median_min': wmedian(m),
                                             'within_15': r3(share([v <= 15 for v in m])), 'within_30': r3(share([v <= 30 for v in m])), 'not_reached': r3(share([v == INF for v in m]))}
# all eight: within 20 of every one; how many of the eight within 20; the minutes needed for all eight (the farthest)
N['all'] = {}
for run in RUNS:
    if not all(key(run, d) in R for d in IDS): continue
    M = [mins(run, d) for d in IDS]
    far = [max(M[k][i] for k in range(len(IDS))) for i in range(len(H))]
    cnt = [sum(1 for k in range(len(IDS)) if M[k][i] <= 20) for i in range(len(H))]
    N['all'][run] = {'within_20': r3(share([v <= 20 for v in far])), 'people_20': round(sum(w for w, v in zip(W, far) if v <= 20)), 'median_min_for_all': wmedian(far),
                     'count_dist': [r3(share([c == n for c in cnt])) for n in range(len(IDS) + 1)], 'mean_count': round(sum(w * c for w, c in zip(W, cnt)) / TOT, 2),
                     'within_30': r3(share([v <= 30 for v in far])), 'within_40': r3(share([v <= 40 for v in far]))}
# without the Hills and the airport (the two far ends): the six others
for run in ['free', 'am', 'pt']:
    six = ['cbd', 'beach', 'hospital', 'uni', 'oval', 'shops']
    far = [max(mins(run, d)[i] for d in six) for i in range(len(H))]
    N['all'][run]['six_no_hills_airport_20'] = r3(share([v <= 20 for v in far]))
# the curve: share within X minutes for the city and for all eight, each run
N['curve'] = {}
for run in ['free', 'am', 'pt']:
    M = [mins(run, d) for d in IDS]; far = [max(M[k][i] for k in range(len(IDS))) for i in range(len(H))]
    c = mins(run, 'cbd')
    N['curve'][run] = {'minutes': list(range(0, 91, 5)), 'cbd': [r3(share([v <= x for v in c])) for x in range(0, 91, 5)], 'all': [r3(share([v <= x for v in far])) for x in range(0, 91, 5)]}
# the minute-by-minute counter for the hero (city, by car, little traffic and rush hour; by public transport)
N['counter'] = {run: [r3(share([v <= x for v in mins(run, 'cbd')])) for x in range(0, 61)] for run in ['free', 'am', 'pt']}
# minutes histogram to the city (people per minute), free and am
N['hist_cbd'] = {run: [round(sum(w for w, v in zip(W, mins(run, 'cbd')) if x <= v < x + 1)) for x in range(0, 70)] for run in ['free', 'am']}
# by SA2
names = {}
gj = json.load(open(os.path.join(B, 'raw/abs/sa2-adelaide.geojson')))
for f in gj['features']: names[str(f['properties']['code'])] = f['properties']['name']
by = {}
Mf = [mins('free', d) for d in IDS]; Ma = [mins('am', d) for d in IDS]; Mp = [mins('pt', d) for d in IDS]
for i, h in enumerate(H):
    s = by.setdefault(h['sa2'], {'people': 0, 'all_free': 0, 'all_am': 0, 'cnt_free': 0, 'cnt_am': 0, 'cnt_pt': 0, 'cbd_free': 0, 'cbd_am': 0, 'cbd_pt': 0, 'cbd_pt_n': 0, **{f'{d}_free': 0 for d in IDS}})
    w = W[i]; s['people'] += w
    cf = sum(1 for k in range(8) if Mf[k][i] <= 20); ca = sum(1 for k in range(8) if Ma[k][i] <= 20); cp = sum(1 for k in range(8) if Mp[k][i] <= 20)
    s['cnt_free'] += w * cf; s['cnt_am'] += w * ca; s['cnt_pt'] += w * cp
    s['all_free'] += w * (cf == 8); s['all_am'] += w * (ca == 8)
    for k, d in enumerate(IDS): s[f'{d}_free'] += w * (Mf[k][i] <= 20)
    s['cbd_free'] += w * Mf[0][i]; s['cbd_am'] += w * Ma[0][i]
    if Mp[0][i] < INF: s['cbd_pt'] += w * Mp[0][i]; s['cbd_pt_n'] += w
os.makedirs(os.path.join(B, 'tables'), exist_ok=True)
rows = []
for code, s in by.items():
    p = s['people']
    if p < 1: continue
    rows.append({'sa2_code': code, 'sa2_name': names.get(code, code), 'residents': round(p), 'share_all_eight_free': r3(s['all_free'] / p), 'share_all_eight_am': r3(s['all_am'] / p),
                 'places_within_20_free': round(s['cnt_free'] / p, 2), 'places_within_20_am': round(s['cnt_am'] / p, 2), 'places_within_20_pt': round(s['cnt_pt'] / p, 2),
                 'mean_min_city_free': round(s['cbd_free'] / p, 1), 'mean_min_city_am': round(s['cbd_am'] / p, 1), 'mean_min_city_pt': round(s['cbd_pt'] / s['cbd_pt_n'], 1) if s['cbd_pt_n'] else None,
                 **{f'share_{d}_free': r3(s[f'{d}_free'] / p) for d in IDS}})
rows.sort(key=lambda r: (-r['places_within_20_free'], r['mean_min_city_free']))
with open(os.path.join(B, 'tables/sa2.csv'), 'w', newline='') as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
big = [r for r in rows if r['residents'] >= 3000]
N['sa2'] = {'count': len(rows), 'best': sorted(big, key=lambda r: (-r['share_all_eight_free'], -r['places_within_20_free']))[:10],
            'worst': sorted(big, key=lambda r: (r['places_within_20_free'], -r['mean_min_city_free']))[:10],
            'holds_free': sum(1 for r in rows if r['share_all_eight_free'] >= 0.5), 'holds_am': sum(1 for r in rows if r['share_all_eight_am'] >= 0.5)}
# per destination table
with open(os.path.join(B, 'tables/destinations.csv'), 'w', newline='') as f:
    wr = csv.writer(f); wr.writerow(['destination', 'run', 'share_within_20', 'residents_within_20', 'median_min', 'share_within_15', 'share_within_30', 'share_not_reached'])
    for d, v in N['destinations'].items():
        for run, x in v['runs'].items(): wr.writerow([v['name'], RUNS[run], x['within_20'], x['people_20'], x['median_min'], x['within_15'], x['within_30'], x['not_reached']])
json.dump(N, open(os.path.join(B, 'numbers.json'), 'w'), indent=1)
pct = lambda x: f'{x * 100:.1f}%'
for d in IDS: print(f"{SHORT[d]:28s}", ' '.join(f"{run}:{pct(N['destinations'][d]['runs'][run]['within_20'])}/{N['destinations'][d]['runs'][run]['median_min']}" for run in RUNS if run in N['destinations'][d]['runs']))
for run, a in N['all'].items(): print('ALL', run, pct(a['within_20']), a['people_20'], 'median for all', a['median_min_for_all'], 'mean count', a['mean_count'], 'dist', a['count_dist'], 'six', a.get('six_no_hills_airport_20'))
print('hosp9 free', N['destinations']['hospital9']['runs']['free'])
print('best', [(r['sa2_name'], r['share_all_eight_free']) for r in N['sa2']['best']])
print('worst', [(r['sa2_name'], r['places_within_20_free']) for r in N['sa2']['worst']])
print('SA2s where most have all eight, free', N['sa2']['holds_free'], 'am', N['sa2']['holds_am'], 'of', len(rows))
