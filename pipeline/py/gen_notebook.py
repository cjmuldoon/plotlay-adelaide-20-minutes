# Writes python/adelaide_20_minutes.ipynb for the public repo: a short narrated notebook that reads only ../data and
# gets the page's numbers again (the share within 20 minutes of each place and of all eight, by car and public
# transport, and the areas where it holds). Execute it afterwards with nbconvert (outputs kept).
#   python -I gen_notebook.py <repo dir>
import sys, os, nbformat as nbf
REPO = sys.argv[1]
nb = nbf.v4.new_notebook(); C = []
md = lambda s: C.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: C.append(nbf.v4.new_code_cell(s.strip()))
md('''
# Is everything in Adelaide 20 minutes away?

The drive from every Greater Adelaide mesh block to eight places, at the speed limit with no traffic (`free`), in
TomTom's 2025 morning and evening rush-hour slowdown (`am`, `pm`), and by public transport arriving 8 to 9 am (`pt`).
Made in [Plotlay](https://www.getplotlay.com). This notebook reads only `../data`.

**Read it carefully.** The rush hour is a city-wide average slowdown, not a traffic forecast; the trips go to the
nearest place of each kind and leave out parking.
''')
code('''
import pandas as pd
DATA = '../data'
mb = pd.read_csv(f'{DATA}/mesh_block_minutes.csv', dtype={'mb_code': str, 'sa2_code': str})
PLACES = ['cbd', 'beach', 'airport', 'hospital', 'uni', 'oval', 'hills', 'shops']
total = mb.residents.sum()
print(f'{len(mb):,} mesh blocks, {total:,.0f} residents')
''')
md('## Within 20 minutes of each place\n\nA mesh block counts when its minutes are 20 or fewer; empty means not reached.')
code('''
def share(run, place, limit=20):
    m = mb[f'{run}_{place}']
    return (mb.residents * (m <= limit)).sum() / total
table = pd.DataFrame({run: {p: share(run, p) for p in PLACES} for run in ['free', 'am', 'pm', 'pt']})
(table * 100).round(1).sort_values('free', ascending=False)
''')
md('## All eight')
code('''
def all_eight(run, limit=20):
    ok = pd.concat([mb[f'{run}_{p}'] <= limit for p in PLACES], axis=1).all(axis=1)
    return (mb.residents * ok).sum() / total
for run in ['free', 'am', 'pm', 'typical', 'pt']:
    print(f'{run:8s} {all_eight(run) * 100:5.1f}% within 20 minutes of all eight')
''')
md('## How many of the eight, at the speed limit')
code('''
count = sum((mb[f'free_{p}'] <= 20).astype(int) for p in PLACES)
(mb.groupby(count).residents.sum() / total * 100).round(1).rename('share of residents (%)')
''')
md('## Where it holds: areas where most residents have all eight')
code('''
sa2 = pd.read_csv(f'{DATA}/sa2.csv', dtype={'sa2_code': str})
sa2[sa2.residents >= 3000].sort_values('share_all_eight_free', ascending=False)[['sa2_name', 'residents', 'share_all_eight_free', 'places_within_20_free', 'mean_min_city_free']].head(10)
''')
md('## Where it fails')
code('''
sa2[sa2.residents >= 3000].sort_values('places_within_20_free')[['sa2_name', 'residents', 'places_within_20_free', 'mean_min_city_free', 'mean_min_city_am']].head(10)
''')
nb['cells'] = C
nb['metadata'] = {'kernelspec': {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'}}
nbf.write(nb, os.path.join(REPO, 'python', 'adelaide_20_minutes.ipynb'))
print('notebook')
