# opkit API

`import opkit as ok` 후 프로젝트 파일에서 쓰는 함수와 파라미터 전체.

## 목차
1. init
2. 박자 헬퍼
3. S() — 컷
4. 합성 컷(kind)
5. 리듬과 글자
6. 명령
7. 좌표·단위 규칙

## 1. init

```python
ok.init(work, name, out=None, size=(1280, 720), fps=24, mood='horror',
        fonts=None, seed=44, accent=None, flash_alt=None)
```

| 인자 | 뜻 |
|---|---|
| `work` | `song.wav`, `grid.json`, `clips_*.json`, `stills_*.json`, `fonts.json`이 있는 폴더 |
| `name` | 완성본 파일 이름의 앞부분. 버전을 넣는다 (`작품_OP_v2`) |
| `out` | 완성본 폴더. 기본은 work의 상위 |
| `size`, `fps` | 출력 규격. 소스가 24fps면 24, 전부 30fps면 30 |
| `mood` | `horror` / `action` / `warm` 색 보정 세트. 작품 장르에 맞춰 고른다 |
| `fonts` | `{'title':…, 'hand':…, 'hand2':…, 'sub':…, 'small':…}` 경로로 fonts.json을 덮어씀 |
| `accent` | 네거티브 플래시·꺼진 격자 칸의 색 (기본 붉은색) |
| `flash_alt` | `redflash=1`일 때 흰색 다음에 오는 섬광 색 |

`ok.add_still('키', '경로')`로 폴더 밖의 이미지 한 장을 소스로 추가한다. `ok.DUR`은 곡 길이(초).

## 2. 박자 헬퍼

```python
A = ok.beats('A')      # grid.json의 구간 A
A(0)                   # 구간 A의 첫 박 시각(초). A(4)는 한 마디 뒤
ok.GRID['A']['per']    # 한 박의 길이(초)
```

## 3. S() — 컷

```python
S(t, src, tin=0.0, speed=1.0, z=(1.04, 1.09), c=(0.5, 0.5), c1=None, ease='lin',
  grade='verse', flash=0, shake=0, chroma=0, punch=0.0, vig=0.55, kind=None, tr=None, **옵션)
```

컷은 `t`에 시작해 다음 컷의 `t`까지 이어진다. 마지막에 `S(끝시각, 'black')`을 둔다.

| 인자 | 뜻 | 흔한 값 |
|---|---|---|
| `t` | 시작 시각(초). 박 헬퍼로 쓴다 | `A(8)` |
| `src` | 클립 키, 스틸 키, 또는 `'black'` | `'C12'` |
| `tin` | 클립의 몇 초부터 쓸지 | 동작 정점 0.3~0.6초 전 |
| `speed` | 재생 속도. 음수면 역재생(`tin`은 끝 지점) | 1.0~2.0, `-1.1` |
| `z` | 줌 (시작, 끝). 1.0 = 꽉 찬 화면 | 푸시 `(1.03, 1.12)`, 풀 `(1.3, 1.02)` |
| `c`, `c1` | 화면 중심 (x, y) 0~1. `c1`을 주면 그쪽으로 이동 | 얼굴 `(0.5, 0.42)` |
| `ease` | `lin` / `in`(끝에서 가속) / `out` / `exp` | 돌진 줌은 `in` |
| `grade` | 색 보정 이름: intro, chant, title, cast, verse, versed(어두운 벌스), pre, chorus, break, final, finald, outro, none | |
| `flash` | 첫 n프레임 섬광. 4 이상이면 강하게 | 2, 5 |
| `shake` | 흔들림 세기(1080 기준 px). 컷 초반에 강하고 잦아듦 | 5~18 |
| `chroma` | 색분리(px) | 2~6 |
| `punch` | 컷 시작의 순간 줌 | 0.08~0.35 |
| `vig` | 비네팅 | 0.3~1.1, 0이면 없음 |
| `tr` | 이 컷으로 **들어오는** 전환: `whip_l/r/u/d`, `zoom`, `glitch`, `black` | |

### 옵션 (키워드로 추가)

| 옵션 | 뜻 |
|---|---|
| `fadein=n` | 첫 n프레임 페이드 인 |
| `fadeout=n` | 마지막 n프레임 어둡게 |
| `fadeblack=(시각, 길이)` | 지정 시각부터 완전 암전 |
| `stepz=[(시각, 배율), …]` | 그 시각에 줌이 단계적으로 뜀 (스냅 줌) |
| `snap=(시각, 추가줌, (cx, cy), 길이)` | 그 시각에 지정 지점으로 급히 당김 |
| `desat=(시각, 길이, 채도)` | 그 시각부터 채도를 뺌 |
| `ramp=(길이, 배율)` | 컷 초반 `길이`초 동안 속도를 `배율`배로 (스피드 램프) |
| `sub=(클립, 시각, n)` | 컷의 마지막 n프레임을 다른 클립의 네거티브 프레임으로 (서브리미널) |
| `glitch_tail=초` | 컷 끝에서 색분리와 찢김이 커짐 |
| `flicker=1` | 불규칙하게 어두워짐 |
| `strobe=n` | n프레임마다 암전 반복 |
| `dimtail=초` | 컷 끝에서 어두워짐 |
| `hblur=n` | 가로 모션 블러 (스틸 팬에) |
| `redflash=1` | 섬광 2프레임째부터 강조색 |
| `nopulse=True` | 박자 펄스 제외 (타이틀 밑 그림 등) |
| `dup_ok=True` | 의도된 재사용이라 중복 검사에서 제외 |

## 4. 합성 컷 (kind)

```python
# 스톱타임 타격: 한 프레임을 네거티브(neg) 또는 강한 흑백(bw)으로
S(A(25), 'C41', 1.2, kind='hit', look='neg', punch=0.18, shake=8, vig=0)

# 2×2 인물 보드: step초마다 한 칸씩. 타일은 (클립 또는 스틸 키, 시작 초)
S(A(8), 'quad', kind='quad', step=ok.GRID['A']['per'], grade='cast', vig=0.3,
  tiles=[('C10', 0.2), ('C11', 0.3), ('I03', 0), ('C13', 0.3)])

# 4×4 격자: 채워짐 / 하나씩 꺼짐. 타일은 ok.grid_tiles()로 등록
S(C(56), 'grid', kind='grid_fill', step=ok.GRID['C']['per'] / 2, grade='chorus', vig=0.3, flash=2)
S(E(15), 'grid', kind='grid_erase', grade='final', vig=0.5)

# 스트로브: 2프레임마다 다음 프레임으로, 네거티브와 흑백 교대
S(F(27), 'strobe', kind='strobe', grade='final', shake=12, chroma=6,
  frames=[('N23', 2.6), ('N25', 2.4), ('C66', 2.0)])
```

`ok.grid_tiles(keys, erase_order=None)` — 16개. 키는 스틸 키 또는 `(클립, 시각)`. `erase_order`는 꺼지는 칸 번호 순서(기본 14칸이 꺼지고 2칸이 남는다).

보드와 격자로 들어가는 `tr`은 앞 컷의 퇴장에만 적용된다. 빈 칸이 많은 화면에 휩이나 줌을 걸면 검은 프레임으로 보이기 때문이다.

## 5. 리듬과 글자

```python
ok.pulse(t0, t1, 'A', 0.03)        # t0~t1 동안 구간 A 격자에 맞춘 박자 줌 펄스

ok.title_card(t0, t1, parts, sub=None, credit=None, size=212)
ok.end_card(t0, parts, sub=None, credit=None, size=212, fade=(시작, 길이), glitch=(시각, (클립, 초)))
# parts = [('강조어', (R,G,B)), (' ', None), ('나머지', (R,G,B))]

ok.typo(t0, t1, rows, side='L', end=None, style='chalk')
# rows = [[('하나,', 4.72)], [('종', 5.84), ('치면', 6.14)], …]  첫 줄은 크게. style: chalk(흰 분필) / blood(붉고 떨림)

ok.lyrics([(시작, 끝, '가사'), …])   # SRT와 '_가사자막' 버전에만 나온다. 메인에는 안 들어간다
```

타이포 스타일을 바꾸려면 `ok.TYPO_STYLES['이름'] = (폰트역할, 첫줄크기, 본문크기, (R,G,B,255), 떨림여부)`.

## 6. 명령

```bash
python3 project.py edl                  # 타임라인 표 + check
python3 project.py sheet [main|lyric|clean]
python3 project.py frames NAME t1 t2 …  # 지정 시각의 프레임 → sheets/NAME_00.jpg
python3 project.py seq NAME t count     # t부터 count프레임 연속
python3 project.py render [t0 t1 tag]   # 전체 3종, 또는 구간만 빠르게(메인 1종)
python3 project.py mux                  # 음악 합쳐 완성본 생성
python3 project.py srt                  # 등록된 가사를 <name>.srt로 (역전·겹침·길이 초과 검사)
python3 project.py qa                   # 완성본 검사 + sheets/qa_N.jpg
python3 project.py cutlist              # 컷 리스트 + 사용 소스 목록 md
python3 project.py all                  # check → render → mux → srt → qa → cutlist
```

완성본 이름: `<name>_<높이>p.mp4`(메인, 가사 없음), `…_가사자막.mp4`, `…_텍스트없음.mp4`, `<name>.srt`, `<name>_컷리스트.md`.

`qa`는 전체 디코딩 오류, 출력보다 작은 소스, 1.2초 이상 정지 화면, 검은 구간, 음량·피크를 출력하고 완성 파일에서 프레임 시트를 뽑는다.

## 7. 좌표·단위 규칙

- 글자 크기, 흔들림, 색분리 같은 픽셀 값은 전부 1080p 기준이다. 엔진이 출력 해상도에 맞게 줄인다. 720p로 바꿔도 프로젝트 파일을 고칠 필요가 없다.
- `c`의 x, y는 **소스 이미지** 안의 위치다. 인물이 소스의 x=0.5에 있을 때 `c=(0.62, …)`와 `z=1.2`를 주면 화면에서는 왼쪽(약 0.36)에 놓인다.
- `z`는 1.0 미만이 될 수 없다. 펀치·펄스·스냅은 곱해진다.
- 소스 화면비가 출력과 다르면 가운데를 잘라 채운다. 세로 이미지는 `c`의 y로 보일 부분을 정한다.
- 30fps 클립을 24fps로 내면 미세한 끊김이 생긴다. `speed`를 1.0이 아닌 값으로 주면 눈에 덜 띈다.
