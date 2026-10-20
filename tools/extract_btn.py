"""Extrae el botón de JUGAR de la portada (Arte/pantalla_inicial.png) con transparencia.

El botón es una píldora rosa con borde blanco y triángulo blanco; se separa del fondo
(color rosa -> cuerpo, anillo blanco dilatado -> contorno, hueco relleno -> triángulo).
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract2 as e

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Arte', 'pantalla_inicial.png')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'sprites', 'btn_play.png')

PINK = np.array([248, 96, 153])
REG = (110, 535, 375, 775)          # región de la portada con el botón


def dilate(mask, r):
    out = mask.copy()
    for _ in range(r):
        o = out.copy()
        o[1:, :] |= out[:-1, :]
        o[:-1, :] |= out[1:, :]
        o[:, 1:] |= out[:, :-1]
        o[:, :-1] |= out[:, 1:]
        out = o
    return out


def main():
    im = np.asarray(Image.open(SRC).convert('RGB')).astype(int)
    x0, y0, x1, y1 = REG
    sub = im[y0:y1, x0:x1]

    pink = np.abs(sub - PINK).max(axis=2) < 55
    comps = e.components(pink)
    comps = [c for c in comps if len(c) > 800]
    if not comps:
        raise SystemExit('no se encontró la píldora')
    pill = max(comps, key=len)
    body = np.zeros(pink.shape, bool)
    for (yy, xx) in pill:
        body[yy, xx] = True

    # contorno blanco: anillo alrededor del cuerpo
    near_white = sub.min(axis=2) > 210
    ring = dilate(body, 11) & ~dilate(body, 2) & near_white
    # triángulo: hueco claro dentro del cuerpo
    holes = e.fill_holes(body)
    tri = holes & ~body & (sub.min(axis=2) > 195)

    mask = body | ring | tri
    mask = e.fill_holes(mask)

    # recorta al borde del anillo
    ys, xs = np.nonzero(mask)
    mask = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    rgb = sub[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

    alpha = np.where(mask, 255, 0).astype(np.uint8)
    out = Image.fromarray(np.dstack([rgb.astype(np.uint8), alpha]), 'RGBA')
    a = out.getchannel('A').filter(ImageFilter.GaussianBlur(0.8))
    a = a.point(lambda v: 0 if v < 40 else min(255, int((v - 40) * 255 / 200)))
    out.putalpha(a)
    out.save(OUT)
    print('btn_play', out.size, '->', OUT)

    # vista previa sobre el rosa del juego
    prev = out.resize((out.width * 2, out.height * 2), Image.LANCZOS)
    b = Image.new('RGBA', prev.size, (244, 190, 224, 255))
    Image.alpha_composite(b, prev).convert('RGB').save(
        os.path.join(os.path.dirname(OUT), '..', '..', 'tools', '_btn_prev.png'))


if __name__ == '__main__':
    main()
