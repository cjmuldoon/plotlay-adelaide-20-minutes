// The eight places of "everything is 20 minutes away", each as the nearest of its kind (a list of points), and how
// each was chosen. Points are [lat, lng]; OpenStreetMap ones come from raw/osm/places.geojsonseq (the extract of
// 13 Nov 2026, ODbL), the rest are named places placed by hand at their main entrance or centre.
import fs from 'node:fs';
import path from 'node:path';

const RAD = Math.PI / 180;
function readPlaces(B) {
    const out = [];
    for (let l of fs.readFileSync(path.join(B, 'raw/osm/places.geojsonseq'), 'utf8').split('\n')) {
        l = l.replace(/^\x1e/, ''); if (!l.trim()) continue;
        const f = JSON.parse(l); if (!/Polygon/.test(f.geometry.type)) continue;
        const polys = f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates;
        let area = 0, cx = 0, cy = 0; const rings = [];
        for (const pl of polys) {
            const r = pl[0], lat0 = r[0][1], mx = 111320 * Math.cos(lat0 * RAD), my = 111132; rings.push(r);
            let a = 0, x = 0, y = 0;
            for (let i = 0; i + 1 < r.length; i++) { const x0 = (r[i][0] - r[0][0]) * mx, y0 = (r[i][1] - lat0) * my, x1 = (r[i + 1][0] - r[0][0]) * mx, y1 = (r[i + 1][1] - lat0) * my, k = x0 * y1 - x1 * y0; a += k; x += (x0 + x1) * k; y += (y0 + y1) * k; }
            if (Math.abs(a) > 1) { const A = Math.abs(a) / 2; area += A; cx += (r[0][0] + x / (3 * a) / mx) * A; cy += (lat0 + y / (3 * a) / my) * A; }
        }
        if (!area) continue;
        out.push({ props: f.properties, area_ha: area / 1e4, ll: [cy / area, cx / area], rings });
    }
    return out;
}
// points every `step` metres round a ring ([lng, lat]), for a long beach
function along(ring, step) {
    const pts = []; let acc = step;
    for (let i = 0; i + 1 < ring.length; i++) {
        const [x0, y0] = ring[i], [x1, y1] = ring[i + 1], mx = 111320 * Math.cos(y0 * RAD), L = Math.hypot((x1 - x0) * mx, (y1 - y0) * 111132);
        while (acc <= L) { const t = acc / L; pts.push([y0 + (y1 - y0) * t, x0 + (x1 - x0) * t]); acc += step; }
        acc -= L;
    }
    return pts;
}

export function destinations(B) {
    const P = readPlaces(B);
    const beaches = P.filter((p) => p.props.natural === 'beach' && p.area_ha >= 1);
    const beachPts = beaches.flatMap((b) => { const a = along(b.rings[0], 500); return (a.length ? a : [b.ll]).map((ll) => ({ name: b.props.name || 'Beach', ll })); });
    const malls = P.filter((p) => p.props.shop === 'mall' && p.props.name && !/homemaker/i.test(p.props.name));
    return [
        { id: 'cbd', name: 'The city (GPO)', short: 'The city', how: 'Adelaide GPO, 141 King William Street.', points: [{ name: 'Adelaide GPO', ll: [-34.92566, 138.59990] }] },
        { id: 'beach', name: 'The nearest beach', short: 'A beach', how: `OpenStreetMap sand beaches (natural=beach) of 1 ha or more: ${beaches.length} on the Gulf St Vincent coast from North Haven to Sellicks Beach, each a point every 500 m along its outline (${beachPts.length} points).`, points: beachPts },
        { id: 'airport', name: 'Adelaide Airport', short: 'The airport', how: 'The domestic and international terminal (OpenStreetMap way 26586784).', points: [{ name: 'Adelaide Airport terminal', ll: [-34.9386, 138.5379] }] },
        { id: 'hospital', name: 'The nearest public emergency department', short: 'An emergency department', how: 'The six adult emergency departments of Adelaide’s metropolitan public hospitals: Royal Adelaide, Flinders Medical Centre, The Queen Elizabeth, Lyell McEwin, Modbury and Noarlunga. The Women’s and Children’s Hospital (children, and women in pregnancy) and the country hospitals at Gawler and Mount Barker are left out, and counted in a sensitivity.',
            points: [['Royal Adelaide Hospital', -34.9208, 138.5867], ['Flinders Medical Centre', -35.0214, 138.5695], ['The Queen Elizabeth Hospital', -34.8845, 138.5335], ['Lyell McEwin Hospital', -34.7475, 138.6650], ['Modbury Hospital', -34.8341, 138.6899], ['Noarlunga Hospital', -35.1397, 138.5007]].map(([name, a, b]) => ({ name, ll: [a, b] })) },
        { id: 'uni', name: 'The nearest university campus', short: 'A university campus', how: 'The teaching campuses of Adelaide University (North Terrace, City West, City East, Magill, Mawson Lakes, Waite, Roseworthy) and Flinders University (Bedford Park, Tonsley, the city campus in Festival Tower).',
            points: [['Adelaide University, North Terrace', -34.9184, 138.6044], ['Adelaide University, City West', -34.9230, 138.5912], ['Adelaide University, City East', -34.9198, 138.6064], ['Adelaide University, Magill', -34.9103, 138.6740], ['Adelaide University, Mawson Lakes', -34.8100, 138.6203], ['Adelaide University, Waite', -34.9686, 138.6360], ['Adelaide University, Roseworthy', -34.5280, 138.6818], ['Flinders University, Bedford Park', -35.0249, 138.5725], ['Flinders University, Tonsley', -35.0080, 138.5720], ['Flinders University, city campus', -34.9205, 138.5980]].map(([name, a, b]) => ({ name, ll: [a, b] })) },
        { id: 'oval', name: 'Adelaide Oval', short: 'Adelaide Oval', how: 'Adelaide Oval, its southern gate by the Riverbank Footbridge.', points: [{ name: 'Adelaide Oval, southern gate', ll: [-34.9180, 138.5962] }] },
        { id: 'hills', name: 'The Hills (Hahndorf or Mount Lofty)', short: 'The Hills', how: 'Hahndorf’s Main Street or Mount Lofty Summit, whichever is nearer.', points: [{ name: 'Hahndorf, Main Street', ll: [-35.0287, 138.8095] }, { name: 'Mount Lofty Summit', ll: [-34.9767, 138.7087] }] },
        { id: 'shops', name: 'The nearest shopping centre', short: 'A shopping centre', how: `Every named shopping centre in OpenStreetMap (shop=mall), large or small, homemaker centres left out: ${malls.length}.`, points: malls.map((m) => ({ name: m.props.name, ll: m.ll })) },
    ];
}
export const EXTRA_EDS = [['Women’s and Children’s Hospital', -34.9115, 138.6000], ['Gawler Health Service', -34.5938, 138.7554], ['Mount Barker Hospital', -35.0812, 138.8700]];
