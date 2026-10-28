#!/bin/sh
# Join the rendered chunks (out/chunks/c_*.mp4) losslessly into out/video.mp4; fails if any chunk is missing
set -e
D=$(cd "$(dirname "$0")/.." && pwd); C="$D/out/chunks"
N=$(ls "$C"/c_*.mp4 2>/dev/null | grep -v part | wc -l)
[ "$N" -eq 60 ] || { echo "join.sh: $N/60 chunks rendered; run tools/chunks.mjs again (it resumes)"; exit 1; }
ls "$C"/c_*.mp4 | grep -v part | sort | sed "s|^|file '|; s|$|'|" > "$C/list.txt"
ffmpeg -y -hide_banner -loglevel error -f concat -safe 0 -i "$C/list.txt" -c copy "$D/out/video.mp4"
echo "$D/out/video.mp4"
