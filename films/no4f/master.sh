#!/bin/sh
# Master and mux: static gain to about −14 LUFS integrated + a true-peak limiter (keeps the film's dynamics: the silences stay silent,
# the hum stays quiet; core/render/mux.sh's dynamic loudnorm would lift the quiet passages). Usage: sh master.sh video.mp4 mix.wav out.mp4
set -e
V="$1"; A="$2"; O="$3"
I=$(ffmpeg -hide_banner -nostats -i "$A" -af ebur128 -f null - 2>&1 | awk '/Integrated loudness/{f=1} f&&/I:/{print $2; exit}')
G=$(awk -v i="$I" 'BEGIN{ printf "%.2f", -14 - i }')
echo "measured $I LUFS → gain $G dB"
ffmpeg -y -hide_banner -loglevel error -i "$V" -i "$A" -map 0:v -map 1:a -c:v copy \
  -af "volume=${G}dB,alimiter=limit=0.6:attack=2:release=60:level=disabled,aresample=48000" -c:a aac -b:a 256k -shortest -movflags +faststart "$O.tmp.mp4"
mv "$O.tmp.mp4" "$O"
ffmpeg -hide_banner -nostats -i "$O" -af ebur128=peak=true -f null - 2>&1 | awk '/Summary/{f=1} f' | grep -E "I:|LRA:|Peak:"
