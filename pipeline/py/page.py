"""The showcase page site/showcase/adelaide-20-minutes/index.html, every number from numbers.json.
   python3 -I py/page.py <build dir> <page dir>"""
import json, sys, os
from PIL import Image
B, PAGE = sys.argv[1:3]
N = json.load(open(f'{B}/numbers.json'))
D, A, NET, PT = N['destinations'], N['all'], N['network'], N['pt']
REPO = 'https://github.com/cjmuldoon/plotlay-adelaide-20-minutes'
pc = lambda x: f'{x * 100:.0f}%'
p1 = lambda x: f'{x * 100:.1f}%'
n0 = lambda x: f'{round(x):,}'
r = lambda d, run='free': D[d]['runs'][run]
def wh(n):
    f = os.path.join(PAGE, 'img', n)
    return Image.open(f).size if os.path.exists(f) else (1920, 1080)
def pic(n, alt, lazy=True):
    w, h = wh(n)
    lz = ' loading="lazy"' if lazy else ''
    img = f'<img src="img/{n}" width="{w}" height="{h}"{lz} alt="{alt}">'
    sq = n.replace('_16x9.', '_1x1.') if '_16x9.' in n else n.replace('.jpg', '-phone.jpg') if os.path.exists(os.path.join(PAGE, 'img', n.replace('.jpg', '-phone.jpg'))) else n
    if os.path.exists(os.path.join(PAGE, 'img', sq)): img = f'<picture><source media="(max-width: 699px)" srcset="img/{sq}" width="{wh(sq)[0]}" height="{wh(sq)[1]}">{img}</picture>'
    return img
def fig(n, alt, cap, lazy=True): return f'<figure>{pic(n, alt, lazy)}<figcaption>{cap}</figcaption></figure>'
def anim(name, alt, cap, wide=True):
    if wide:
        return (f'<figure class="sc-anim"><div class="sc-anim-box"><video src="img/{name}_16x9.mp4" data-square="img/{name}_1x1.mp4" data-square-poster="img/{name}_poster_1x1.jpg" poster="img/{name}_poster_16x9.jpg" muted loop playsinline preload="metadata" width="1920" height="1080" aria-label="{alt}"></video>'
                f'<button class="sc-anim-btn" type="button" aria-label="Play the animation">Play</button></div><figcaption>{cap}</figcaption></figure>')
    return (f'<figure class="sc-anim sc-anim-sq"><div class="sc-anim-box"><video src="img/{name}.mp4" data-square="img/{name}.mp4" data-square-poster="img/{name}_poster.jpg" poster="img/{name}_poster.jpg" muted loop playsinline preload="metadata" width="1080" height="1080" aria-label="{alt}"></video>'
            f'<button class="sc-anim-btn" type="button" aria-label="Play the animation">Play</button></div><figcaption>{cap}</figcaption></figure>')

ORDER = ['shops', 'hospital', 'uni', 'beach', 'oval', 'cbd', 'airport', 'hills']
TITLE = {'cbd': 'The city', 'beach': 'A beach', 'airport': 'The airport', 'hospital': 'An emergency department', 'uni': 'A university campus', 'oval': 'Adelaide Oval', 'hills': 'The Hills', 'shops': 'A shopping centre'}
dest = json.load(open(f'{B}/out/destinations.json'))
tiles = ''.join(f'<figure class="sc-tile"><picture><source media="(max-width: 699px)" srcset="img/mini_{d}.jpg" width="540" height="600"><img src="img/mini_{d}.jpg" width="540" height="600" loading="lazy" alt="Map of Greater Adelaide: the land within 20 minutes by car of {TITLE[d].lower()} in orange, the rest in blue, the places as white dots."></picture>'
                f'<figcaption><b>{TITLE[d]}</b><span class="sc-big">{pc(r(d)["within_20"])}</span><span>within 20 min at the speed limit</span><span class="sc-rush">Rush hour: {pc(r(d, "am")["within_20"])}</span></figcaption></figure>' for d in ORDER)
rows = ''.join(f'<tr><th scope="row">{TITLE[d]}</th><td>{p1(r(d)["within_20"])}</td><td>{r(d)["median_min"]:.0f}</td><td>{p1(r(d, "am")["within_20"])}</td><td>{p1(r(d, "pt")["within_20"])}</td></tr>' for d in ORDER)
rows += f'<tr class="sc-total"><th scope="row">All eight</th><td>{p1(A["free"]["within_20"])}</td><td>{A["free"]["median_min_for_all"]:.0f}</td><td>{p1(A["am"]["within_20"])}</td><td>{p1(A["pt"]["within_20"])}</td></tr>'
best = N['sa2']['best'][:5]; worst = N['sa2']['worst'][:6]
holds = ''.join(f'<li><b>{x["sa2_name"].replace(" - ", " and ")}</b>: {pc(x["share_all_eight_free"])} of {n0(x["residents"])} residents have all eight within 20 minutes.</li>' for x in best)
fails = ''.join(f'<li><b>{x["sa2_name"].replace(" - ", " and ")}</b>: {x["places_within_20_free"]:.1f} of the eight on average; {x["mean_min_city_free"]:.0f} minutes to the city.</li>' for x in worst)
hows = ''.join(f'<li><b>{TITLE[d]}</b>: {dest[d]["how"]}</li>' for d in ['cbd', 'beach', 'airport', 'hospital', 'uni', 'oval', 'hills', 'shops'])
cd = A['free']['count_dist']
desc = (f"For every Greater Adelaide resident, the drive to eight places: the city, a beach, the airport, an emergency department, a university, Adelaide Oval, the Hills and a shopping centre. "
        f"At the speed limit with no traffic, {p1(A['free']['within_20'])} have all eight within 20 minutes; in the morning rush hour, none do.")
page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Is everything in Adelaide 20 minutes away? - Plotlay</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://www.getplotlay.com/showcase/adelaide-20-minutes/">
<meta property="og:type" content="article">
<meta property="og:url" content="https://www.getplotlay.com/showcase/adelaide-20-minutes/">
<meta property="og:title" content="Is everything in Adelaide 20 minutes away?">
<meta property="og:description" content="{p1(A['free']['within_20'])} of Adelaideans have all eight places within a 20-minute drive with no traffic. In the rush hour, nobody does.">
<meta property="og:image" content="https://www.getplotlay.com/showcase/adelaide-20-minutes/img/hero_poster_16x9.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.png">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=Caveat:wght@600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">
<link rel="stylesheet" href="page.css">
</head>
<body>
<div class="frame" aria-hidden="true">
  <div class="ruler top"><span>A</span><span>B</span><span>C</span><span>D</span><span>E</span><span>F</span><span>G</span><span>H</span></div>
  <div class="ruler left"><span>1</span><span>2</span><span>3</span><span>4</span><span>5</span><span>6</span></div>
</div>

<div class="sheet">
<header class="masthead"><a class="mark" href="/"><img src="/favicon.png" alt="" width="30" height="30"><span>Plotlay</span></a>
<nav class="register"><a href="/design/"><i>01</i>Design</a><a href="/data/"><i>02</i>Data</a><a href="/features"><i>F</i>Features</a><a href="/#s6"><i>06</i>Fees</a><a href="/guides/"><i>G</i>Guides</a><a href="/learn/"><i>L</i>Learn</a><a href="/blog/"><i>B</i>Blog</a></nav>
<details class="mnav"><summary aria-label="Menu"><span class="mnav-ic" aria-hidden="true"></span><span class="mnav-t">Menu</span></summary><nav class="mnav-panel" aria-label="Site menu"><a href="/design/"><i>01</i>Design</a><a href="/data/"><i>02</i>Data</a><a href="/features"><i>F</i>Features</a><a href="/#s6"><i>06</i>Fees</a><a href="/guides/"><i>G</i>Guides</a><a href="/learn/"><i>L</i>Learn</a><a href="/blog/"><i>B</i>Blog</a><a href="/whats-new"><i>N</i>What&rsquo;s new</a><a href="/support"><i>S</i>Support</a><a class="mnav-app" href="https://app.plotlay.io">Open the app &rarr;</a></nav></details>
<a class="open" href="https://app.plotlay.io">Open the app &rarr;</a>
</header>
<main class="sc">
<nav class="sc-crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span aria-hidden="true">/</span><a href="/showcase/">Showcases</a><span aria-hidden="true">/</span><span aria-current="page">Adelaide in 20 minutes</span></nav>
<p class="sc-kicker">Showcase &middot; How far by car &middot; OpenStreetMap, TomTom and Adelaide Metro</p>
<h1>Is everything in Adelaide 20 minutes away?</h1>
<p class="sc-lede">Adelaideans say it about their city. We tested it for all {n0(N['residents'])} residents of Greater Adelaide and eight places: the city, a beach, the airport, an emergency department, a university, Adelaide Oval, the Hills and a shopping centre. <b>Driving at the speed limit with no traffic, {p1(A['free']['within_20'])} have all eight within 20 minutes. In the morning rush hour, at TomTom&rsquo;s measured slowdown, nobody does.</b> By public transport, nobody does either.</p>
{anim('hero', 'Animation: a dark map of Greater Adelaide. From the GPO the roads light up minute by minute, gold inside 20 minutes and blue after it, while a counter of residents reached climbs to 48% at 20 minutes, where the edge pulses, and to 99% at 45.', f'From the GPO, minute by minute, at the speed limit with no traffic. The counter is the share of Greater Adelaide&rsquo;s residents who can reach the GPO within that many minutes. At 20 minutes it is {p1(r("cbd")["within_20"])}.')}
<div class="sc-cta"><a class="sc-btn sc-btn-main" href="https://app.plotlay.io/?example=adelaide-20-minutes&amp;as=client">Open in Plotlay<span>Play the roads, compare car and public transport. No account needed.</span></a><a class="sc-btn" href="downloads/adelaide-20-minutes-data.zip" download>The data<span>Minutes per mesh block to each place, by area, and the method</span></a><a class="sc-btn repo-link" href="{REPO}">Data and notebook on GitHub<span>The plotlay-adelaide-20-minutes repository</span></a></div>

<div class="sc-stats">
<div><b>{p1(A['free']['within_20'])}</b><span>have all eight within 20 min at the speed limit, no traffic</span></div>
<div><b>0%</b><span>have all eight within 20 min in the morning rush hour (TomTom 2025 slowdown)</span></div>
<div><b>{pc(r('cbd')['within_20'])}</b><span>reach the city within 20 min at the speed limit; {pc(r('cbd', 'am')['within_20'])} in the rush hour (TomTom)</span></div>
<div><b>{p1(r('cbd', 'pt')['within_20'])}</b><span>reach the city within 20 min by public transport</span></div>
</div>

<h2>Read this first</h2>
<p><b>&ldquo;At the speed limit, no traffic&rdquo;</b> means every road driven at its posted limit, with a stated wait at each set of traffic lights and at junctions, and nothing else in the way: the best a trip can be. Real trips are slower. <b>The rush hour</b> applies the slowdown TomTom measured for Adelaide in 2025: trips at the morning peak took 58.5% longer than at free flow on ordinary roads and 24.6% longer on motorways (<a href="https://www.tomtom.com/traffic-index/adelaide-traffic/">TomTom Traffic Index 2025</a>). That is a city-wide average over the year, applied to every road of its kind. It is not a traffic forecast and it does not know which roads jam.</p>

<h2>Eight places, one at a time</h2>
<p>The saying holds for the everyday places. {p1(r('shops')['within_20'])} of residents live within 20 minutes of a shopping centre and {p1(r('hospital')['within_20'])} of a public emergency department, even at TomTom&rsquo;s rush-hour slowdown ({pc(r('shops', 'am')['within_20'])} and {pc(r('hospital', 'am')['within_20'])}). It breaks on the places Adelaide has only one of. Half the city is within 20 minutes of the GPO ({p1(r('cbd')['within_20'])}) or Adelaide Oval ({p1(r('oval')['within_20'])}), {p1(r('airport')['within_20'])} of the airport, and a quarter of the Hills ({p1(r('hills')['within_20'])}).</p>
<div class="sc-grid8">{tiles}</div>
<p class="sc-count">Each map: the land within 20 minutes by car at the speed limit in orange, further in blue, inside Greater Adelaide. Rush hour: at the TomTom Traffic Index 2025 slowdown. The share is of residents, counted by mesh block.</p>
{fig('chart_share_16x9.png', 'Bar chart of the share of residents within 20 minutes of each place by car at the speed limit, by car in the rush hour and by public transport: a shopping centre 99, 98 and 37 percent; an emergency department 94, 79 and 5; a university campus 92, 65 and 5; a beach 62, 41 and 7; Adelaide Oval 51, 24 and 1; the city 48, 22 and 2; the airport 40, 15 and 0; the Hills 25, 9 and 0; all eight 10, 0 and 0.', 'Made in Plotlay&rsquo;s Analysis page from the pipeline&rsquo;s numbers.')}
<div class="sc-scroll"><table class="sc-src-table sc-t5">
<caption>Share of residents within 20 minutes, and the median trip by car at the speed limit</caption>
<thead><tr><th>Place</th><th>Car, speed limit</th><th>Median, min</th><th>Car, rush hour</th><th>Public transport</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>

<h2>All eight</h2>
<p>To have everything within 20 minutes you have to live in the middle: the inner south and the city. At the speed limit, {p1(A['free']['within_20'])} of residents ({n0(A['free']['people_20'])}) have all eight; {p1(cd[7])} have seven of them, usually all but the Hills or the airport. Leave those two out and {p1(A['free']['six_no_hills_airport_20'])} have the other six. The typical resident needs {A['free']['median_min_for_all']:.0f} minutes to have all eight; at TomTom&rsquo;s morning rush-hour slowdown, {A['am']['median_min_for_all']:.0f} minutes.</p>
{fig('map_areas_16x9.jpg', 'Map of Greater Adelaide by area, coloured by how many of the eight places are within 20 minutes by car on average: seven or more in the inner south and the city, five to seven in the middle suburbs, one to three in the Hills, the far north and the far south.', 'Made in Plotlay: the areas map picture on the Ink base map, from the example.')}
<div class="sc-pair">
<div><h3>Where it holds</h3><ul class="sc-list">{holds}</ul></div>
<div><h3>Where it fails</h3><ul class="sc-list">{fails}</ul></div>
</div>
<p class="sc-count">ABS Statistical Areas Level 2 with 3,000 residents or more, at the speed limit with no traffic. In {N['sa2']['holds_free']} of {N['sa2']['count']} areas most residents have all eight.</p>

<h2>The rush hour</h2>
<p>The same trips at TomTom&rsquo;s morning-peak slowdown. The share within 20 minutes of the GPO falls from {p1(r('cbd')['within_20'])} to {p1(r('cbd', 'am')['within_20'])}, and the median trip to it rises from {r('cbd')['median_min']:.0f} to {r('cbd', 'am')['median_min']:.0f} minutes. Nobody has all eight within 20 minutes. The evening peak (62.7% longer on ordinary roads, 9.8% on motorways) gives almost the same answer: {p1(r('cbd', 'pm')['within_20'])} within 20 minutes of the GPO.</p>
<div class="sc-pair">
{fig('chart_minutes_free_16x9.png', 'Column chart of residents by minutes to the GPO at the speed limit: most between 10 and 30 minutes, the bars up to 20 minutes in blue and after it in orange.', 'At the speed limit, no traffic.')}
{fig('chart_minutes_am_16x9.png', 'Column chart of residents by minutes to the GPO in the morning rush hour: the bars spread out to 60 minutes, most of them past 20.', 'In the morning rush hour: TomTom Traffic Index 2025.')}
</div>
{anim('hero_am', 'Animation: the same map in the morning rush hour. The gold area inside 20 minutes is much smaller and the counter reaches 22% at 20 minutes.', f'The morning rush hour, minute by minute: {p1(r("cbd", "am")["within_20"])} reach the GPO within 20 minutes. Slowdown from the TomTom Traffic Index 2025.', wide=False)}

<h2>By public transport</h2>
<p>Adelaide Metro&rsquo;s timetable, arriving between 8 and 9 am on a weekday, the median trip, walking up to {PT['walk_max_m']:,} m to the first stop and at most {PT['transfers']} changes. {p1(r('cbd', 'pt')['within_20'])} of residents reach the GPO within 20 minutes and nobody has all eight. The closest to the saying is the shopping centre: {p1(r('shops', 'pt')['within_20'])} of residents are within 20 minutes of one. The median trip to the city is {r('cbd', 'pt')['median_min']:.0f} minutes, against {r('cbd')['median_min']:.0f} by car at the speed limit.</p>
{anim('compare', 'Animation: two maps side by side, by car on the left and by public transport on the right, growing from the GPO on the same clock with a counter each. At 20 minutes the car has reached 48% of residents and public transport 2%.', 'The car at the speed limit and public transport on the same clock, to the GPO. Public transport counts the walk at each end and the wait; the car counts none of the parking.')}

<h2 id="how">How it was made in Plotlay</h2>
<ol class="sc-steps">
<li><b>The roads</b>: OpenStreetMap&rsquo;s roads for Greater Adelaide ({NET['km']:,} km), read with <b>How far by car</b> and <b>Road rules</b> on: {NET['one_way_stretches']:,} one-way stretches, {NET['turn_bans']:,} turn bans, {NET['signal_nodes']:,} traffic-signal nodes in {NET['sets_of_lights']:,} sets of lights. Speeds are the speed limits.</li>
<li><b>The trips</b>: from every one of {n0(N['mesh_block_parts'])} mesh blocks with residents to the nearest of each kind of place, the quickest route by road. Once at the speed limit, once at TomTom&rsquo;s morning and evening slowdowns.</li>
<li><b>Public transport</b>: <b>How far by public transport</b> on Adelaide Metro&rsquo;s GTFS feed, arriving 8 to 9 am on Tuesday 17 November 2026.</li>
<li><b>Compare travel times</b> counts the residents within 20 minutes by each answer, by all and by any.</li>
<li>The bands to the GPO in the <b>Flow look</b>, which plays minute by minute; the charts on the <b>Analysis</b> page. The animations on this page draw the same Flow segments from Plotlay&rsquo;s engine over Plotlay&rsquo;s Ink base map, with the counter added.</li>
</ol>
<div class="sc-pair">
{fig('map_free_16x9.jpg', 'Plotlay map picture: the roads around Adelaide coloured by minutes to the GPO in 5-minute bands, gold to 20 minutes and blue to violet after, on the dark Ink map.', 'The map picture of the bands, exported from the example.')}
<figure>{pic('app-drive-card.jpg', 'Plotlay with the How far by car card open: Road rules ticked, Speeds, Which way and Traffic.')}<figcaption>How far by car with Road rules, Speeds and Traffic.</figcaption></figure>
</div>
<p><a class="sc-link" href="/showcase/transit-45-minutes/">45 minutes by public transport</a> &middot; <a class="sc-link" href="/showcase/adelaide-15-minutes/">Adelaide&rsquo;s 15-minute walk</a> &middot; <a class="sc-link" href="/showcase/south-road-closure/">The South Road closure</a> &middot; <a class="sc-link" href="https://app.plotlay.io/?start=data">Try it on your own places</a></p>

<h2>The eight places</h2>
<ul class="sc-caveats">{hows}</ul>

<h2>Python and Power BI</h2>
<p>A Jupyter notebook reads the minutes for each mesh block and gets the same shares, the all-eight count and the table by area. <code>mesh_block_minutes.csv</code> and <code>sa2.csv</code> open in Power BI Desktop with Get data, Text/CSV; each mesh block has its latitude and longitude for a map visual.</p>
<p><a class="sc-link" href="downloads/adelaide_20_minutes.ipynb" download>Download the notebook</a> and <a class="sc-link" href="downloads/adelaide-20-minutes-data.zip" download>the data</a>. Both are in the <a class="sc-link repo-link" href="{REPO}">plotlay-adelaide-20-minutes repository on GitHub</a>.</p>

<h2>Read it carefully</h2>
<ul class="sc-caveats">
<li><b>Not a traffic forecast.</b> The rush hour is TomTom&rsquo;s 2025 average slowdown for Adelaide, applied to every road of its kind. A real peak is worse on some roads and better on others.</li>
<li><b>Door to door, without parking.</b> Each trip starts at the middle of a mesh block and ends at the place&rsquo;s entrance or a point on it. Finding a park at the Oval or the airport is not counted; public transport counts the walk and the wait.</li>
<li><b>The waits are assumptions.</b> 12 seconds for each set of lights (Webster&rsquo;s average delay for a 100-second cycle at half green), and 4 to 10 seconds to give way at a junction by the turn made. Turn bans with a via way ({NET['turn_bans_left_out']['via_way']:,} in Adelaide) are left out.</li>
<li><b>Speed limits are as mapped.</b> Where OpenStreetMap has no limit, the Australian default applies: 50 km/h in built-up areas, 100 km/h outside them.</li>
<li><b>The nearest of each kind</b>, not the one people use. A family at the Women&rsquo;s and Children&rsquo;s, or a student at a campus across town, may drive further. With the Women&rsquo;s and Children&rsquo;s, Gawler and Mount Barker emergency departments counted, {p1(r('hospital9')['within_20'])} are within 20 minutes of one.</li>
<li><b>A different speed model.</b> With Plotlay&rsquo;s older typical speeds by kind of road (no lights, no turn bans), {p1(A['typical']['within_20'])} would have all eight. The road rules make the answer more cautious and, we think, closer to a real drive.</li>
<li>Residents from the 2021 Census by mesh block; OpenStreetMap as at 13 November 2026; Adelaide Metro feed version {PT['feed_version']}.</li>
</ul>

<section class="sc-credits">
<h2>Sources and licences</h2>
<p>Roads, speed limits, one-way streets, turn restrictions, traffic signals, beaches and shopping centres: &copy; OpenStreetMap contributors, <a href="https://www.openstreetmap.org/copyright">Open Database Licence</a> (Geofabrik extract of 13 November 2026). Rush-hour slowdown: <a href="https://www.tomtom.com/traffic-index/adelaide-traffic/">TomTom Traffic Index 2025, Adelaide</a>, read 18 November 2026. Timetable: Adelaide Metro GTFS, CC BY 4.0. Residents, mesh blocks and areas: Australian Bureau of Statistics, 2021 Census and ASGS Edition 3, CC BY 4.0. Base map on the maps and animations: Plotlay Ink, &copy; OpenStreetMap contributors, tiles Protomaps.</p>
<p>The minutes are made from OpenStreetMap, so the tables are shared under the Open Database Licence. Pictures, charts and animations are CC BY 4.0, crediting OpenStreetMap; the code is MIT: see the <a href="{REPO}">plotlay-adelaide-20-minutes repository on GitHub</a>. Independent work using open data, not endorsed by the South Australian Government, Adelaide Metro or TomTom.</p>
</section>

<div class="sc-signup"><h2>Time your own places</h2><p>Plotlay is free to start: every tool, three cloud projects.</p><a class="sc-btn sc-btn-main" href="https://app.plotlay.io">Create free account<span>Then open Data layers, Analyse, How far by car</span></a></div>
</main>
<footer class="titleblock"><div class="tb-cell tb-brand"><img src="/favicon.png" alt="" width="40" height="40"><div><b>Plotlay</b><span>drawings, maps &amp; site capture</span></div></div>
<div class="tb-cell"><i>Project</i>getplotlay.com</div><div class="tb-cell"><i>Guides</i><a href="/guides/">Worked examples</a><br><a href="/whats-new">What&rsquo;s new</a></div><div class="tb-cell"><i>Contact</i><a href="mailto:hello@plotlay.io">hello@plotlay.io</a></div>
<div class="tb-cell"><i>Also see</i><span class="tb-links"><a href="/blog/">Blog</a> <a href="/support">Support</a> <a href="/roadmap">Roadmap</a> <a href="/status">Status</a> <a href="/for/suppliers">For suppliers</a> <a href="/privacy">Privacy</a> <a href="/terms">Terms</a> <a href="/privacy#cookies">Cookies</a> <a href="/dpa">DPA</a></span></div><div class="tb-cell tb-rev"><i>Rev</i>A</div><div class="tb-cell tb-dwg"><i>Dwg no.</i>PL-SC33</div>
<div class="tb-cell tb-go"><a href="https://app.plotlay.io">Open Plotlay &rarr;</a></div></footer>
</div>
<script src="page.js"></script>
<script src="/nav.js" defer></script>
</body>
</html>
"""
assert '\u2014' not in page and '&mdash;' not in page
open(os.path.join(PAGE, 'index.html'), 'w').write(page)
print('page', len(page))
