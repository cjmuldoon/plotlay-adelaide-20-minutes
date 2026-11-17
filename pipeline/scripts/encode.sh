#!/bin/bash
# The videos from the frames (py/hero.py) and the cards: the page's loops and posters, and the cuts for LinkedIn
# (1:1, Big number opener) and YouTube or the site (16:9). H.264 High 4.1, 30 fps, yuv420p, limited range, faststart.
#   scripts/encode.sh <build dir> <page img dir>
set -e
B="$1"; IMG="$2"; V="$B/videos"; T="$B/work/enc"; mkdir -p "$V" "$T" "$IMG"
ENC=(-c:v libx264 -profile:v high -level:v 4.1 -pix_fmt yuv420p -color_range tv -r 30 -movflags +faststart -an)
seq_() { # frames dir, start, count, out, crf, [scale]
  nice -n 10 ffmpeg -y -loglevel error -framerate 30 -start_number "$2" -i "$1/%04d.png" -frames:v "$3" ${6:+-vf scale=$6:flags=lanczos} "${ENC[@]}" -crf "$5" -preset slow "$4"; }
card() { # png, seconds, out, crf, [scale]
  nice -n 10 ffmpeg -y -loglevel error -loop 1 -framerate 30 -i "$1" -t "$2" ${5:+-vf scale=$5:flags=lanczos} "${ENC[@]}" -crf "$4" -preset slow "$3"; }
cat_() { local out="$1"; shift; : > "$T/list.txt"; for f in "$@"; do echo "file '$f'" >> "$T/list.txt"; done; ffmpeg -y -loglevel error -f concat -safe 0 -i "$T/list.txt" -c copy -movflags +faststart "$out"; }
F="$B/frames"; N=$(ls "$F/hero_free_1x1" | grep -c png)
POSTER=228   # the 20-minute hold, the edge lit
# the page's loops (no cards: the page says it all) and posters
seq_ "$F/hero_free_16x9" 0 "$N" "$IMG/hero_16x9.mp4" 27
seq_ "$F/hero_free_1x1" 0 "$N" "$IMG/hero_1x1.mp4" 27 720:720
seq_ "$F/hero_am_1x1" 0 "$N" "$IMG/hero_am.mp4" 27 720:720
seq_ "$F/compare_16x9" 0 "$N" "$IMG/compare_16x9.mp4" 27
seq_ "$F/compare_1x1" 0 "$N" "$IMG/compare_1x1.mp4" 27 720:720
for x in "hero_free_16x9 hero_poster_16x9" "hero_free_1x1 hero_poster_1x1" "hero_am_1x1 hero_am_poster" "compare_16x9 compare_poster_16x9" "compare_1x1 compare_poster_1x1"; do set -- $x
  ffmpeg -y -loglevel error -i "$F/$1/$(printf %04d $POSTER).png" -q:v 3 "$IMG/$2.jpg"; done
# LinkedIn, 1:1 (trimmed 18 Nov to about 48 s): the roads growing at the speed limit to 60 minutes, the rush hour and
# car against public transport each from about 6 minutes to their 20-minute hold, the eight places in two pages of four (5 s each), the end card
card "$B/stills/open_1x1.png" 4.5 "$T/l1.mp4" 22
card "$B/stills/clean_free_1x1.png" 1.2 "$T/l0.mp4" 22
seq_ "$F/hero_free_1x1" 0 $((N - 30)) "$T/l2.mp4" 25   # to 60 minutes, no end hold
seq_ "$F/hero_am_1x1" 60 225 "$T/l3.mp4" 25   # from about 6 minutes to its 20-minute hold
seq_ "$F/compare_1x1" 60 225 "$T/l4.mp4" 25
card "$B/stills/grid4a_1x1.png" 5 "$T/l5.mp4" 22
card "$B/stills/grid4b_1x1.png" 5 "$T/l6.mp4" 22
card "$B/stills/end_1x1.png" 5 "$T/l7.mp4" 22
# the shared cut opens on the map at its 20-minute moment, for the 2.2 s opener (videos-2026-11/openers: the big number
# over this picture, then the roads grow from zero)
SH="$OUTPUTS/videos-2026-11/adelaide-20-minutes"; mkdir -p "$SH"
cat_ "$V/plotlay-adelaide-20-minutes-1x1.mp4" "$T"/l{0,2,3,4,5,6,7}.mp4
# 16:9: the big number, the roads growing (wide), car against public transport, the eight places, the end card
card "$B/stills/clean_free_16x9.png" 1.2 "$T/w1.mp4" 22
seq_ "$F/hero_free_16x9" 0 "$N" "$T/w2.mp4" 25
seq_ "$F/compare_16x9" 0 345 "$T/w3.mp4" 25
card "$B/stills/grid_16x9.png" 7 "$T/w4.mp4" 22
card "$B/stills/end_16x9.png" 8 "$T/w5.mp4" 22
cat_ "$V/plotlay-adelaide-20-minutes-16x9.mp4" "$T"/w{1,2,3,4,5}.mp4
# the hero alone, square, for a short post or a repost
cat_ "$V/adelaide-20-minutes-hero-1x1.mp4" "$T/l1.mp4" "$T/l2.mp4" "$T/l7.mp4"
for f in plotlay-adelaide-20-minutes-1x1 plotlay-adelaide-20-minutes-16x9; do /bin/cp -f "$V/$f.mp4" "$SH/$f.mp4"; unlink "$SH/$f.pre-opener.mp4" 2>/dev/null || true; done
ls -la "$V" "$IMG"/*.mp4 | awk '{print $5, $NF}'
