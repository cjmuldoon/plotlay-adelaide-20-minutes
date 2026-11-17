// The in-app example templates/adelaide-20-minutes: "Is everything in Adelaide 20 minutes away?" on Plotlay's dark
// Ink map. Made with Plotlay's own engine from the pipeline's inputs:
//   - the eight places, each its own layer (the GPO, the beaches, the airport, the emergency departments, the
//     university campuses, Adelaide Oval, the Hills, the shopping centres), so How far by car? can be run from any;
//   - by car to the GPO at the speed limit with no traffic, and in the morning rush hour (TomTom Traffic Index 2025 preset): 5-minute
//     bands to 60 with the road rules and speed limits (core/drivetime.js addDriveCatchments, rules, flow), in the
//     Flow look: the roads light up minute by minute when played;
//   - by public transport to the GPO, arriving 8 to 9 am (the pipeline's grid, core/transitrun.js bandsOf, flowOf);
//   - Greater Adelaide's 112 SA2 areas with their residents and the pipeline's answers (tables/sa2.csv: how many of
//     the eight are within 20 minutes, minutes to the city by car and public transport), coloured by the first.
// Saved views: Greater Adelaide, the city, the south, the Hills.
//   node make_example.mjs <plotlay repo> [build dir]
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { readOpl } from './scripts/opl.mjs';
import { destinations } from './scripts/destinations.mjs';
const [PL, B0] = process.argv.slice(2);
const B = path.resolve(B0 || path.dirname(new URL(import.meta.url).pathname));
const im = (f) => import(pathToFileURL(path.join(PL, f)).href);
const A = await im('src/core/agent.js'), D = await im('src/core/datalayers.js'), DT = await im('src/core/drivetime.js'), S = await im('src/core/datastyle.js');
const RUN = await im('src/core/transitrun.js'), R = await im('src/core/transitroute.js'), TR = await im('src/core/transit.js'), VW = await im('src/core/views.js');
const N = JSON.parse(fs.readFileSync(path.join(B, 'numbers.json'), 'utf8'));
const GPO = [-34.92566, 138.5999];
const p = A.newProject({ name: 'Is everything in Adelaide 20 minutes away?', lat: GPO[0], lng: GPO[1] });
p.basemap = 'ink';
const f = A.frameOf(p);
const OSM = D.OSM_ATTRIBUTION;
// the eight places
const DEST = destinations(B), ids = {};
const PREFIX = { cbd: 'G', beach: 'B', airport: 'A', hospital: 'E', uni: 'U', oval: 'O', hills: 'H', shops: 'S' };
const LAYER = { cbd: 'Adelaide GPO', beach: 'Beaches', airport: 'Adelaide Airport', hospital: 'Emergency departments', uni: 'University campuses', oval: 'Adelaide Oval', hills: 'The Hills', shops: 'Shopping centres' };
for (const d of DEST) {
    const dl = D.createDataLayer(p, { name: LAYER[d.id], prefix: PREFIX[d.id], digits: 3 });
    D.addField(p, { layer: dl.id, name: 'name', type: 'text' });
    D.addDataShapes(p, { layer: dl.id, order: 'as-is', shapes: d.points.map((q, i) => ({ point: f.toM(q.ll), key: `${PREFIX[d.id]}${String(i + 1).padStart(3, '0')}`, props: { name: q.name } })) });
    dl.attribution = ['beach', 'shops'].includes(d.id) ? OSM : null;
    dl.about = d.how;
    ids[d.id] = dl.id;
    dl.style = { ...(dl.style || {}), labels: 'none' };
}
// SA2 areas with the answers
const sa2 = JSON.parse(fs.readFileSync(path.join(B, 'raw/abs/sa2-adelaide.geojson'), 'utf8'));
const rows = fs.readFileSync(path.join(B, 'tables/sa2.csv'), 'utf8').trim().split('\n'); const head = rows.shift().split(',');
const byCode = new Map(rows.map((l) => { const v = l.split(','), o = {}; head.forEach((h, i) => { o[h] = v[i]; }); return [o.sa2_code, o]; }));
const ar = D.createDataLayer(p, { name: 'Areas (SA2)', prefix: 'A', digits: 3 });
const NUM = ['residents', 'half_or_more_pct', 'half_or_more_rush_pct', 'places_within_20_free', 'places_within_20_am', 'places_within_20_pt', 'share_all_eight_free', 'mean_min_city_free', 'mean_min_city_am', 'mean_min_city_pt'];
D.addField(p, { layer: ar.id, name: 'name', type: 'text' });
for (const k of NUM) D.addField(p, { layer: ar.id, name: k, type: 'number' });
const shapes = [];
for (const ft of sa2.features) {
    const o = byCode.get(String(ft.properties.code)); if (!o) continue;
    const polys = ft.geometry.type === 'Polygon' ? [ft.geometry.coordinates] : ft.geometry.coordinates;
    // (the headline: the share of residents with half the places or more, 4 of the 8, within 20 minutes, in per cent)
    const src = { ...o, half_or_more_pct: Math.round(1000 * o.share_half_free) / 10, half_or_more_rush_pct: Math.round(1000 * o.share_half_am) / 10 };
    const props = { name: ft.properties.name, ...Object.fromEntries(NUM.map((k) => [k, src[k] === '' ? null : +src[k]])) };
    for (const pl of polys) shapes.push({ ring: pl[0].slice(0, -1).map(([ln, la]) => f.toM([la, ln])), holes: pl.slice(1).map((h) => h.slice(0, -1).map(([ln, la]) => f.toM([la, ln]))), key: String(ft.properties.code), props });
}
D.addDataShapes(p, { layer: ar.id, order: 'as-is', shareKeys: true, shapes });
ar.attribution = 'Areas and residents: Australian Bureau of Statistics, ASGS 2021 and 2021 Census, CC BY 4.0';
// coloured by the share with half the places or more, split at 50% (the saying holds for most residents, or not)
S.setDataStyle(p, { layer: ar.id, by: 'field:half_or_more_pct', method: 'manual', breaks: [10, 25, 50, 75, 90, 100], palette: 'custom', custom: { type: 'seq', colours: ['#6f90f6', '#60a6f8', '#6ed0fa', '#ffdd85', '#ffb54e', '#ff7448'] } });
// by car from the GPO: the roads with their rules, at the speed limit and in the morning rush hour, in the Flow look
const els = readOpl(path.join(B, 'raw/osm/roads.opl'));
const net = DT.networkFromElements(els, { rules: true, model: 'limits' });
const BANDS = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60], box = [-35.36, 138.43, -34.49, 139.06];
const carLayers = {};
// the hero's colours: warm inside 20 minutes, cool past it (py/hero.py), one per 5-minute band
const HERO = ['#fff3cf', '#ffdd85', '#ffb54e', '#ff7448', '#6ed0fa', '#60a6f8', '#6f90f6', '#8080f5', '#9171ef', '#a06ee9', '#ac67e2', '#b464dc'];
for (const [tag, name, peak] of [['free', 'By car to the GPO: at the speed limit, no traffic', null], ['am', 'By car to the GPO: morning rush hour', 'adelaide-tomtom-2025-am']]) {
    const r = DT.addDriveCatchments(p, { layer: ids.cbd, net, rules: true, direction: 'to', peak, bands: BANDS, cell: 250, beyond: false, box, flow: { maxSegs: 30000 }, name });
    carLayers[tag] = r.id;
    const dl = D.findDataLayer(p, r.id);
    dl.about = peak ? `${r.road_rules.peak.source} ${r.road_rules.peak.note}` : 'At the speed limit, no traffic: each road at its speed limit, with a wait at each set of lights and at junctions. Rush-hour trips take longer.';
    S.setDataStyle(p, { layer: r.id, by: 'field:band', palette: 'custom', custom: { type: 'cat', colours: HERO } });
    console.log(name, r.areas.length, 'bands', r.flow?.segments, 'flow segments');
}
// by public transport to the GPO (the pipeline's grid)
{
    const r = JSON.parse(fs.readFileSync(path.join(B, 'out/pt-grid-cbd.json'), 'utf8'));
    const g = { ...r, minutes: new Uint8Array(Buffer.from(r.minutes, 'base64')) }, fr = R.frameAt(g.frame.lat0, g.frame.lng0);
    const ups = [20, 40, 60, 90, 120].filter((x) => x <= 60);
    const run = { bands: RUN.bandsOf(g, [20, 40, 60], fr), flow: RUN.flowOf(g, [20, 40, 60], fr), routes: [], grid: g, summary: { feeds: [{ name: 'Adelaide Metro', publisher: 'Adelaide Metro', licence: 'CC BY 4.0' }], timetable: { date: '2026-11-17' }, from: '08:00', to: '09:00', direction: 'to', stat: 'median', step_s: 120, transfers: 3, kmh: 5.1, walker: { name: 'Adult' }, walk: 'streets', walk_max_m: 1200 } };
    const res = TR.addTransitResult(p, run, { name: 'By public transport to the GPO: arriving 8 to 9 am', routes: false });
    D.findDataLayer(p, res.id).attribution = `Timetable: Adelaide Metro, CC BY 4.0; walking: ${OSM}`;
    S.setDataStyle(p, { layer: res.id, by: 'field:band', palette: 'custom', custom: { type: 'cat', colours: [HERO[3], HERO[6], HERO[10]] } });
    console.log('public transport bands', ups);
}
// the keys stay off the map (the places are named in their tables; the areas and bands by their colours)
for (const dl of p.dataLayers) dl.style = { ...(dl.style || {}), labels: 'none' };
// views
VW.addView(p, { name: 'Greater Adelaide', mode: 'plan', note: `Half the eight places or more within 20 minutes by car: ${Math.round(N.all.free.half_20 * 1000) / 10}% of residents at the speed limit with no traffic, ${Math.round(N.all.am.half_20 * 1000) / 10}% in the morning rush hour (TomTom Traffic Index 2025), ${Math.round(N.all.pt.half_20 * 1000) / 10}% by public transport. All eight: ${Math.round(N.all.free.within_20 * 1000) / 10}%, none and none.`, plan: { center: [-34.93, 138.64], zoom: 10 } });
VW.addView(p, { name: 'The city', mode: 'plan', note: `Within 20 minutes of the GPO by car: ${Math.round(N.destinations.cbd.runs.free.within_20 * 100)}% of residents at the speed limit with no traffic, ${Math.round(N.destinations.cbd.runs.am.within_20 * 100)}% in the morning rush hour (TomTom 2025), ${Math.round(N.destinations.cbd.runs.pt.within_20 * 1000) / 10}% by public transport.`, plan: { center: GPO, zoom: 12 } });
VW.addView(p, { name: 'The south coast', mode: 'plan', note: 'Beaches are close in the south; the city, the airport and the Hills are not.', plan: { center: [-35.12, 138.52], zoom: 11 } });
VW.addView(p, { name: 'The Hills', mode: 'plan', note: 'The Hills are within 20 minutes for the eastern suburbs and the Hills towns; the beach and the airport are not.', plan: { center: [-35.0, 138.75], zoom: 11 } });
// the bands at the speed limit shown first; the areas, the rush hour and public transport layers start hidden
for (const dl of p.dataLayers) if ([carLayers.am, ar.id].includes(dl.id) || /public transport/.test(dl.name)) { const L = p.layers.find((l) => l.id === dl.layerId); if (L) L.visible = false; }
const r5 = (c) => (typeof c[0] === 'number' ? [Math.round(c[0] * 1e5) / 1e5, Math.round(c[1] * 1e5) / 1e5] : c.map(r5));
for (const a of p.annotations) if (a.kind === 'data' && Array.isArray(a.coords)) a.coords = r5(a.coords);
p.view = { center: [-34.93, 138.64], zoom: 10 };
const OUT = process.env.OUT_DIR || path.join(PL, 'templates', 'adelaide-20-minutes'); fs.mkdirSync(OUT, { recursive: true });
fs.writeFileSync(path.join(OUT, 'project.json'), JSON.stringify({ format: 'map-overlay-project', version: 1, project: p, blobs: {} }));
fs.writeFileSync(path.join(B, 'app/engine-project.json'), JSON.stringify(p));
console.log(`project.json ${Math.round(fs.statSync(path.join(OUT, 'project.json')).size / 1e3)} KB, layers: ${p.dataLayers.map((d) => d.name).join(' | ')}`);
