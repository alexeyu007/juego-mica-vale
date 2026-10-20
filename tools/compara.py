"""Compara el sprite actual (assets/sprites) con una versión candidata (carpeta dada)
componiéndolas sobre rosa, una al lado de la otra."""
import os, sys
from PIL import Image, ImageDraw

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'sprites')
PINK = (244, 190, 224)

cand = sys.argv[1]
names = sys.argv[2:]
tiles = []
for n in names:
    row = []
    for d in (BASE, cand):
        p = os.path.join(d, n)
        im = Image.open(p).convert('RGBA') if os.path.exists(p) else Image.new('RGBA', (60, 60), (255, 0, 0, 255))
        im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
        b = Image.new('RGBA', im.size, PINK + (255,))
        row.append(Image.alpha_composite(b, im).convert('RGB'))
    tiles.append(row)

cols = len(tiles)
cw = max(max(t[0].width, t[1].width) for t in tiles) + 10
ch = max(t[0].height for t in tiles) + 26
o = Image.new('RGB', (cw * cols, ch * 2), (20, 20, 20))
d = ImageDraw.Draw(o)
for i, (a, b) in enumerate(tiles):
    o.paste(a, (i * cw + 5, 20))
    o.paste(b, (i * cw + 5, ch + 20))
    d.text((i * cw + 6, 4), n if False else names[i][:14], fill=(255, 255, 0))
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_cmp.png')
o.save(out)
print(out, o.size)
