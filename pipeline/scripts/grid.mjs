// Each of the eight places' catchment as filled land for the small multiples: driving minutes (little traffic and
// the morning rush hour) on a 250 m grid, each cell timed from the nearest road within 500 m (core/drivetime.js
// fromSources with the road rules, timeAt). Cells further than 500 m from a road stay empty.
//   node scripts/grid.mjs <plotlay repo>   -> out/grid.json { box, cell_m, nx, ny, free: {id: base64 Uint8}, am: {...} }
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { readOpl } from './opl.mjs';
import { destinations } from './destinations.mjs';
const [PL] = process.argv.slice(2), B = path.dirname(path.dirname(new URL(import.meta.url).pathname));
const T = await import(pathToFileURL(path.join(PL, 'src/core/drivetime.js')).href);
const net = T.networkFromElements(readOpl(path.join(B, 'raw/osm/roads.opl')), { rules: true, model: 'limits' });
const box = [-35.40, 138.40, -34.50, 139.02], cell = 250, MY = 111132, MX = 111320 * Math.cos(-34.95 * Math.PI / 180);
const ny = Math.ceil((box[2] - box[0]) * MY / cell), nx = Math.ceil((box[3] - box[1]) * MX / cell);
const out = { box, cell_m: cell, nx, ny, free: {}, am: {} };
for (const [rk, peak] of [['free', null], ['am', 'adelaide-tomtom-2025-am']]) for (const d of destinations(B)) {
    const run = T.fromSources(net, d.points.map((q, i) => ({ key: `${d.id}${i}`, ll: q.ll })), { rules: true, direction: 'to', peak, snap: 500 });
    const g = new Uint8Array(nx * ny).fill(255);
    for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
        const r = T.timeAt(run, [box[0] + (j + 0.5) * cell / MY, box[1] + (i + 0.5) * cell / MX]);
        if (r) g[j * nx + i] = Math.min(254, Math.round(r.minutes));
    }
    out[rk][d.id] = Buffer.from(g).toString('base64'); console.log(rk, d.id);
}
fs.writeFileSync(path.join(B, 'out/grid.json'), JSON.stringify(out));
