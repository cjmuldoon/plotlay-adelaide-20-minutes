// Plotlay's own dark Ink base map, fetched by the real app (src/app/mapexport-ui.js mapBase) for exactly the views the
// hero, the compare and the small multiples draw over, with the app's projection checked at known points (so the
// build's own drawing of the roads lines up with the app's map to the pixel).
//   node scripts/bases.mjs <plotlay repo> [BASE=http://127.0.0.1:8743]   -> app/bases/<name>.jpg and app/bases/views.json
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
const [PL] = process.argv.slice(2), B = path.dirname(path.dirname(new URL(import.meta.url).pathname));
const { chromium } = createRequire(path.join(PL, 'package.json'))('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8743';
export const VIEWS = {
    square: { center: [-34.955, 138.655], zoom: 9.62, W: 540, H: 540 },
    wide: { center: [-34.955, 138.72], zoom: 9.62, W: 960, H: 540 },
    mini: { center: [-34.955, 138.655], zoom: 8.95, W: 270, H: 300 },
    city: { center: [-34.925, 138.60], zoom: 11.6, W: 540, H: 540 },
};
const b = await chromium.launch({ executablePath: process.env.PLOTLAY_CHROME || undefined });
const pg = await (await b.newContext({ viewport: { width: 1280, height: 800 }, serviceWorkers: 'block' })).newPage();
await pg.goto(`${BASE}/?nosw&studio=data&example=adelaide-20-minutes`, { waitUntil: 'domcontentloaded' });
await pg.waitForFunction(() => (window.mapOverlayApp?.store?.p?.dataLayers || []).length >= 12 && window.mapOverlayApp.ctx?.basemap, null, { timeout: 240000 });
await new Promise((r) => setTimeout(r, 4000));
const out = {};
for (const [name, v] of Object.entries(VIEWS)) {
    const r = await pg.evaluate(async ({ v, test }) => {
        const app = window.mapOverlayApp, M = await import('/src/app/mapexport-ui.js'), MC = await import('/src/core/mapchart.js');
        const view = { center: v.center, zoom: v.zoom }, base = await M.mapBase(app, view, v.W, v.H, 2, { muted: false });
        const P = MC.projector(view, v.W, v.H, false);
        return { href: base.href, credit: base.credit, basemap: app.ctx.basemap?.id || app.ctx.basemapKey, test: test.map((q) => [q, P(q)]) };
    }, { v, test: [[-34.92566, 138.5999], [-35.0287, 138.8095], [-34.6, 138.45]] });
    if (!r.href) throw new Error(`no base for ${name}`);
    fs.writeFileSync(path.join(B, 'app/bases', `${name}.jpg`), Buffer.from(r.href.split(',')[1], 'base64'));
    // the same without place names, so the build can draw the roads between the map and its names
    const nl = await pg.evaluate(async ({ v }) => {
        const app = window.mapOverlayApp, M = await import('/src/app/mapexport-ui.js'), s = app.store.p.settings, was = s.baseLabels;
        s.baseLabels = false; app.ctx.basemap?.setLabels?.(false);
        try { return (await M.mapBase(app, { center: v.center, zoom: v.zoom }, v.W, v.H, 2, { muted: false })).href; } finally { s.baseLabels = was; }
    }, { v });
    fs.writeFileSync(path.join(B, 'app/bases', `${name}-nolabels.jpg`), Buffer.from(nl.split(',')[1], 'base64'));
    out[name] = { ...v, scale: 2, credit: r.credit, basemap: r.basemap, test: r.test };
    console.log(name, r.basemap, r.test.map(([, p]) => p.map((x) => x.toFixed(1)).join(',')).join(' | '));
}
fs.writeFileSync(path.join(B, 'app/bases/views.json'), JSON.stringify(out, null, 1));
await b.close();
