# The hero animation and the stills: Greater Adelaide's roads lighting up minute by minute from the GPO, on Plotlay's
# own Ink base map (fetched by the app, scripts/bases.mjs), with the live counter of residents reached and the
# 20-minute moment (the reach holds at 20 minutes, its edge pulses). Roads and minutes come from Plotlay's engine
# (out/flow-<run>-cbd.json: core/drivetime.js driveFlow, the same Flow look segments the app draws); the counter
# from numbers.json (the share of residents, by mesh block, within each minute). Public transport draws the
# timetable run's 150 m cells (out/pt-grid-cbd.json) as points of light.
#   python3 -I py/hero.py <build dir> frames <run> <view> <out dir>    run: free | am | pt; view: square | wide
#   python3 -I py/hero.py <build dir> compare <out dir>                car (free) beside public transport, 16:9
#   python3 -I py/hero.py <build dir> grid <out dir>                   the eight places, small multiples
#   python3 -I py/hero.py <build dir> still <run> <view> <minute> <file>
import sys, os, json, math, base64
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops, ImageOps

B = sys.argv[1]
J = lambda f: json.load(open(os.path.join(B, f)))
N = J('numbers.json'); VIEWS = J('app/bases/views.json')
FONT = lambda name, size: ImageFont.truetype(os.path.join(B, 'fonts', name), size)
COND_B, COND, SANS, SANS_SB = 'IBMPlexSansCondensed-Bold.ttf', 'IBMPlexSansCondensed-Regular.ttf', 'IBMPlexSans-Regular.ttf', 'IBMPlexSans-SemiBold.ttf'
FPS = 30
# the colours: warm and bright inside 20 minutes, cool and dimmer past it, so the 20-minute edge is a visible change
STOPS = [(0, (255, 250, 228)), (5, (255, 228, 140)), (10, (255, 196, 84)), (15, (255, 150, 60)), (20, (255, 104, 72)),
         (20.001, (110, 208, 250)), (30, (96, 166, 248)), (40, (128, 128, 245)), (50, (160, 110, 235)), (60, (180, 100, 220))]
def colour(m):
    if m <= STOPS[0][0]: return STOPS[0][1]
    for (a, ca), (b, cb) in zip(STOPS, STOPS[1:]):
        if m <= b:
            t = (m - a) / (b - a) if b > a else 1
            return tuple(int(ca[i] + (cb[i] - ca[i]) * t) for i in range(3))
    return STOPS[-1][1]

def projector(v):
    z, s = v['zoom'], v['scale']
    def world(lat, lng):
        k = 256 * 2 ** z; x = (lng + 180) / 360 * k
        r = math.radians(lat); y = (1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * k
        return x, y
    cx, cy = world(*v['center'])
    def P(lat, lng):
        x, y = world(lat, lng); return ((x - cx + v['W'] / 2) * s, (y - cy + v['H'] / 2) * s)
    # the app's own projection at the test points, to the pixel
    for (q, p) in v['test']:
        x, y = P(*q); assert abs(x - p[0] * s) < 1.5 and abs(y - p[1] * s) < 1.5, (q, p, x, y)
    return P

def segments(run, P):
    """[(x1, y1, x2, y2, minute at the start, span minutes)] in pixels, from the flow file (dm in its own frame)."""
    f = J(f'out/flow-{run}-cbd.json'); lat0, lng0 = f['origin']; mx = 111320 * math.cos(math.radians(lat0)); my = 111132
    ll = lambda x, y: (lat0 + y / 10 / my, lng0 + x / 10 / mx)
    out = []
    for pr in f['profiles'].values():
        S = pr['segs']
        for q in range(0, len(S), 7):
            x1, y1, x2, y2, ca, cb = S[q:q + 6]
            if ca < 0 and cb < 0: continue
            if ca < 0: ca = cb + 1000
            if cb < 0: cb = ca + 1000
            if cb < ca: x1, y1, x2, y2, ca, cb = x2, y2, x1, y1, cb, ca
            a = P(*ll(x1, y1)); b = P(*ll(x2, y2))
            out.append((a[0], a[1], b[0], b[1], ca / 1000, max(0.01, (cb - ca) / 1000)))
    out.sort(key=lambda s: s[4])
    return out

def pt_cells(P):
    g = J('out/pt-grid-cbd.json'); m = np.frombuffer(base64.b64decode(g['minutes']), dtype=np.uint8)
    fr = g['frame']; lat0, lng0 = fr['lat0'], fr['lng0']; mx = 111320 * math.cos(math.radians(lat0)); my = 111132
    nx, ny, G = g['nx'], g['ny'], g.get('G') or g.get('cell') or 150
    x0, y0 = g.get('x0', 0), g.get('y0', 0)
    out = []
    for j in range(ny):
        for i in range(nx):
            v = int(m[j * nx + i])
            if v == 255: continue
            x, y = x0 + (i + 0.5) * G, y0 + (j + 0.5) * G
            out.append((*P(lat0 + y / my, lng0 + x / mx), float(v)))
    out.sort(key=lambda c: c[2])
    return out

def counter_share(run, t):
    c = N['counter'][run]; i = int(math.floor(t)); f = t - i
    if i >= len(c) - 1: return c[-1]
    return c[i] + (c[i + 1] - c[i]) * f

class Painter:
    """Draws the reach at minute t, keeping finished roads on a layer so each frame only adds what is new."""
    def __init__(self, run, vname, scale_w=1.0):
        self.v = VIEWS[vname]; self.P = projector(self.v); self.run = run
        lab = Image.open(os.path.join(B, 'app/bases', f'{vname}.jpg')).convert('RGB')
        self.base = Image.open(os.path.join(B, 'app/bases', f'{vname}-nolabels.jpg')).convert('RGB')
        # the place names: where the named map differs from the plain one (text and its halo), drawn last
        diff = np.abs(np.asarray(lab, dtype=np.int16) - np.asarray(self.base, dtype=np.int16)).max(axis=2)
        self.lab = lab; self.labmask = Image.fromarray(np.clip((diff - 10) * 6, 0, 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))
        self.W, self.H = self.base.size; self.k = self.W / 1080 if vname != 'wide' else self.H / 1080
        self.pt = run == 'pt'
        self.items = pt_cells(self.P) if self.pt else segments(run, self.P)
        self.core = Image.new('RGB', (self.W, self.H)); self.dc = ImageDraw.Draw(self.core)
        self.done = 0; self.lw = max(1, round(1.6 * self.k * scale_w))
        self.cell = max(2, round(150 / (156543 * math.cos(math.radians(-34.93)) / 2 ** self.v['zoom']) * self.v['scale']))
    def _draw(self, d, it, frac=1.0, col=None, w=None):
        if self.pt:
            x, y, m = it; r = self.cell / 2 + 0.6
            d.rectangle([x - r, y - r, x + r, y + r], fill=col or colour(m))
        else:
            x1, y1, x2, y2, m, sp = it
            d.line([(x1, y1), (x1 + (x2 - x1) * frac, y1 + (y2 - y1) * frac)], fill=col or colour(m), width=w or self.lw)
    def frame(self, t, pulse=0.0, dim_past=None):
        it = self.items
        if not hasattr(self, 'start'):
            self.start = np.array([s[2] if self.pt else s[4] for s in it]); self.finish = self.start if self.pt else self.start + np.array([s[5] for s in it])
            self.byfin = np.argsort(self.finish, kind='stable')
        # finished: whole segment reached (committed once, in the order they finish)
        while self.done < len(it) and self.finish[self.byfin[self.done]] <= t:
            self._draw(self.dc, it[self.byfin[self.done]]); self.done += 1
        top = self.core.copy(); dt = ImageDraw.Draw(top)
        # in progress (started, not finished), and the wavefront (started in the last 1.6 minutes), white-hot
        front = Image.new('RGB', (self.W, self.H)); df = ImageDraw.Draw(front)
        for q in np.nonzero((self.start <= t) & ((self.finish > t) | (self.start >= t - 1.6)))[0]:
            s = it[q]; m = s[2] if self.pt else s[4]
            if not self.pt:
                frac = min(1.0, (t - s[4]) / s[5])
                if frac < 1: self._draw(dt, s, frac)
                if m >= t - 1.6: self._draw(df, s, frac, col=(255, 255, 240) if m <= 20 else (225, 240, 255), w=self.lw + 1)
            else: self._draw(df, s, col=(255, 255, 240))
        if pulse > 0 and not self.pt:
            # the 20-minute edge: every road reached between 19 and 20 minutes, flashing white
            for s in it:
                if s[4] > 20: break
                if s[4] >= 18.8: self._draw(df, s, min(1.0, (20 - s[4]) / s[5]), col=(255, 255, 255), w=self.lw + 2)
        if pulse > 0 and self.pt:
            for s in it:
                if s[2] > 20: break
                if s[2] >= 18: self._draw(df, s, col=(255, 255, 255))
        glow = ImageChops.screen(top.filter(ImageFilter.GaussianBlur(4 * self.k)).point(lambda x: int(x * 0.55)), top.filter(ImageFilter.GaussianBlur(16 * self.k)).point(lambda x: int(x * 0.45)))
        fglow = front.filter(ImageFilter.GaussianBlur(4 * self.k))
        img = ImageChops.screen(self.base, glow)
        img = Image.composite(top, img, top.convert('L').point(lambda x: 255 if x > 8 else 0).filter(ImageFilter.GaussianBlur(0.6)))
        g = 0.55 + 0.45 * pulse if pulse > 0 else 0.55
        img = ImageChops.screen(img, fglow.point(lambda x, g=g: int(x * g)))
        img = ImageChops.screen(img, front.point(lambda x, g=g: int(x * (0.45 + 0.4 * g))))
        img.paste(self.lab, (0, 0), self.labmask)
        return img

def text(d, xy, s, font, fill=(240, 244, 250), anchor='la', shadow=True):
    if shadow: d.text((xy[0], xy[1] + 2), s, font=font, fill=(6, 10, 18), anchor=anchor)
    d.text(xy, s, font=font, fill=fill, anchor=anchor)

LABEL = {'free': 'By car, at the speed limit, no traffic', 'am': 'By car, morning rush hour (TomTom 2025)', 'pt': 'By public transport, 8 to 9 am'}
def overlay(img, run, t, k, pulse=0.0, x0=None, y0=None, compact=False):
    """the counter: the minute, the share of Greater Adelaide's residents reached, and what is being drawn"""
    d = ImageDraw.Draw(img); W, H = img.size
    x = x0 if x0 is not None else round(56 * k); y = y0 if y0 is not None else round(60 * k)
    m = min(t, 60); share = counter_share(run, m)
    text(d, (x, y), LABEL[run].upper(), FONT(SANS_SB, round((22 if not compact else 20) * k)), fill=(170, 186, 210))
    y += round(40 * k)
    big = FONT(COND_B, round((150 if not compact else 120) * k))
    col = (255, 214, 120) if m <= 20 else (150, 205, 250)
    if pulse > 0: col = tuple(int(c + (255 - c) * pulse * 0.6) for c in col)
    text(d, (x, y), f'{share * 100:.0f}%', big, fill=col)
    y += round((160 if not compact else 128) * k)
    text(d, (x, y), 'of Greater Adelaide’s', FONT(SANS, round(30 * k)))
    text(d, (x, y + round(38 * k)), 'residents reached', FONT(SANS, round(30 * k)))
    y += round(100 * k)
    clock = FONT(COND_B, round(64 * k))
    text(d, (x, y), f'{int(m):d} min', clock, fill=(255, 255, 255) if m < 20 or pulse > 0 or m > 20.5 else (255, 255, 255))
    if 19.99 <= m <= 20.01 and pulse >= 0:
        text(d, (x, y + round(78 * k)), 'The saying’s limit', FONT(SANS_SB, round(30 * k)), fill=(255, 214, 120))
    return img

def credit(img, k, wide=False, run='free'):
    W, H = img.size; h = round(40 * k)
    strip = Image.new('RGB', (W, h), (10, 14, 22)); img.paste(Image.blend(img.crop((0, H - h, W, H)), strip, 0.82), (0, H - h))
    d = ImageDraw.Draw(img)
    s = 'Roads © OpenStreetMap contributors (ODbL) · Base map Plotlay Ink, tiles Protomaps · Residents ABS 2021 Census · Made in Plotlay'
    if run == 'am': s = 'Rush-hour slowdown: TomTom Traffic Index 2025 · Roads © OpenStreetMap contributors (ODbL) · Plotlay Ink, Protomaps · ABS 2021 Census · Made in Plotlay'
    text(d, (W - round(24 * k), H - round(14 * k)), s, FONT(SANS, round(15 * k)), fill=(160, 172, 192), anchor='rs', shadow=False)

def timeline(hold20=2.5, to20=6.5, past=5.0, end=1.5, last=60):
    """(minute, pulse) for each frame: up to 20 minutes, the hold with its pulse, on to the last minute, a short end"""
    out = []
    n = int(to20 * FPS)
    for i in range(1, n + 1): u = i / n; out.append((20 * (u ** 1.15), 0.0))
    for i in range(int(hold20 * FPS)): out.append((20.0, 0.5 + 0.5 * math.sin(i / FPS * 2 * math.pi * 1.2 - math.pi / 2) if i < hold20 * FPS - 6 else 0.0))
    n = int(past * FPS)
    for i in range(1, n + 1): out.append((20 + (last - 20) * (i / n), 0.0))
    for i in range(int(end * FPS)): out.append((last, 0.0))
    return out

def run_frames(run, vname, outdir, last=60):
    os.makedirs(outdir, exist_ok=True)
    pa = Painter(run, vname); k = pa.k
    tl = timeline(last=last)
    for i, (t, pulse) in enumerate(tl):
        img = pa.frame(t, pulse)
        overlay(img, run, t, k, pulse)
        credit(img, k, run=run)
        img.save(os.path.join(outdir, f'{i:04d}.png'), compress_level=1)
    json.dump({'frames': len(tl), 'fps': FPS}, open(os.path.join(outdir, 'meta.json'), 'w'))
    print(run, vname, len(tl), 'frames')

def compare(outdir, last=60):
    """car at the speed limit beside public transport, the same clock, each with its counter: 1920 x 1080"""
    os.makedirs(outdir, exist_ok=True)
    A = Painter('free', 'square'); Bp = Painter('pt', 'square')
    tl = timeline(last=last)
    for i, (t, pulse) in enumerate(tl):
        a = A.frame(t, pulse); b = Bp.frame(t, pulse)
        img = Image.new('RGB', (1920, 1080), (14, 18, 26))
        img.paste(a.resize((960, 960), Image.LANCZOS), (0, 120)); img.paste(b.resize((960, 960), Image.LANCZOS), (960, 120))
        d = ImageDraw.Draw(img); d.line([(960, 120), (960, 1080)], fill=(40, 48, 62), width=2)
        k = 960 / 1080
        overlay(img, 'free', t, k * 0.92, pulse, x0=36, y0=150, compact=True)
        overlay(img, 'pt', t, k * 0.92, pulse, x0=996, y0=150, compact=True)
        text(d, (960, 64), 'To the GPO: the car against public transport, minute by minute', FONT(COND_B, 46), anchor='mm')
        d.text((1896, 1060), 'Roads © OpenStreetMap contributors (ODbL) · Timetable Adelaide Metro (CC BY 4.0) · Base map Plotlay Ink, tiles Protomaps · ABS 2021 Census · Made in Plotlay', font=FONT(SANS, 14), fill=(150, 162, 182), anchor='rs')
        img.save(os.path.join(outdir, f'{i:04d}.png'), compress_level=1)
    print('compare', len(tl), 'frames')

def compare_square(outdir, last=60):
    """the compare for a phone: the two maps side by side on top, each counter large beneath its map: 1080 x 1080"""
    os.makedirs(outdir, exist_ok=True)
    A = Painter('free', 'square'); Bp = Painter('pt', 'square')
    tl = timeline(last=last)
    for i, (t, pulse) in enumerate(tl):
        a = A.frame(t, pulse); b = Bp.frame(t, pulse)
        img = Image.new('RGB', (1080, 1080), (14, 18, 26))
        img.paste(a.resize((540, 540), Image.LANCZOS), (0, 110)); img.paste(b.resize((540, 540), Image.LANCZOS), (540, 110))
        d = ImageDraw.Draw(img); d.line([(540, 110), (540, 1040)], fill=(40, 48, 62), width=2)
        text(d, (540, 58), 'To the GPO: car against public transport', FONT(COND_B, 44), anchor='mm')
        m = min(t, 60)
        for x0, run, lab in ((40, 'free', 'CAR, SPEED LIMIT, NO TRAFFIC'), (580, 'pt', 'PUBLIC TRANSPORT, 8 TO 9 AM')):
            text(d, (x0, 680), lab, FONT(SANS_SB, 22), fill=(170, 186, 210))
            col = (255, 214, 120) if m <= 20 else (150, 205, 250)
            text(d, (x0, 712), f'{counter_share(run, m) * 100:.0f}%', FONT(COND_B, 150), fill=col)
            text(d, (x0, 880), 'of residents reached', FONT(SANS, 30))
        text(d, (540, 960), f'{int(m):d} min', FONT(COND_B, 64), anchor='mm')
        d.text((1064, 1068), 'OpenStreetMap (ODbL) · Adelaide Metro (CC BY 4.0) · Plotlay Ink, Protomaps · ABS 2021 · Made in Plotlay', font=FONT(SANS, 15), fill=(150, 162, 182), anchor='rs')
        img.save(os.path.join(outdir, f'{i:04d}.png'), compress_level=1)
    print('compare square', len(tl), 'frames')

if __name__ == '__main__':
    cmd = sys.argv[2]
    if cmd == 'compare1': compare_square(sys.argv[3])
    if cmd == 'frames': run_frames(sys.argv[3], sys.argv[4], sys.argv[5])
    elif cmd == 'compare': compare(sys.argv[3])
    elif cmd == 'still':
        run, vname, minute, f = sys.argv[3], sys.argv[4], float(sys.argv[5]), sys.argv[6]
        pa = Painter(run, vname); img = pa.frame(minute, 1.0 if minute == 20 else 0.0)
        overlay(img, run, minute, pa.k, 1.0 if minute == 20 else 0.0); credit(img, pa.k, run=run); img.save(f); print(f)

ORDER = ['shops', 'hospital', 'uni', 'beach', 'oval', 'cbd', 'airport', 'hills']
TITLE = {'cbd': 'The city', 'beach': 'A beach', 'airport': 'The airport', 'hospital': 'An emergency department', 'uni': 'A university campus', 'oval': 'Adelaide Oval', 'hills': 'The Hills', 'shops': 'A shopping centre'}
_GRID = None; _MASK = {}
def gcca_mask(vname, size):
    """Greater Adelaide (its 112 SA2 areas) as a mask in the view's pixels"""
    if vname in _MASK: return _MASK[vname]
    P = projector(VIEWS[vname]); m = Image.new('L', size, 0); dm = ImageDraw.Draw(m)
    for f in J('raw/abs/sa2-adelaide.geojson')['features']:
        g = f['geometry']; polys = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
        for pl in polys:
            dm.polygon([P(la, ln) for ln, la in pl[0]], fill=255)
            for h in pl[1:]: dm.polygon([P(la, ln) for ln, la in h], fill=0)
    _MASK[vname] = m; return m
def mini(d, size=(540, 600), run='free'):
    """one place: its catchment as filled land, warm within 20 minutes by car, cool past it, inside Greater Adelaide,
    the places themselves as small white pins"""
    global _GRID
    v = VIEWS['mini']; P = projector(v)
    lab = Image.open(os.path.join(B, 'app/bases', 'mini-nolabels.jpg')).convert('RGB')
    if _GRID is None: _GRID = J('out/grid.json')
    G = _GRID; nx, ny, c = G['nx'], G['ny'], G['cell_m']; s0, w0 = G['box'][0], G['box'][1]
    MY = 111132; MX = 111320 * math.cos(math.radians(-34.95))
    g = np.frombuffer(base64.b64decode(G[run][d]), dtype=np.uint8).reshape(ny, nx)
    fill = Image.new('RGB', lab.size); df = ImageDraw.Draw(fill)
    for jj in range(ny):
        la0, la1 = s0 + jj * c / MY, s0 + (jj + 1) * c / MY
        for ii in range(nx):
            mm = g[jj, ii]
            if mm == 255: continue
            ln0, ln1 = w0 + ii * c / MX, w0 + (ii + 1) * c / MX
            (x0, y0), (x1, y1) = P(la1, ln0), P(la0, ln1)
            df.rectangle([x0, y0, x1 + 0.6, y1 + 0.6], fill=(255, 176, 72) if mm <= 20 else (64, 104, 182))
    mask = gcca_mask('mini', lab.size).point(lambda x: int(x * 0.86))
    img = Image.composite(fill, lab, mask)
    img = ImageChops.screen(img, Image.composite(fill, Image.new('RGB', lab.size), mask).filter(ImageFilter.GaussianBlur(6)).point(lambda x: int(x * 0.25)))
    # the place names over the colours
    nl = Image.open(os.path.join(B, 'app/bases', 'mini.jpg')).convert('RGB')
    diff = np.abs(np.asarray(nl, dtype=np.int16) - np.asarray(lab, dtype=np.int16)).max(axis=2)
    over = Image.new('RGBA', img.size, (0, 0, 0, 0))
    over.paste(nl, (0, 0), Image.fromarray(np.clip((diff - 10) * 6, 0, 255).astype(np.uint8)))
    from destinations_py import points_of
    names = over.copy(); pins = Image.new('RGBA', img.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(pins)
    pts = points_of(d); r = 2.4 if len(pts) > 30 else 4.5
    for (la, ln) in pts:
        x, y = P(la, ln)
        dr.ellipse([x - r - 1.5, y - r - 1.5, x + r + 1.5, y + r + 1.5], fill=(14, 18, 26, 255)); dr.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 255))
    over.paste(pins, (0, 0), pins)
    under = img.copy(); img.paste(over, (0, 0), over); img.info['over'] = over; img.info['under'] = under; img.info['names'] = names; img.info['pins'] = pins
    return img

def grid(outdir, run='free'):
    os.makedirs(outdir, exist_ok=True)
    sys.path.insert(0, os.path.join(B, 'py'))
    tiles = {d: mini(d, run=run) for d in ORDER}
    def panel(d, w, h):
        sz = (w, round(w * 600 / 540)); full = tiles[d].info['under'].resize(sz, Image.LANCZOS); ov = tiles[d].info['names'].resize(sz, Image.LANCZOS); pn = tiles[d].info['pins'].resize(sz, Image.LANCZOS); off = max(0, (full.size[1] - h) // 2)
        t = full.crop((0, off, w, off + h)); ov = ov.crop((0, off, w, off + h)); pn = pn.crop((0, off, w, off + h)); k = w / 480
        # a soft dark corner behind the words, the names and pins kept above it
        sh_ = Image.new('L', (w, h), 0); ds = ImageDraw.Draw(sh_); ds.rectangle([0, 0, round(190 * k), round(185 * k)], fill=210)
        sh_ = sh_.filter(ImageFilter.GaussianBlur(18 * k))
        t = Image.composite(Image.new('RGB', (w, h), (12, 16, 24)), t, sh_)
        # names and pins fade out under the words, so the share is never crossed by a town name
        om = Image.new('L', (w, h), 0); ImageDraw.Draw(om).rectangle([0, 0, w, round(190 * k)], fill=255)
        ov.putalpha(ImageChops.multiply(ov.getchannel('A'), ImageOps.invert(om.filter(ImageFilter.GaussianBlur(6 * k)))))
        t.paste(ov, (0, 0), ov); t.paste(pn, (0, 0), pn)
        dr = ImageDraw.Draw(t)
        x = round(22 * k)
        text(dr, (x, round(20 * k)), TITLE[d], FONT(COND_B, round(30 * k)))
        sh = N['destinations'][d]['runs'][run]['within_20']; am = N['destinations'][d]['runs']['am']['within_20']
        text(dr, (x, round(58 * k)), f'{sh * 100:.0f}%', FONT(COND_B, round(76 * k)), fill=(255, 196, 96))
        text(dr, (x, round(142 * k)), 'within 20 min', FONT(SANS, round(19 * k)), fill=(225, 230, 240))
        text(dr, (x, round(168 * k)), f'Rush hour: {am * 100:.0f}%', FONT(SANS, round(19 * k)), fill=(150, 200, 250))
        return t
    # 16:9: four by two
    W, Hh = 1920, 1080; img = Image.new('RGB', (W, Hh), (14, 18, 26)); top = 128
    pw, ph = 480, (Hh - top - 40) // 2
    for n, d in enumerate(ORDER): img.paste(panel(d, pw, ph), ((n % 4) * pw, top + (n // 4) * ph))
    dr = ImageDraw.Draw(img)
    text(dr, (40, 22), 'Is everything in Adelaide 20 minutes away? Eight places, by car', FONT(COND_B, 50))
    dr.text((40, 112), 'By car at the speed limit, no traffic. Orange: within 20 minutes. Blue: further. White: the places. Rush hour: TomTom 2025.', font=FONT(SANS, 21), fill=(190, 200, 214), anchor='ls')
    for n in range(1, 4): dr.line([(n * pw, top), (n * pw, top + 2 * ph)], fill=(14, 18, 26), width=4)
    dr.line([(0, top + ph), (W, top + ph)], fill=(14, 18, 26), width=4)
    dr.text((W - 24, Hh - 12), 'Roads © OpenStreetMap contributors (ODbL) · Rush hour: TomTom Traffic Index 2025 · Base map Plotlay Ink, tiles Protomaps · Residents ABS 2021 Census, by mesh block · Made in Plotlay', font=FONT(SANS, 15), fill=(150, 162, 182), anchor='rs')
    img.save(os.path.join(outdir, 'grid_16x9.png'))
    # 1:1: three by three, the ninth the answer for all eight
    S = 1080; img = Image.new('RGB', (S, S), (14, 18, 26)); top = 96; pw = S // 3; ph = (S - top - 30) // 3
    for n, d in enumerate(ORDER): img.paste(panel(d, pw, ph), ((n % 3) * pw, top + (n // 3) * ph))
    dr = ImageDraw.Draw(img)
    text(dr, (28, 26), 'Eight places, 20 minutes by car', FONT(COND_B, 46))
    x0, y0 = 2 * pw + 22, top + 2 * ph + 16; a = N['all']
    text(dr, (x0, y0), 'Half or more', FONT(COND_B, 30))
    text(dr, (x0, y0 + 36), f"{a['free']['half_20'] * 100:.0f}%", FONT(COND_B, 76), fill=(255, 196, 96))
    text(dr, (x0, y0 + 120), '4 of 8 within 20 min', FONT(SANS, 19), fill=(225, 230, 240))
    text(dr, (x0, y0 + 146), f"Rush hour: {a['am']['half_20'] * 100:.0f}%", FONT(SANS, 19), fill=(150, 200, 250))
    text(dr, (x0, y0 + 190), 'Speed limit, no traffic.', FONT(SANS, 16), fill=(180, 190, 206))
    text(dr, (x0, y0 + 212), 'Rush hour: TomTom 2025.', FONT(SANS, 16), fill=(180, 190, 206))
    dr.text((S - 16, S - 10), 'OpenStreetMap (ODbL) · TomTom Traffic Index 2025 · Plotlay Ink, Protomaps · ABS 2021 Census · Made in Plotlay', font=FONT(SANS, 13), fill=(150, 162, 182), anchor='rs')
    img.save(os.path.join(outdir, 'grid_1x1.png'))
    # the tiles alone for the page (its words are HTML), and two pages of four for the square video
    for d in ORDER: tiles[d].save(os.path.join(outdir, f'mini_{d}.jpg'), quality=88)
    for n, part in enumerate((ORDER[:4], ORDER[4:])):
        img = Image.new('RGB', (S, S), (14, 18, 26)); top = 96; pw = S // 2; ph = (S - top - 30) // 2
        for q, d in enumerate(part): img.paste(panel(d, pw, ph), ((q % 2) * pw, top + (q // 2) * ph))
        dr = ImageDraw.Draw(img)
        text(dr, (28, 24), 'Within 20 minutes by car' if n == 0 else 'Further: the city, the Oval, the airport, the Hills', FONT(COND_B, 44))
        dr.line([(pw, top), (pw, top + 2 * ph)], fill=(14, 18, 26), width=4); dr.line([(0, top + ph), (S, top + ph)], fill=(14, 18, 26), width=4)
        dr.text((S - 16, S - 10), 'At the speed limit, no traffic · Rush hour: TomTom Traffic Index 2025 · OpenStreetMap (ODbL) · ABS 2021 · Made in Plotlay', font=FONT(SANS, 15), fill=(160, 172, 192), anchor='rs')
        img.save(os.path.join(outdir, f'grid4{"ab"[n]}_1x1.png'))
    print('grid', outdir)

if __name__ == '__main__' and sys.argv[2] == 'grid': grid(sys.argv[3])

def cards(outdir):
    """the opener (a big number, frame one is the thumbnail) and the end card, square and wide"""
    os.makedirs(outdir, exist_ok=True)
    a = N['all']['free']['half_20']; am = N['all']['am']['half_20']; pt = N['all']['pt']['half_20']
    for (W, H, tag) in ((1080, 1080, '1x1'), (1920, 1080, '16x9')):
        k = H / 1080
        for kind in ('open', 'end'):
            base = Image.open(os.path.join(B, 'app/bases', ('square' if tag == '1x1' else 'wide') + '-nolabels.jpg')).convert('RGB').resize((W, H))
            img = Image.blend(base, Image.new('RGB', (W, H), (10, 14, 22)), 0.55); d = ImageDraw.Draw(img)
            x = round(80 * k) if tag == '1x1' else 140
            if kind == 'open':
                text(d, (x, round(150 * k)), 'IS EVERYTHING IN ADELAIDE 20 MINUTES AWAY?', FONT(SANS_SB, round(30 * k)), fill=(170, 186, 210))
                text(d, (x - 8, round(200 * k)), f'{a * 100:.0f}%', FONT(COND_B, round(330 * k)), fill=(255, 196, 96))
                text(d, (x, round(560 * k)), 'of Adelaideans have at least half', FONT(SANS_SB, round(50 * k)))
                text(d, (x, round(626 * k)), 'the eight places within 20 minutes', FONT(SANS_SB, round(50 * k)))
                text(d, (x, round(730 * k)), f'At the speed limit, no traffic. Rush hour: {am * 100:.0f}%.', FONT(SANS, round(34 * k)), fill=(150, 205, 250))
            else:
                text(d, (x, round(230 * k)), 'Everything 20 minutes away?', FONT(COND_B, round(72 * k)))
                for i, (ln, col) in enumerate(((f'At least half the places for {a * 100:.0f}%,', (255, 214, 120)), ('at the speed limit with no traffic.', (255, 214, 120)),
                                               (f'Rush hour: {am * 100:.0f}%.', (150, 205, 250)), (f'Public transport: {pt * 100:.0f}%.', (150, 205, 250)))):
                    text(d, (x, round((340 + i * 52 + (24 if i >= 2 else 0)) * k)), ln, FONT(SANS_SB, round(40 * k)), fill=col)
                text(d, (x, round(640 * k)), 'Made in Plotlay', FONT(COND_B, round(60 * k)))
                text(d, (x, round(720 * k)), 'getplotlay.com/showcase/adelaide-20-minutes', FONT(SANS, round(34 * k)), fill=(200, 210, 224))
            d.text((W - round(24 * k), H - round(16 * k)), 'Roads © OpenStreetMap contributors · Rush hour: TomTom Traffic Index 2025 · Adelaide Metro · ABS 2021 Census', font=FONT(SANS, round(16 * k)), fill=(150, 162, 182), anchor='rs')
            img.save(os.path.join(outdir, f'{kind}_{tag}.png'))
    print('cards')

if __name__ == '__main__' and sys.argv[2] == 'cards': cards(sys.argv[3])

def clean(outdir):
    """the map at the 20-minute moment with no counter, for the opener's picture (square and wide)"""
    for vname, tag in (('square', '1x1'), ('wide', '16x9')):
        pa = Painter('free', vname); img = pa.frame(20, 1.0); credit(img, pa.k); img.save(os.path.join(outdir, f'clean_free_{tag}.png'))
    print('clean')

if __name__ == '__main__' and sys.argv[2] == 'clean': clean(sys.argv[3])
