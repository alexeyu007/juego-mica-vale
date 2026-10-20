"""Diagnóstico de halos: compone sprites sobre el rosa del juego y mide bordes claros."""
import os, sys
import numpy as np
from PIL import Image

SPR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'sprites')
PINK = (244, 190, 224)


def stats(path):
    im = np.asarray(Image.open(path).convert('RGBA')).astype(np.int16)
    a = im[:, :, 3]
    rgb = im[:, :, :3]
    op = a > 200
    semi = (a > 0) & (a < 250)
    if op.sum() == 0:
        return None
    # halo: píxel opaco/semisemi claro y desaturado en el borde (vecino de transparencia)
    pale = (rgb.min(axis=2) > 195) & ((rgb.max(axis=2) - rgb.min(axis=2)) < 45)
    edge = np.zeros(a.shape, bool)
    edge[1:, :] |= (a[1:, :] == 0) | (a[:-1, :] == 0)
    edge[:-1, :] |= (a[:-1, :] == 0) | (a[1:, :] == 0)
    edge[:, 1:] |= (a[:, 1:] == 0) | (a[:, :-1] == 0)
    edge[:, :-1] |= (a[:, :-1] == 0) | (a[:, 1:] == 0)
    halo = (edge & op & pale).sum()
    return dict(op=int(op.sum()), semi=int(semi.sum()), halo=int(halo),
                halo_pct=round(100.0 * halo / max(1, op.sum()), 2))


def compose(names, out, scale=2, bg=PINK):
    tiles = []
    for n in names:
        im = Image.open(os.path.join(SPR, n)).convert('RGBA')
        im = im.resize((im.width * scale, im.height * scale), Image.LANCZOS)
        b = Image.new('RGBA', im.size, bg + (255,))
        tiles.append(Image.alpha_composite(b, im).convert('RGB'))
    cols = min(4, len(tiles))
    rows = (len(tiles) + cols - 1) // cols
    cw = max(t.width for t in tiles) + 10
    ch = max(t.height for t in tiles) + 10
    o = Image.new('RGB', (cw * cols, ch * rows), (25, 25, 25))
    for i, t in enumerate(tiles):
        o.paste(t, ((i % cols) * cw + 5, (i // cols) * ch + 5))
    o.save(out)
    return out


if __name__ == '__main__':
    names = sys.argv[1:] or sorted(f for f in os.listdir(SPR) if f.endswith('.png'))
    print('%-24s %8s %8s %8s %7s' % ('sprite', 'opaco', 'semi', 'halo', 'halo%'))
    for n in names:
        s = stats(os.path.join(SPR, n))
        if s:
            print('%-24s %8d %8d %8d %7.2f' % (n, s['op'], s['semi'], s['halo'], s['halo_pct']))
    compose(names[:16], os.path.join(os.path.dirname(__file__), '_pink1.png'))
    if len(names) > 16:
        compose(names[16:32], os.path.join(os.path.dirname(__file__), '_pink2.png'))
