"""Montaje de sprites sobre damero para inspeccion visual."""
import os, sys
import numpy as np
from PIL import Image

SPR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'sprites')
OUT = os.path.join(os.path.dirname(__file__), 'vis_')

def checker(shape, s=10):
    H, W = shape
    yy, xx = np.mgrid[0:H, 0:W]
    return np.where(((yy // s + xx // s) % 2) == 0, 200, 255).astype(np.uint8)

files = sys.argv[1:]
tiles = []
for fn in files:
    im = Image.open(os.path.join(SPR, fn)).convert('RGBA')
    im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    a = np.asarray(im).astype(np.float32)
    bg = np.stack([checker(a.shape[:2])] * 3, axis=2)
    al = a[:, :, 3:4] / 255.0
    rgb = a[:, :, :3] * al + bg * (1 - al)
    tiles.append(Image.fromarray(rgb.astype(np.uint8)))

cols = min(3, len(tiles))
rows = (len(tiles) + cols - 1) // cols
cw = max(t.width for t in tiles) + 8
ch = max(t.height for t in tiles) + 8
out = Image.new('RGB', (cw * cols, ch * rows), (30, 30, 30))
for i, t in enumerate(tiles):
    out.paste(t, ((i % cols) * cw + 4, (i // cols) * ch + 4))
path = OUT + '_'.join(f[:-4] for f in files)[:80] + '.png'
out.save(path)
print(path)
