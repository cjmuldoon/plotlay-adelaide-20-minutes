"""The headline map: every Greater Adelaide mesh block with residents, coloured by how many of the eight places are within
20 minutes by car (at the speed limit with no traffic, or in the TomTom rush hour), 0 to 8, cool below four and warm from
four up, so "half the places or more" is the line you see. Drawn over Plotlay's Ink base map (scripts/bases.mjs, from the
app) with the place names on top, a legend and the credit. Mesh block outlines: ABS ASGS Edition 3 (2021).
  python3 -I py/mbmap.py <build dir> <mesh block pages dir> <out dir>     writes mbmap_<run>_<1x1|16x9>.png"""
import sys, os, json, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
B, MBDIR, OUT = sys.argv[1:4]
sys.argv = [sys.argv[0], B]
sys.path.insert(0, os.path.join(B, 'py'))
import hero as Hh
J = Hh.J; N = Hh.N; FONT = Hh.FONT; text = Hh.text
IDS = ['cbd', 'beach', 'airport', 'hospital', 'uni', 'oval', 'hills', 'shops']
# 0 to 3 places: blues, dark to light; 4 to 8: warm, yellow to red (the hero's colours)
COL = [(56, 70, 150), (72, 100, 200), (96, 150, 240), (120, 200, 250), (255, 226, 140), (255, 196, 90), (255, 160, 70), (255, 120, 64), (240, 84, 70)]

T = J('out/times.json'); H = T['homes']
def counts(run):
    M = [[(v if v is not None else 1e9) for v in T['runs'][f'car_{run}_{d}']] for d in IDS]
    by = {}
    for i, h in enumerate(H):
        c = sum(1 for k in range(8) if M[k][i] <= 20)
        a = by.setdefault(h['code'], [0.0, 0.0]); a[0] += h['people'] * c; a[1] += h['people']
    return {k: round(s / w) if w else None for k, (s, w) in by.items()}

polys = {}
for f in sorted(glob.glob(os.path.join(MBDIR, 'page_*.json'))):
    for ft in json.load(open(f))['features']:
        g = ft.get('geometry'); code = str(ft['properties']['mb_code_2021'])
        if not g: continue
        polys[code] = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']

def render(run, vname, tag):
    v = VIEWS[vname]; P = Hh.projector(v)
    base = Image.open(os.path.join(B, 'app/bases', f'{vname}-nolabels.jpg')).convert('RGB')
    W, Hgt = base.size; fill = Image.new('RGB', (W, Hgt)); mask = Image.new('L', (W, Hgt), 0)
    df, dm = ImageDraw.Draw(fill), ImageDraw.Draw(mask)
    cnt = counts(run)
    for code, c in cnt.items():
        if c is None or code not in polys: continue
        for pl in polys[code]:
            ring = [P(la, ln) for ln, la in pl[0]]
            if len(ring) < 3: continue
            df.polygon(ring, fill=COL[c]); dm.polygon(ring, fill=225)
    img = Image.composite(fill, base, mask)
    # the place names over the colours (the base with names, where it differs from the one without)
    nl = Image.open(os.path.join(B, 'app/bases', f'{vname}.jpg')).convert('RGB')
    diff = np.abs(np.asarray(nl, dtype=np.int16) - np.asarray(base, dtype=np.int16)).max(axis=2)
    k = Hgt / 1080; pw = round(470 * k) if tag == '16x9' else round(430 * k)
    nm = np.clip((diff - 10) * 6, 0, 255).astype(np.uint8); nm[:, :pw] = 0   # no names under the words
    img.paste(nl, (0, 0), Image.fromarray(nm))
    a = N['all'][run]
    lab = 'At the speed limit, no traffic' if run == 'free' else 'Morning rush hour (TomTom Traffic Index 2025)'
    # a dark panel for the words and the key
    panel = Image.new('L', (W, Hgt), 0); ImageDraw.Draw(panel).rectangle([0, 0, pw, Hgt], fill=200)
    img = Image.composite(Image.new('RGB', (W, Hgt), (12, 16, 24)), img, panel.filter(ImageFilter.GaussianBlur(30 * k))); d = ImageDraw.Draw(img)
    x = round(44 * k); y = round(52 * k)
    text(d, (x, y), 'HOW MANY OF THE EIGHT PLACES', FONT(Hh.SANS_SB, round(22 * k)), fill=(170, 186, 210))
    text(d, (x, y + round(30 * k)), 'ARE WITHIN 20 MINUTES BY CAR', FONT(Hh.SANS_SB, round(22 * k)), fill=(170, 186, 210))
    text(d, (x - 4, y + round(70 * k)), f"{a['half_20'] * 100:.0f}%", FONT(Hh.COND_B, round(150 * k)), fill=(255, 196, 96))
    text(d, (x, y + round(240 * k)), 'have half or more (4 of 8)', FONT(Hh.SANS_SB, round(30 * k)))
    text(d, (x, y + round(282 * k)), lab, FONT(Hh.SANS, round(22 * k)), fill=(150, 205, 250))
    ky = y + round(350 * k); sw = round(30 * k); gap = round(38 * k)
    for n in range(8, -1, -1):
        yy = ky + (8 - n) * gap
        d.rectangle([x, yy, x + sw, yy + sw], fill=COL[n])
        share = a['count_dist'][n] * 100
        text(d, (x + sw + round(14 * k), yy + round(2 * k)), f"{n} place{'s' if n != 1 else ''}  {share:.0f}%", FONT(Hh.SANS, round(22 * k)), shadow=False)
        if n == 4: d.line([(x - round(6 * k), yy + sw + round(4 * k)), (x + round(250 * k), yy + sw + round(4 * k))], fill=(255, 255, 255), width=max(2, round(2 * k)))
    text(d, (x, ky + 9 * gap + round(4 * k)), 'Above the line: half the places or more', FONT(Hh.SANS, round(18 * k)), fill=(200, 210, 224), shadow=False)
    Hh.credit(img, k); d = ImageDraw.Draw(img); d.rectangle([0, Hgt - round(40 * k), W, Hgt], fill=(10, 14, 22))
    d.text((W - round(24 * k), Hgt - round(14 * k)), 'Mesh blocks with residents: ABS 2021 Census · Roads © OpenStreetMap contributors (ODbL)' + (' · Rush hour: TomTom Traffic Index 2025' if run == 'am' else '') + ' · Plotlay Ink, Protomaps · Made in Plotlay', font=FONT(Hh.SANS, round(15 * k)), fill=(160, 172, 192), anchor='rs')
    os.makedirs(OUT, exist_ok=True); img.save(os.path.join(OUT, f'mbmap_{run}_{tag}.png'))

VIEWS = Hh.VIEWS
for run in ('free', 'am'):
    render(run, 'square', '1x1'); render(run, 'wide', '16x9')
print('mbmap', len(polys), 'mesh blocks')
