#!/usr/bin/env python3
"""<작품명> fan-made opening — edit description.

Copy this file into the project's work folder as project.py and fill it in.
Run:  python3 project.py edl      (timeline + checks)
      python3 project.py sheet    (two stills per shot -> work/sheets/timeline_NN.jpg — LOOK at them)
      python3 project.py all      (check, render 3 variants, add music, SRT, QA, cut list)
"""
import os, sys
sys.path.insert(0, "<ABSOLUTE PATH TO THIS SKILL>/scripts")
import opkit as ok

WORK = os.path.dirname(os.path.abspath(__file__))
ok.init(work=WORK, name="<작품명>_OP_v1", size=(1280, 720), fps=24, mood="<horror|action|warm>")   # 작품 장르에 맞춰 고른다
# ok.add_still('BG1', '/path/to/extra_still.jpg')

S = ok.S
A, B, C = ok.beats('A'), ok.beats('B'), ok.beats('C')   # one helper per section fitted in grid.json

# ---------------------------------------------------------------- shots
# S(start_time, source_key, clip_in_seconds, ...) — a shot lasts until the next one starts.
# Write start times as beat indices (A(0), A(4) ...) so every cut lands on the grid.

# intro: slow, sets the mood
S(0.00, 'C00', 0.0, z=(1.0, 1.07), grade='intro', fadein=22, vig=0.9)

# title: first big hit of the song
S(A(0), 'C01', 0.3, z=(1.0, 1.10), grade='title', flash=5, vig=0.8, nopulse=True)

# verse: 2-4 shots per lyric line, hard cuts with a small punch; a transition where the line changes
S(A(8), 'C02', 0.2, grade='verse', tr='whip_l')
S(A(12), 'C03', 0.5, grade='verse', punch=0.10)
S(A(16), 'C04', 1.0, speed=1.3, grade='versed', tr='zoom', shake=5)

# chorus: start each action clip so its peak lands on the downbeat; flash + punch + shake on the first hit
S(B(0), 'C05', 1.2, speed=1.3, grade='chorus', flash=5, punch=0.25, shake=12, chroma=3)
S(B(4), 'C06', 0.5, grade='chorus', punch=0.16, shake=6)

# outro
S(C(0), 'C07', 0.2, z=(1.0, 1.2), grade='outro', fadeblack=(ok.DUR - 4.0, 1.0))
S(ok.DUR - 3.0, 'black')

# ---------------------------------------------------------------- rhythm
ok.pulse(A(0), B(0), 'A', 0.015)      # verse: barely there
ok.pulse(B(0), C(0), 'B', 0.035)      # chorus: clearly felt

# ---------------------------------------------------------------- text
INK, PAPER = (214, 26, 32), (245, 243, 236)
PARTS = [('<강조어>', INK), ('<나머지 제목>', PAPER)]
ok.title_card(A(0), A(8), PARTS, sub="<E N G L I S H   S U B T I T L E>", credit="원작  <작가>  「<작품명>」  ·  <연재처>")
ok.end_card(ok.DUR - 3.0, PARTS, credit="FAN-MADE OPENING   ·   원작  <작가>  (<연재처>)", fade=(ok.DUR - 1.2, 0.9))

# word-by-word handwritten lines (rules, a spoken hook, a countdown) — times come from the lyric timestamps
# ok.typo(t0, t1, [[('<첫 단어>', 시각)], [('<단어>', 시각), ('<단어>', 시각)]], side='L', style='chalk')

ok.lyrics([
    # (start, end, "가사 한 줄"),   -> <name>.srt 로도 내보내진다
])

if __name__ == '__main__':
    ok.main(sections=[(0, '인트로'), (A(0), 'Verse'), (B(0), 'Chorus'), (C(0), '아웃트로')])
