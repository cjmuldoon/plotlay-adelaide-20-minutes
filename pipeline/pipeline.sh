#!/bin/bash
# Is everything in Adelaide 20 minutes away? The whole build, step by step. Each step can be run on its own:
#   ./pipeline.sh <step> [<plotlay repo>]     steps: extract run numbers grid example bases app frames cards encode page package all
# Inputs: the Geofabrik Australia PBF (osm-au-2026-11), Adelaide Metro's GTFS (raw/gtfs), ABS mesh blocks with residents
# (raw/abs, from transit-45-minutes-build) and SA2 areas (py/mb_sa2.py). Plotlay's engine is imported from the repo.
# Browser steps (bases, app) use Playwright's own Chrome for Testing against a local server of the repo on 127.0.0.1:8743
# (the example served from its build), each under a browser slot lock.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; PL="${2:-$PLOTLAY_REPO}"
CHROME="$HOME/Library/Caches/ms-playwright/chromium-1208/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
PAGE="$PL/site/showcase/adelaide-20-minutes"; NB="$OUTPUTS/pbi-kit/work/nbvenv/bin"
slot() { for s in 1 2; do L="$OUTPUTS/.browser.$s.lock"; if mkdir "$L" 2>/dev/null; then echo "adelaide-20 $(date)" > "$L/who"; trap 'rm -f "$L/who"; rmdir "$L"' EXIT; return; fi; done; echo "no browser slot free"; exit 1; }
step() {
  case "$1" in
    extract) "$HERE/scripts/osm_extract.sh" ;;
    sa2) "$NB/python" -I "$HERE/py/mb_sa2.py" "$HERE" ;;
    run) node --max-old-space-size=12288 "$HERE/scripts/run.mjs" "$PL" car pt ;;
    numbers) python3 -I "$HERE/py/numbers.py" "$HERE" ;;
    grid) node --max-old-space-size=8192 "$HERE/scripts/grid.mjs" "$PL" ;;
    example) node --max-old-space-size=8192 "$HERE/make_example.mjs" "$PL" "$HERE" ;;
    bases) slot; PLOTLAY_CHROME="$CHROME" node "$HERE/scripts/bases.mjs" "$PL" ;;
    app) slot; (cd "$PL" && PLOTLAY_CHROME="$CHROME" STEPS=maps,charts,app node scripts/datalayers/adelaide-20-minutes.mjs "$HERE") ;;
    frames) for r in free am pt; do python3 -I "$HERE/py/hero.py" "$HERE" frames $r square "$HERE/frames/hero_${r}_1x1"; done
            python3 -I "$HERE/py/hero.py" "$HERE" frames free wide "$HERE/frames/hero_free_16x9"
            python3 -I "$HERE/py/hero.py" "$HERE" compare "$HERE/frames/compare_16x9"; python3 -I "$HERE/py/hero.py" "$HERE" compare1 "$HERE/frames/compare_1x1" ;;
    cards) python3 -I "$HERE/py/hero.py" "$HERE" grid "$HERE/stills"; python3 -I "$HERE/py/hero.py" "$HERE" cards "$HERE/stills" ;;
    mbmap) python3 -I "$HERE/py/mbmap.py" "$HERE" "$OUTPUTS/transit-45-minutes-build/raw/abs/mb_4GADE" "$HERE/stills"
           python3 -c "import sys; from PIL import Image; [Image.open(f'{sys.argv[1]}/mbmap_{r}_{t}.png').convert('RGB').save(f'{sys.argv[2]}/mbmap_{r}_{t}.jpg', quality=86) for r in ('free', 'am') for t in ('16x9', '1x1')]" "$HERE/stills" "$PAGE/img" ;;
    encode) "$HERE/scripts/encode.sh" "$HERE" "$PAGE/img" ;;
    page) python3 -I "$HERE/py/page.py" "$HERE" "$PAGE" ;;
    package) python3 -I "$HERE/py/package.py" "$HERE" "$PAGE"; "$NB/python" -I "$HERE/py/gen_notebook.py" "$HERE/repo-src"
             (cd "$HERE/repo-src/python" && "$NB/python" -m nbconvert --to notebook --execute --inplace adelaide_20_minutes.ipynb) ;;
    all) for s in run numbers grid example bases app frames cards mbmap encode page package; do step $s; done ;;
    *) echo "unknown step $1"; exit 1 ;;
  esac
}
step "${1:-all}"
