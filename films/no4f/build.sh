#!/bin/sh
# Rebuild "4층은 없습니다" from scratch. Run from anywhere; LIB = the Lemo-Opuscar library (this folder lives in $LIB/films/no4f).
# No GPU: set PLAYWRIGHT_CHROME to a chrome-headless-shell; the render takes ~3–4 h on 4 CPU cores and resumes if interrupted.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
LIB=${LIB:-$(cd "$HERE/../.." && pwd)}; export LIB
[ -f "$LIB/core/render/video.mjs" ] || { echo "set LIB to the library folder"; exit 1; }
cd "$LIB"
python3 "$HERE/tools/fonts.py"                                         # 1. Korean fonts (OFL), subset to the film's characters
node core/render/events.mjs "$HERE"                                    # 2. page timeline → events.json (sound cues, light curve, captions)
"$LIB/.venv/bin/python" "$HERE/mix.py"                                 # 3. hum / foley / chime / breath / drone / silences → mix.wav
node "$HERE/tools/chunks.mjs" "$HERE" --chunk 240 --workers 2          # 4. picture, 14 400 frames in 60 resumable chunks
sh "$HERE/tools/join.sh"                                               # 5. join chunks → out/video.mp4
python3 -c "import json;E=json.load(open('$HERE/events.json'));json.dump([{'t0':e['t'],'t1':e['t1'],'text':e['text']} for e in E['ev'] if e['type']=='cap'],open('$HERE/out/cues.json','w'),ensure_ascii=False)"
"$LIB/.venv/bin/python" core/render/srt.py "$HERE/out/cues.json" "$HERE/no4f.srt"   # 6. subtitles
sh "$HERE/master.sh" "$HERE/out/video.mp4" "$HERE/mix.wav" "$HERE/out/master.mp4"   # 7. ≈ −14 LUFS, true-peak limited, mux
ffmpeg -y -loglevel error -i "$HERE/out/master.mp4" -c:v libx264 -preset medium -crf 25 -tune grain -pix_fmt yuv420p -c:a copy -movflags +faststart "$HERE/no4f.mp4"
ffmpeg -y -loglevel error -i "$HERE/no4f.mp4" -vf "crop=1440:1080:240:0,scale=960:720" -c:v libx264 -preset slow -b:v 1050k -maxrate 1600k -bufsize 3000k -tune grain -c:a aac -b:a 128k -movflags +faststart "$HERE/no4f_web.mp4"   # repo-sized 4:3 copy
ffmpeg -y -loglevel error -ss 441 -i "$HERE/out/video.mp4" -frames:v 1 -q:v 2 "$HERE/poster.jpg"   # 8. poster
