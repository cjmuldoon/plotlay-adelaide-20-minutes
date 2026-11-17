// "Is everything in Adelaide 20 minutes away?" The pipeline's engine run, with Plotlay's own code (the plotlay repo's
// src/core/drivetime.js with core/roadrules.js, and core/gtfs.js, transitrun.js for public transport).
//
// Who: every resident of Greater Adelaide (ABS GCCSA 4GADE), placed at the middle of their 2021 Census mesh block
// (raw/abs/people-adelaide.json: 1,386,882 residents in 15,797 mesh block parts with people).
// What: the eight places of the saying (scripts/destinations.mjs), each the nearest of its kind.
// By car: OpenStreetMap roads of 13 Nov 2026 (raw/osm/roads.opl) with the road rules (one-way streets, turn bans,
// waits at lights and junctions), each road at its speed limit, from each resident TO the place:
//   free     little traffic (free-flow)
//   am       the morning rush hour slowdown of the TomTom Traffic Index 2025 for Adelaide's metro area (preset
//            adelaide-tomtom-2025-am: highways 24.6%, other roads 58.5% slower)
//   pm       the evening rush hour (sensitivity)
//   typical  Plotlay's older model: typical running speeds by kind of road, both ways, no waits (sensitivity)
// By public transport: Adelaide Metro's GTFS (feed version 1718) for Tuesday 17 November 2026, arriving between 08:00
// and 09:00 (the median trip), walking at 5.1 km/h on OpenStreetMap's walkable ways, up to 1,200 m to the first stop
// and from the last, up to 3 changes, 150 m cells.
// Out: out/times.json (minutes per mesh block part, per place and run), out/road-*.json (the roads with their minutes
// to the GPO for the maps), numbers.json (the headline figures).
//   node --max-old-space-size=12288 scripts/run.mjs <plotlay repo> [car] [pt]
import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline';
import { open } from 'node:fs/promises';
import { readOpl } from './opl.mjs';
import { destinations, EXTRA_EDS } from './destinations.mjs';

const [REPO, ...want0] = process.argv.slice(2), want = want0.length ? want0 : ['car', 'pt'];
const T = await import(path.join(REPO, 'src/core/drivetime.js'));
const B = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..'), OUT = path.join(B, 'out');
fs.mkdirSync(OUT, { recursive: true });
const r1 = (x) => (x == null || !Number.isFinite(x) ? null : Math.round(x * 10) / 10);

// people: each mesh block part at its middle (area-weighted centroid of its outer ring)
const ppl = JSON.parse(fs.readFileSync(path.join(B, 'raw/abs/people-adelaide.json'), 'utf8'));
const mbsa2 = JSON.parse(fs.readFileSync(path.join(B, 'raw/abs/mb_sa2.json'), 'utf8'));
function centroid(ring) {
    const lat0 = ring[0][0], mx = 111320 * Math.cos(lat0 * Math.PI / 180), my = 111132;
    let a = 0, cx = 0, cy = 0;
    for (let i = 0; i < ring.length; i++) { const p = ring[i], q = ring[(i + 1) % ring.length]; const x0 = (p[1] - ring[0][1]) * mx, y0 = (p[0] - lat0) * my, x1 = (q[1] - ring[0][1]) * mx, y1 = (q[0] - lat0) * my, f = x0 * y1 - x1 * y0; a += f; cx += (x0 + x1) * f; cy += (y0 + y1) * f; }
    if (Math.abs(a) < 1e-6) return [ring.reduce((t, q) => t + q[0], 0) / ring.length, ring.reduce((t, q) => t + q[1], 0) / ring.length];
    return [lat0 + cy / (3 * a) / my, ring[0][1] + cx / (3 * a) / mx];
}
const homes = ppl.blocks.map((b, i) => ({ i, code: b.code, sa2: mbsa2[b.code]?.sa2 || null, people: b.people, ll: centroid(b.rings[0]) }));
console.log('mesh block parts', homes.length, 'residents', Math.round(homes.reduce((t, h) => t + h.people, 0)));
const D = destinations(B);
const times = fs.existsSync(path.join(OUT, 'times.json')) ? JSON.parse(fs.readFileSync(path.join(OUT, 'times.json'), 'utf8')) : { homes: homes.map((h) => ({ code: h.code, sa2: h.sa2, people: Math.round(h.people * 100) / 100, ll: [Math.round(h.ll[0] * 1e6) / 1e6, Math.round(h.ll[1] * 1e6) / 1e6] })), runs: {} };
const meta = fs.existsSync(path.join(OUT, 'meta.json')) ? JSON.parse(fs.readFileSync(path.join(OUT, 'meta.json'), 'utf8')) : {};

if (want.includes('car')) {
    let t0 = performance.now();
    const els = readOpl(path.join(B, 'raw/osm/roads.opl'));
    const net = T.networkFromElements(els, { rules: true, model: 'limits' });
    const typ = T.networkFromElements(els, { model: 'typical' });
    console.log('networks', net.nodes, net.edges, Math.round(net.length_m / 1000), 'km', ((performance.now() - t0) / 1000).toFixed(1), 's');
    meta.network = { nodes: net.nodes, edges: net.edges, km: Math.round(net.length_m / 1000), signal_nodes: net.rules.signals, sets_of_lights: net.rules.light_sets, turn_bans: net.rules.restrictions,
        turn_bans_left_out: net.rules.restrictions_left_out, one_way_stretches: net.rules.oneway_edges, osm_extract: 'Geofabrik australia-latest.osm.pbf, 2026-11-13T21:22:20Z' };
    const RUNS = { free: { net, opts: { rules: true, direction: 'to' } }, am: { net, opts: { rules: true, direction: 'to', peak: 'adelaide-tomtom-2025-am' } }, pm: { net, opts: { rules: true, direction: 'to', peak: 'adelaide-tomtom-2025-pm' } }, typical: { net: typ, opts: {} } };
    for (const [rk, R] of Object.entries(RUNS)) {
        // sensitivity: the emergency departments with the Women's and Children's and the Gawler and Mount Barker hospitals
        const hosp = D.find((d) => d.id === 'hospital');
        const extra = rk === 'typical' ? [] : [{ id: 'hospital9', points: [...hosp.points, ...EXTRA_EDS.map(([name, a, b]) => ({ name, ll: [a, b] }))] }];
        for (const d of [...D, ...extra]) {
            t0 = performance.now();
            const run = T.fromSources(R.net, d.points.map((q, i) => ({ key: q.name || `${d.id}${i}`, ll: q.ll })), R.opts);
            const mins = new Array(homes.length), near = new Array(homes.length);
            homes.forEach((h, i) => { const r = T.timeAt(run, h.ll); mins[i] = r ? r1(r.minutes) : null; near[i] = r ? r.nearest : null; });
            times.runs[`car_${rk}_${d.id}`] = mins;
            if (rk === 'free') times.runs[`nearest_${d.id}`] = near;
            if (rk === 'free' && run.not_placed.length) console.log('  not placed', d.id, run.not_placed);
            console.log(rk, d.id, ((performance.now() - t0) / 1000).toFixed(1), 's');
            // the roads with their minutes to the GPO (and the nearest beach), for the maps and the example
            if ((rk === 'free' || rk === 'am') && (d.id === 'cbd' || d.id === 'beach')) {
                const nm = T.nodeMinutes(run), out = [];
                const fl = T.driveFlow(run, [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60], { maxSegs: 140000, skip: ['service', 'living_street', 'track'] });
                fs.writeFileSync(path.join(OUT, `flow-${rk}-${d.id}.json`), JSON.stringify(fl));
                console.log('   flow segments', fl.drive.segments, 'simplify', fl.drive.simplify_m);
                // edges as [lat1, lng1, lat2, lng2, min1, min2, class] for the page's road map
                for (let k = 0; k < net.edges; k++) {
                    const w = net.ways[net.way[k]], a = net.a[k], b = net.b[k];
                    if (!w || ['service', 'living_street', 'track'].includes(w.highway)) continue;
                    const ma = nm[a], mb = nm[b];
                    if (!(Math.min(ma, mb) < 90)) continue;
                    out.push([+net.lat[a].toFixed(5), +net.lng[a].toFixed(5), +net.lat[b].toFixed(5), +net.lng[b].toFixed(5), r1(ma), r1(mb), w.highway]);
                }
                fs.writeFileSync(path.join(OUT, `roads-${rk}-${d.id}.json`), JSON.stringify(out));
            }
        }
    }
}

if (want.includes('pt')) {
    const G = await import(path.join(REPO, 'src/core/gtfs.js')), R = await import(path.join(REPO, 'src/core/transitroute.js')), RUN = await import(path.join(REPO, 'src/core/transitrun.js'));
    let t0 = performance.now();
    const fh = await open(path.join(B, 'raw/gtfs/adelaide-metro.zip')), { size } = await fh.stat();
    const src = { size, read: async (o, n) => { const b = new Uint8Array(n); await fh.read(b, 0, n, o); return b; } };
    const DAY = '2026-11-17';
    const tt = await G.readGtfs(src, { date: DAY, from: '06:00', to: '09:00', shapes: false, feedName: 'Adelaide Metro', licence: 'CC BY 4.0' });
    await fh.close();
    console.log('timetable', ((performance.now() - t0) / 1000).toFixed(1), 's');
    const f = R.frameAt(-34.9257, 138.5997);
    t0 = performance.now();
    const graph = await walkGraph(path.join(B, 'raw/osm/walk.geojsonseq'), f);
    console.log('walk graph', graph.n, graph.edges, ((performance.now() - t0) / 1000).toFixed(1), 's');
    meta.pt = { day: DAY, arrive: '08:00 to 09:00', stat: 'median', walker: 'adult 5.1 km/h', walk_max_m: 1200, transfers: 3, cell_m: 150, feed_version: tt.feeds?.[0]?.version || null, walk_km: graph.km };
    for (const d of D) {
        t0 = performance.now();
        // up to 50 places at once (the engine's limit), spread along the list
        const pts = d.points.length <= 50 ? d.points : d.points.filter((_, i) => i % Math.ceil(d.points.length / 50) === 0);
        const run = RUN.runTransit(tt, { origins: pts.map((q) => q.ll), frame: f, from: '08:00', to: '09:00', step: 120, bands: [20, 40, 60, 90, 120], transfers: 3, walker: 'adult', walkMaxM: 1200, graph, targets: 'cells', cell: 150, direction: 'to', stat: 'median' });
        const g = run.grid;
        const mins = homes.map((h) => { const [x, y] = f.toXY(h.ll[0], h.ll[1]); const i = Math.floor((x - g.x0) / g.G), j = Math.floor((y - g.y0) / g.G); if (i < 0 || j < 0 || i >= g.nx || j >= g.ny) return null; const v = g.minutes[j * g.nx + i]; return v === 255 ? null : v; });
        times.runs[`pt_${d.id}`] = mins;
        if (d.id === 'cbd') fs.writeFileSync(path.join(OUT, 'pt-grid-cbd.json'), JSON.stringify({ ...g, minutes: Buffer.from(g.minutes).toString('base64') }));
        console.log('pt', d.id, pts.length, 'places', ((performance.now() - t0) / 1000).toFixed(1), 's');
    }
}
fs.writeFileSync(path.join(OUT, 'times.json'), JSON.stringify(times));
fs.writeFileSync(path.join(OUT, 'meta.json'), JSON.stringify(meta, null, 1));

// the walk graph of the transit-45-minutes showcase (its run.mjs): ways read as lines, only their ends and shared
// points become nodes
async function walkGraph(file, f) {
    const WALKABLE = new Set(['footway', 'path', 'pedestrian', 'living_street', 'residential', 'service', 'unclassified', 'tertiary', 'tertiary_link', 'secondary', 'secondary_link', 'primary', 'primary_link', 'steps', 'track', 'cycleway', 'corridor', 'road', 'bridleway']);
    const key = (x, y) => (Math.round(x * 2) + 2 ** 20) * 2 ** 21 + (Math.round(y * 2) + 2 ** 20);
    const lines = [];
    const rl = readline.createInterface({ input: fs.createReadStream(file), crlfDelay: Infinity });
    for await (let l of rl) {
        if (l.charCodeAt(0) === 0x1e) l = l.slice(1);
        if (!l) continue;
        const ft = JSON.parse(l), t = ft.properties || {};
        if (!WALKABLE.has(t.highway) || /^(no|private)$/.test(t.foot || '') || /^(no|private)$/.test(t.access || '') || t.area === 'yes') continue;
        const c = ft.geometry.coordinates, xy = new Float64Array(c.length * 2);
        for (let i = 0; i < c.length; i++) { const q = f.toXY(c[i][1], c[i][0]); xy[i * 2] = q[0]; xy[i * 2 + 1] = q[1]; }
        lines.push(xy);
    }
    const seen = new Map();
    for (const xy of lines) for (let i = 0; i < xy.length; i += 2) { const k = key(xy[i], xy[i + 1]); seen.set(k, (seen.get(k) || 0) + ((i === 0 || i === xy.length - 2) ? 2 : 1)); }
    const idx = new Map(), xs = [], ys = [], ea = [], eb = [], el = [];
    const node = (x, y, k) => { let n = idx.get(k); if (n == null) { n = xs.length; idx.set(k, n); xs.push(x); ys.push(y); } return n; };
    for (const xy of lines) {
        let a = node(xy[0], xy[1], key(xy[0], xy[1])), len = 0;
        for (let i = 2; i < xy.length; i += 2) {
            len += Math.hypot(xy[i] - xy[i - 2], xy[i + 1] - xy[i - 1]);
            const k = key(xy[i], xy[i + 1]);
            if (seen.get(k) >= 2 || i === xy.length - 2 || len > 120) { const b = node(xy[i], xy[i + 1], k); if (a !== b && len > 0) { ea.push(a); eb.push(b); el.push(len); } a = b; len = 0; }
        }
    }
    const n = xs.length, off = new Int32Array(n + 1);
    for (let i = 0; i < ea.length; i++) { off[ea[i] + 1]++; off[eb[i] + 1]++; }
    for (let i = 0; i < n; i++) off[i + 1] += off[i];
    const to = new Int32Array(off[n]), len = new Float32Array(off[n]), fill = off.slice(0, n);
    for (let i = 0; i < ea.length; i++) { to[fill[ea[i]]] = eb[i]; len[fill[ea[i]]++] = el[i]; to[fill[eb[i]]] = ea[i]; len[fill[eb[i]]++] = el[i]; }
    return { n, x: Float64Array.from(xs), y: Float64Array.from(ys), off, to, len, edges: ea.length, km: Math.round(el.reduce((t, v) => t + v, 0) / 1000) };
}
