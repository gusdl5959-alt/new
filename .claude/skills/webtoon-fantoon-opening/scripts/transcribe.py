#!/usr/bin/env python3
"""Lyric timestamps (word level) for a song, using faster-whisper if it is available locally.

  transcribe.py --work WORK [--lang ko] [--prompt "first lyric line ..."] [--model turbo]

Reads WORK/song16k.wav (made by analyze_song.py scan), writes WORK/lyrics_stt.json and prints each line.
Sung vocals are transcribed imperfectly: trust the TIMES, take the WORDS from the real lyric sheet.
If faster-whisper is not importable, the script says so; then either run it with a Python that has it
(extra site-packages can be passed with --path) or time the lyric lines by ear from the energy map.
"""
import argparse, json, os, sys

ap = argparse.ArgumentParser()
ap.add_argument("--work", required=True)
ap.add_argument("--lang", default="ko")
ap.add_argument("--prompt", default="")
ap.add_argument("--model", default="turbo")
ap.add_argument("--path", action="append", default=[], help="extra directory to import faster_whisper from")
args = ap.parse_args()
for p in args.path:
    sys.path.insert(0, p)
try:
    from faster_whisper import WhisperModel
    import soundfile as sf
except Exception as e:
    raise SystemExit(f"faster-whisper not available in this Python ({e}). See the docstring for options.")

try:
    model = WhisperModel(args.model, device="cpu", compute_type="int8", cpu_threads=8, local_files_only=True)
except Exception:
    raise SystemExit("The model is not cached locally. Downloading it needs the user's go-ahead; ask before removing local_files_only.")
samples, sr = sf.read(os.path.join(args.work, "song16k.wav"), dtype="float32")
segs, _ = model.transcribe(samples, language=args.lang, beam_size=5, word_timestamps=True, vad_filter=False,
                           condition_on_previous_text=False, initial_prompt=args.prompt or None)
data = []
for s in segs:
    data.append(dict(start=s.start, end=s.end, text=s.text,
                     words=[dict(s=w.start, e=w.end, t=w.word) for w in (s.words or [])]))
    print(f"{s.start:7.2f}-{s.end:7.2f} {s.text}")
    print("        " + " ".join(f"{w.word.strip()}@{w.start:.2f}" for w in (s.words or [])))
json.dump(data, open(os.path.join(args.work, "lyrics_stt.json"), "w"), ensure_ascii=False, indent=1)
