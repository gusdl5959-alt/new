"""Fetch the Korean fonts (OFL, Google Fonts) subset to the characters this film uses → fonts/*.woff2 + fonts/fonts.css
Run: python3 tools/fonts.py   (needs network; re-run after changing any on-screen text)"""
import os, re, urllib.request, urllib.parse
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
chars = set()
for f in os.listdir(HERE):
    if f.endswith('.js'): chars |= set(open(os.path.join(HERE, f), encoding='utf-8').read())
chars = ''.join(sorted(c for c in chars if c.isprintable() and c not in '\\`'))
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'
FAMS = [('Nanum Gothic', [400, 700, 800]), ('Nanum Myeongjo', [800]), ('Nanum Gothic Coding', [700]), ('Nanum Pen Script', [400])]
css_out = []
os.makedirs(os.path.join(HERE, 'fonts'), exist_ok=True)
for fam, ws in FAMS:
    for w in ws:
        q = urllib.parse.urlencode({'family': f'{fam}:wght@{w}', 'text': chars})
        css = urllib.request.urlopen(urllib.request.Request('https://fonts.googleapis.com/css2?' + q, headers={'User-Agent': UA})).read().decode()
        url = re.search(r'url\((https://[^)]+)\)', css).group(1)
        name = f"{fam.replace(' ', '')}-{w}.woff2"
        open(os.path.join(HERE, 'fonts', name), 'wb').write(urllib.request.urlopen(url).read())
        css_out.append(f"@font-face{{font-family:'{fam}';font-weight:{w};src:url('{name}') format('woff2')}}")
        print(name, os.path.getsize(os.path.join(HERE, 'fonts', name)))
open(os.path.join(HERE, 'fonts', 'fonts.css'), 'w').write('\n'.join(css_out) + '\n')
print(len(chars), 'characters')
