#!/usr/bin/env python3
"""Worked example: 「44교시 생존수업」 fan-made opening (horror, ~190 bpm, 117.6 s, 97 shots).

READ THIS FOR SYNTAX AND PACING ONLY. Every character, monster, rule card, lyric and motif below belongs to
that one webtoon. Do not carry any of it (names, the black circle, the class roll, the chant) into another
work — a new project starts from its own canon sheet.

It shows how a finished edit reads: every shot time is a beat index, lyric lines get 2-4 shots each, line
boundaries carry the transitions, and no clip is used twice as a full shot.
Runs only where that project's work folder exists:  OP_WORK=/path/to/work OP_STILLS=/path/to/stills python3 op44_project.py edl
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'scripts'))
import opkit as ok

ok.init(work=os.environ['OP_WORK'], name='44교시_OP_v2',
        out=os.environ.get('OP_OUT'), size=(1280, 720), fps=24, mood='horror')
STILLS = os.environ.get('OP_STILLS', '.')
ok.add_still('X06', os.path.join(STILLS, 'OP34_EMPTY_CLASSROOM_v01_20261007183301.jpg'))
ok.add_still('RUN', os.path.join(STILLS, 'SH03_Doyoon_Classroom_v01_20261007165525.jpg'))

S = ok.S
A, B, C, D, E, F = (ok.beats(k) for k in 'ABCDEF')   # one beat grid per song section
PER_A = ok.GRID['A']['per']
DUR = ok.DUR

# ===== INTRO (music box, distant bell)
S(0.00, 'C05', 0.0, z=(1.0, 1.07), grade='intro', fadein=22, vig=0.9)
S(2.04, 'X06', z=(1.02, 1.10), c=(0.52, 0.5), c1=(0.58, 0.47), grade='intro', vig=0.9)
S(3.92, 'N16', 0.0, speed=0.7, z=(1.06, 1.16), c=(0.5, 0.42), grade='intro', vig=1.0, tr='glitch')
# ===== CHILDREN CHANT (rule cards)
S(4.67, 'C12', 0.3, z=(1.16, 1.24), c=(0.40, 0.45), grade='chant', vig=1.0, sub=('C41', 1.5, 2))
S(7.90, 'N19', 0.1, z=(1.20, 1.28), c=(0.62, 0.46), grade='chant', vig=1.0, sub=('C49', 3.2, 2))
S(10.26, 'C46', 0.8, z=(1.18, 1.27), c=(0.40, 0.42), grade='chant', vig=1.0, sub=('C47', 0.3, 2))
S(13.00, 'N20', 0.0, z=(1.20, 1.30), c=(0.62, 0.46), grade='chant', vig=1.0, glitch_tail=0.42)
# ===== TITLE (band slams in)
S(A(0), 'C04', 0.3, z=(1.0, 1.10), grade='title', flash=5, vig=0.8, nopulse=True)
# cast roll: four groups, one face per beat
S(A(8), 'quad', kind='quad', step=PER_A, grade='cast', vig=0.3, tr='whip_l', tiles=[('C10', 0.2), ('N03', 0.0), ('C11', 0.3), ('C13', 0.3)])
S(A(12), 'quad', kind='quad', step=PER_A, grade='cast', vig=0.3, tr='whip_r', tiles=[('C30', 0.3), ('C14', 0.3), ('C16', 0.3), ('C17', 0.3)])
S(A(16), 'quad', kind='quad', step=PER_A, grade='cast', vig=0.3, tr='whip_l', tiles=[('C19', 0.3), ('C20', 0.3), ('C21', 0.3), ('C22', 0.3)])
S(A(20), 'quad', kind='quad', step=PER_A, grade='cast', vig=0.3, tr='whip_r', tiles=[('C23', 0.3), ('C24', 0.3), ('C25', 0.3), ('C26', 0.3)],
  dimtail=0.30)
# stop-time hits: what is waiting inside
S(A(25), 'C41', 1.2, kind='hit', look='neg', z=(1.10, 1.16), c=(0.5, 0.5), punch=0.18, shake=8, vig=0.0)
S(A(26), 'C47', 0.2, kind='hit', look='bw', z=(1.10, 1.16), c=(0.40, 0.45), punch=0.18, shake=8, vig=0.6)
S(A(27), 'N31', 1.5, kind='hit', look='neg', z=(1.10, 1.16), c=(0.5, 0.5), punch=0.18, shake=8, vig=0.0)
S(A(28), 'C55', 1.0, kind='hit', look='bw', z=(1.12, 1.18), c=(0.42, 0.42), punch=0.18, shake=8, vig=0.6)
S(A(29), 'C66', 1.0, kind='hit', look='neg', z=(1.10, 1.16), c=(0.5, 0.42), punch=0.18, shake=8, vig=0.0)
# ===== VERSE
S(A(30), 'C09', 0.2, z=(1.0, 1.06), c=(0.44, 0.60), grade='verse', vig=0.4, flash=3,
  stepz=[(A(34), 1.28), (A(36), 1.30)])
S(A(38), 'C06', 4.75, speed=-1.15, z=(1.03, 1.09), c=(0.45, 0.5), grade='verse', tr='whip_u')
S(A(42), 'C07', 1.6, speed=1.3, z=(1.05, 1.14), c=(0.45, 0.5), grade='versed', punch=0.10,
  stepz=[(A(44), 1.22)])
S(A(46), 'C01', 0.4, z=(1.30, 1.02), ease='out', grade='versed', tr='zoom', shake=5)
S(A(50), 'C77', 0.4, z=(1.03, 1.12), grade='versed', punch=0.10)
S(A(54), 'C02', 1.3, z=(1.04, 1.12), c=(0.42, 0.42), grade='versed', tr='whip_l')
S(A(58), 'C79', 1.0, z=(1.03, 1.10), grade='versed', punch=0.10, stepz=[(A(60), 1.25)])
S(A(62), 'RUN', z=(1.45, 1.45), c=(0.30, 0.56), c1=(0.66, 0.56), grade='verse', tr='whip_r', shake=5, hblur=10)
S(A(64), 'N21', 0.3, speed=1.4, z=(1.04, 1.10), c=(0.5, 0.45), grade='verse', punch=0.10)
S(A(66), 'N02', 0.2, speed=1.5, z=(1.05, 1.12), c=(0.5, 0.42), grade='verse', punch=0.10)
S(A(68), 'N10', 0.9, speed=1.5, z=(1.05, 1.12), c=(0.5, 0.5), grade='verse', punch=0.10)
S(A(70), 'N18', 0.3, speed=1.3, z=(1.03, 1.12), c=(0.5, 0.5), grade='versed', tr='glitch', chroma=3)
S(A(74), 'C37', 0.3, z=(1.04, 1.16), c=(0.42, 0.5), grade='versed', punch=0.12)
S(A(78), 'C49', 1.2, speed=1.1, z=(1.0, 1.10), c=(0.55, 0.5), grade='versed', tr='zoom', shake=6)
S(A(82), 'N05', 0.1, speed=1.2, z=(1.03, 1.10), c=(0.5, 0.5), grade='versed', punch=0.10)
S(A(86), 'C38', 0.3, z=(1.0, 1.22), c=(0.5, 0.48), grade='versed', vig=0.9, tr='black')
S(A(88), 'N23', 0.5, speed=1.3, z=(1.0, 3.0), c=(0.5, 0.5), c1=(0.46, 0.50), ease='in', grade='versed', vig=0.8,
  fadeout=3, shake=10, flash=2, chroma=4)
# ===== PRE-CHORUS
S(B(0), 'N12', 0.5, speed=1.2, z=(1.02, 1.08), c=(0.5, 0.5), grade='pre', vig=0.8, flash=2)
S(B(4), 'C50', 0.5, z=(1.04, 1.18), c=(0.5, 0.5), grade='pre', vig=0.85, punch=0.10)
S(B(8), 'C36', 0.5, z=(1.10, 1.03), grade='pre', tr='whip_d')
S(B(12), 'C29', 0.5, z=(1.03, 1.10), c=(0.5, 0.45), grade='pre', punch=0.08, stepz=[(B(14), 1.18)])
S(B(16), 'C33', 1.0, z=(1.03, 1.11), c=(0.5, 0.45), grade='pre', tr='whip_l')
S(B(20), 'C35', 0.2, z=(1.03, 1.12), c=(0.5, 0.45), grade='pre', punch=0.10, stepz=[(B(22), 1.18)])
S(B(24), 'N32', 0.4, speed=1.3, z=(1.03, 1.10), c=(0.42, 0.5), grade='pre', tr='whip_r')
S(B(27), 'N01', 0.2, speed=1.4, z=(1.03, 1.08), c=(0.5, 0.5), grade='pre', punch=0.10)
S(B(30), 'N00', 0.2, speed=1.6, z=(1.03, 1.08), c=(0.5, 0.45), grade='pre', punch=0.12, shake=5)
# build: reactions accelerate
for i, (k, ti, cx, cy) in enumerate([('N03', 1.5, 0.5, 0.45), ('N07', 0.5, 0.45, 0.42), ('N11', 0.6, 0.45, 0.5),
                                     ('N09', 1.3, 0.5, 0.45), ('N08', 1.2, 0.6, 0.42)]):
    S(B(32 + i), k, ti, z=(1.10 + i * 0.05, 1.16 + i * 0.05), c=(cx, cy), grade='chorus', flash=2, chroma=2 + i,
      shake=3 + i)
S(B(37), 'C10', 2.7, z=(1.25, 1.50), c=(0.60, 0.42), grade='chorus', flash=2, vig=0.9, fadeout=2)
# ===== CHORUS 1
S(C(0), 'N14', 1.3, speed=1.3, z=(1.0, 1.06), c=(0.5, 0.45), grade='chorus', flash=5, punch=0.25, shake=12, chroma=3)
S(C(4), 'C55', 0.5, z=(1.04, 1.16), c=(0.42, 0.42), grade='chorus', punch=0.16, shake=6, flash=2)
S(C(6), 'C76', 2.6, z=(1.02, 1.12), c=(0.5, 0.5), grade='chorus', tr='whip_u')
S(C(10), 'N35', 0.6, speed=2.0, z=(1.0, 1.08), c=(0.5, 0.5), grade='chorus', tr='zoom', shake=6)
S(C(14), 'N31', 0.9, speed=1.4, z=(1.05, 1.13), c=(0.5, 0.5), grade='chorus', punch=0.14, flash=2)
S(C(16), 'N06', 0.2, speed=1.6, z=(1.03, 1.12), c=(0.5, 0.55), grade='chorus', punch=0.14, shake=6)
S(C(18), 'N29', 0.8, speed=1.5, z=(1.03, 1.14), c=(0.5, 0.5), grade='chorus', punch=0.14)
S(C(20), 'N36', 0.0, speed=1.9, z=(1.03, 1.08), c=(0.5, 0.5), grade='chorus', tr='whip_r', shake=6)
S(C(22), 'N30', 0.1, speed=1.6, z=(1.04, 1.12), c=(0.45, 0.5), grade='chorus', punch=0.14)
S(C(24), 'N38', 0.0, speed=1.6, z=(1.02, 1.08), c=(0.5, 0.5), grade='chorus', tr='whip_l', shake=5)
S(C(28), 'N04', 0.7, speed=1.2, z=(1.05, 1.14), c=(0.5, 0.42), grade='chorus', punch=0.12)
S(C(32), 'N27', 0.5, speed=1.5, z=(1.02, 1.12), c=(0.5, 0.45), grade='chorus', flash=4, punch=0.22, shake=10, chroma=3)
S(C(36), 'N33', 1.5, speed=1.5, z=(1.05, 1.14), c=(0.55, 0.5), grade='chorus', punch=0.14, shake=5)
S(C(38), 'C01', 3.0, z=(1.04, 1.16), c=(0.5, 0.45), grade='chorus', tr='whip_d', dup_ok=True)
S(C(42), 'C34', 0.3, z=(1.03, 1.10), grade='chorus', punch=0.10)
S(C(46), 'N13', 0.5, speed=1.2, z=(1.03, 1.10), c=(0.5, 0.5), grade='chorus', tr='whip_l')
S(C(50), 'C31', 0.8, z=(1.10, 1.03), c=(0.5, 0.45), grade='chorus', punch=0.12)
S(C(53), 'C32', 1.0, z=(1.10, 1.03), c=(0.5, 0.45), grade='chorus', punch=0.12)
S(C(56), 'grid', kind='grid_fill', step=ok.GRID['C']['per'] / 2, grade='chorus', vig=0.3, flash=2)
S(78.21, 'black', kind='black')
# ===== BREAKDOWN (twisted chant)
S(78.30, 'C64', 0.5, speed=0.9, z=(1.02, 1.10), c=(0.55, 0.55), grade='break', vig=1.1, flicker=1)
S(D(4), 'N26', 1.5, z=(1.04, 1.14), c=(0.5, 0.55), grade='break', vig=1.1, flicker=1)
S(80.52, 'C78', 0.4, speed=0.6, z=(1.20, 1.30), c=(0.38, 0.42), grade='break', vig=1.1, flicker=1, sub=('N23', 2.2, 2))
S(83.68, 'N24', 1.7, speed=0.9, z=(1.12, 1.24), c=(0.33, 0.5), grade='break', vig=1.1, flicker=1, sub=('N25', 2.2, 2))
S(86.20, 'C47', 4.9, speed=-1.1, z=(1.06, 1.16), c=(0.60, 0.45), grade='break', vig=1.1, flicker=1, sub=('C66', 1.0, 2))
S(88.73, 'N28', 1.6, z=(1.14, 1.26), c=(0.38, 0.45), grade='break', vig=1.1, flicker=1)
S(90.94, 'C39', 0.3, z=(1.2, 2.4), c=(0.5, 0.55), ease='in', grade='final', vig=0.5, strobe=2)
# ===== FINAL CHORUS
S(E(0) - 0.012, 'N25', 0.1, speed=1.5, z=(1.0, 1.08), c=(0.5, 0.45), grade='final', flash=6, punch=0.35, shake=18,
  chroma=5, redflash=1)
S(E(4), 'N22', 0.3, speed=1.4, z=(1.03, 1.12), c=(0.5, 0.5), grade='final', punch=0.16, shake=8, chroma=3, flash=2)
S(E(7), 'C63', 0.3, z=(1.05, 1.14), grade='final', punch=0.14, shake=6, chroma=3, tr='whip_l')
S(E(9), 'N34', 1.5, speed=1.4, z=(1.06, 1.16), c=(0.55, 0.5), grade='final', punch=0.14, shake=6, chroma=3)
S(E(11), 'C61', 0.5, z=(1.05, 1.14), c=(0.6, 0.42), grade='final', punch=0.14, shake=6, chroma=3, flash=2)
S(E(13), 'C69', 0.5, z=(1.04, 1.16), c=(0.55, 0.42), grade='final', punch=0.14, shake=6, chroma=3)
S(E(15), 'grid', kind='grid_erase', grade='final', vig=0.5, shake=4, chroma=3, flash=2)
S(E(22), 'N15', 0.2, speed=1.1, z=(1.02, 1.10), c=(0.5, 0.5), grade='final',
  desat=(99.2, 0.6, 0.30), snap=(100.30, 0.30, (0.62, 0.45), 0.40))
S(F(0), 'C66', 0.5, z=(1.04, 1.14), c=(0.5, 0.42), grade='final', flash=5, punch=0.30, shake=16, chroma=5, redflash=1)
S(F(2), 'C68', 1.0, z=(1.04, 1.14), c=(0.5, 0.45), grade='final', punch=0.16, shake=10, chroma=4)
S(F(4), 'C59', 0.5, z=(1.04, 1.14), grade='final', punch=0.16, shake=10, chroma=4, flash=2)
S(F(6), 'C75', 0.5, z=(1.03, 1.12), c=(0.4, 0.42), grade='final', punch=0.10, shake=4, chroma=2, tr='whip_d')
S(F(10), 'C71', 1.0, speed=1.4, z=(1.04, 1.12), grade='final', punch=0.12, shake=5, chroma=2)
S(F(12), 'C72', 0.3, speed=1.2, z=(1.10, 1.02), c=(0.42, 0.45), grade='final', punch=0.12, shake=5, chroma=2)
S(F(15), 'C58', 0.5, z=(1.05, 1.18), c=(0.5, 0.5), grade='final', flash=3, punch=0.24, shake=10, chroma=4,
  sub=('N23', 2.4, 3))
S(F(18), 'C43', 1.0, z=(1.05, 1.16), c=(0.5, 0.55), grade='final', flash=3, punch=0.24, shake=10, chroma=4,
  sub=('N14', 3.0, 3))
S(F(20), 'C54', 0.3, speed=1.3, z=(1.06, 1.30), c=(0.5, 0.38), grade='final', flash=3, punch=0.24, shake=10, chroma=4,
  sub=('N27', 1.6, 3))
S(F(24), 'C53', 0.5, z=(1.0, 1.35), ease='in', grade='final', shake=10, chroma=5, punch=0.12, flash=2)
S(F(27), 'strobe', kind='strobe', grade='final', vig=0.4, shake=12, chroma=6,
  frames=[('N23', 2.6), ('N25', 2.4), ('C66', 2.0), ('N14', 3.2), ('N27', 1.8), ('C41', 2.0), ('N35', 2.9), ('C55', 2.0),
          ('N29', 3.0), ('C49', 4.0)])
# ===== OUTRO
S(110.08, 'C00', 0.2, z=(1.0, 5.2), c=(0.5, 0.5), c1=(0.5, 0.13), ease='exp', grade='outro', vig=1.0, flash=3,
  fadeblack=(112.9, 0.85))
S(114.17, 'black')


# beat-synced zoom pulse: light in the verse, hard in the choruses, none in the quiet parts
ok.pulse(15.66, 25.17, 'A', 0.028)
ok.pulse(25.17, 45.10, 'A', 0.014)
ok.pulse(45.10, 58.07, 'B', 0.020)
ok.pulse(58.07, 78.20, 'C', 0.032)
ok.pulse(91.54, 100.98, 'E', 0.045)
ok.pulse(100.98, 110.06, 'F', 0.050)

RED, PAPER = (214, 26, 32), (245, 243, 236)
PARTS = [('44', RED), ('교시', PAPER), (' ', None), ('생존수업', PAPER)]
SUB = "T H E   4 4 T H   P E R I O D   ·   S U R V I V A L   C L A S S"
ok.title_card(A(0), A(8), PARTS, sub=SUB, credit="원작  상C  「44교시 생존수업」  ·  네이버웹툰")
ok.end_card(114.17, PARTS, sub=SUB, credit="FAN-MADE OPENING   ·   원작  상C  (네이버웹툰)",
            fade=(116.35, 0.9), glitch=(115.44, ('C41', 1.5)))

# the class roll: fills on "한 명도 빠짐없이", goes dark tile by tile on "지워진 이름들"
ok.grid_tiles(['I01', 'I44', 'I03', 'I25', 'I42', 'I58', 'I12', 'I45',
               'I57', 'I04', 'I15', 'I20', 'I51', 'I28', 'I05', 'I24'])

# rule cards: children's chant in chalk, then the twisted reprise in red
ok.typo(4.67, 7.9, [[('하나,', 4.72)], [('종', 5.84), ('치면', 6.14)], [('교실로', 6.62), ('들어가', 7.2)]],
        side='L', end=7.8, style='chalk')
ok.typo(7.9, 10.26, [[('둘,', 7.98)], [('복도에선', 8.44)], [('돌아보지', 9.18), ('마', 9.78)]],
        side='R', end=10.1, style='chalk')
ok.typo(10.26, 13.0, [[('셋,', 10.34)], [('거울', 10.66), ('속', 11.14), ('나와', 11.32)], [('눈', 11.7), ('맞추지', 11.96), ('마', 12.72)]],
        side='L', end=12.95, style='chalk')
ok.typo(13.0, 15.66, [[('넷,', 13.08)], [('방송이', 13.26), ('나오면', 14.06)], [('귀를', 14.58), ('막아', 15.26)]],
        side='R', end=15.6, style='chalk')
ok.typo(80.52, 83.68, [[('하나,', 80.66)], [('종이', 81.7), ('쳐도', 82.14)], [('문이', 82.62), ('안', 83.04), ('열려', 83.28)]],
        side='L', end=83.66, style='blood')
ok.typo(83.68, 86.2, [[('둘,', 83.82)], [('복도', 84.2), ('끝에', 84.84)], [('누가', 85.18), ('서', 85.44), ('있어', 85.74)]],
        side='L', end=86.15, style='blood')
ok.typo(86.2, 88.73, [[('셋,', 86.26)], [('거울', 86.68), ('속', 87.32), ('내가', 87.58)], [('먼저', 87.94), ('웃어', 88.3)]],
        side='R', end=88.7, style='blood')
ok.typo(88.73, 90.94, [[('넷,', 88.9)], [('방송이', 89.16)], [('내', 89.94), ('이름을', 90.14), ('불러', 90.6)]],
        side='R', end=90.92, style='blood')

ok.lyrics([
    (25.22, 27.86, '평소와 다름없던 등굣길에'),
    (27.98, 30.28, '하늘이 까맣게 내려앉았어'),
    (30.38, 32.82, '학교를 통째로 삼킨 검은 원'),
    (32.96, 35.34, '돌아온 사람은 아무도 없대'),
    (35.44, 37.72, '종이 울리면 교실로 돌아가'),
    (37.82, 40.4, '복도엔 교과서 속 그 애가 걸어'),
    (40.52, 42.96, '웃는 얼굴로 다가오는 그림'),
    (43.04, 45.0, '어긴 사람부터 지워져 가'),
    (45.1, 47.58, '끝이 없는 복도, 뒤틀린 계단'),
    (47.64, 50.1, '지도 위에 규칙을 적어 나가'),
    (50.17, 52.64, '믿을 수 있는 건 서로뿐이야'),
    (52.7, 55.6, '종이 울린다, 지금이야, 달려'),
    (57.36, 59.92, '살아남아, 44교시'),
    (60.1, 62.46, '검은 원 속에 숨겨진 출구까지'),
    (62.56, 65.62, '교칙도 괴담도 전부 깨어난 밤'),
    (65.76, 68.1, '규칙을 읽어 내, 그게 살 길이야'),
    (68.2, 70.05, '살아남아, 44교시'),
    (70.2, 72.58, '여기서의 일 년은 밖의 하루'),
    (72.68, 75.74, '잡은 손 놓지 마, 같이 나가자'),
    (75.9, 78.18, '1학년 4반, 한 명도 빠짐없이'),
    (91.55, 93.72, '살아남아, 44교시'),
    (93.86, 96.22, '규칙이 바뀌어, 출구가 닫혀 가'),
    (96.28, 98.44, '비어 가는 자리, 지워진 이름들'),
    (98.6, 100.96, '뒤돌아보지 마, 바로 뒤에 있어'),
    (101.0, 102.84, '살아남아, 44교시'),
    (102.92, 105.66, '몇 번을 쓰러져도 종은 다시 울려'),
    (105.76, 108.48, '살아남아, 살아남아, 살아남아'),
    (108.66, 111.6, '아직 수업은 끝나지 않았어'),
    (111.88, 113.9, '44교시……'),
])

if __name__ == '__main__':
    ok.main(sections=[(0, '인트로'), (4.67, '수칙 노래'), (15.66, '타이틀 · 출석 보드 · 스톱타임'), (25.16, 'Verse'),
                      (45.10, 'Pre-Chorus'), (58.07, 'Chorus'), (78.21, 'Breakdown'), (91.54, 'Final Chorus'),
                      (110.08, '아웃트로')])
