"""Zoom de sprites sobre rosa para ver bordes/halos con detalle."""
import os, sys
from PIL import Image

SPR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'sprites')
PINK = (244, 190, 224)

names = sys.argv[2:]
scale = int(sys.argv[1])
tiles = []
for n in names:
    im = Image.open(os.path.join(SPR, n)).convert('RGBA')
    im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    b = Image.new('RGBA', im.size, PINK + (255,))
    tiles.append(Image.alpha_composite(b, im).convert('RGB'))
cols = min(3, len(tiles))
rows = (len(tiles) + cols - 1) // cols
cw = max(t.width for t in tiles) + 10
ch = max(t.height for t in tiles) + 10
o = Image.new('RGB', (cw * cols, ch * rows), (20, 20, 20))
for i, t in enumerate(tiles):
    o.paste(t, ((i % cols) * cw + 5, (i // cols) * ch + 5))
out = os.path.join(os.path.dirname(__file__), '_zoom.png')
o.save(out)
print(out, o.size)
