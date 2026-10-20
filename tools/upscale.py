"""Aumenta la resolución de los sprites para que se vean nítidos en pantalla.

Para cada PNG:
  1. "bleed": extiende los colores del interior hacia el vacío (evita que el
     reescalado genere halos blancos por los píxeles transparentes).
  2. reescala RGB y alfa con LANCZOS (factor --factor, por defecto 3).
  3. enmascara el RGB con un sharp para que los bordes queden definidos.
  4. ajusta la rampa del alfa para que el contorno quede limpio.

Uso:
  python tools/upscale.py --factor 3            # aplica a assets/sprites
  python tools/upscale.py --factor 3 --dry-run  # solo informa tamaños
  python tools/upscale.py --factor 3 --out tools/_3x
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SPR = os.path.join(HERE, '..', 'assets', 'sprites')
BAK = os.path.join(HERE, '_sprites_1x')


def shift(a, dy, dx):
    out = np.zeros_like(a)
    ys = slice(max(0, dy), a.shape[0] + min(0, dy))
    xs = slice(max(0, dx), a.shape[1] + min(0, dx))
    yt = slice(max(0, -dy), a.shape[0] + min(0, -dy))
    xt = slice(max(0, -dx), a.shape[1] + min(0, -dx))
    if a.ndim == 3:
        out[ys, xs] = a[yt, xt]
    else:
        out[ys, xs] = a[yt, xt]
    return out


def bleed(rgb, known, iters=8):
    """Propaga los colores del interior hacia el exterior para poder reescalar
    sin que aparezcan halos claros en los bordes."""
    rgb = rgb.astype(np.float32).copy()
    known = known.copy()
    for _ in range(iters):
        if known.all():
            break
        cnt = np.zeros(known.shape, np.float32)
        acc = np.zeros_like(rgb)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            k = shift(known.astype(np.float32), dy, dx)
            cnt += k
            acc += rgb * k[:, :, None]
        fill = (~known) & (cnt > 0)
        if not fill.any():
            break
        rgb[fill] = acc[fill] / cnt[fill][:, None]
        known = known | fill
    return np.clip(rgb, 0, 255).astype(np.uint8)


def upsample(path_out, im, factor, sharp=90, alpha_lo=56, alpha_hi=205, quantize=True):
    rgba = np.asarray(im.convert('RGBA'))
    rgb, a = rgba[:, :, :3], rgba[:, :, 3]
    rgb = bleed(rgb, a > 0)

    big_rgb = Image.fromarray(rgb).resize((im.width * factor, im.height * factor), Image.LANCZOS)
    big_a = Image.fromarray(a).resize((im.width * factor, im.height * factor), Image.LANCZOS)

    if sharp:
        big_rgb = big_rgb.filter(ImageFilter.UnsharpMask(radius=factor * 0.75,
                                                          percent=sharp, threshold=2))
    # rampa de alfa más cerrada => contorno nítido sin escalones
    big_a = big_a.point(lambda v: 0 if v <= alpha_lo else
                        (255 if v >= alpha_hi else int((v - alpha_lo) * 255 / (alpha_hi - alpha_lo))))
    out = big_rgb.convert('RGBA')
    out.putalpha(big_a)
    if quantize:
        # paleta de 255 colores con alfa (tRNS): ~5x más ligero, misma nitidez
        out = out.quantize(colors=255, method=Image.FASTOCTREE)
    out.save(path_out, optimize=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--factor', type=int, default=3)
    ap.add_argument('--out', default=SPR)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--names', nargs='*', default=None)
    ap.add_argument('--sharp', type=int, default=90)
    ap.add_argument('--no-quantize', action='store_true')
    a = ap.parse_args()

    out_dir = a.out
    os.makedirs(out_dir, exist_ok=True)
    if not a.dry_run and os.path.abspath(out_dir) == os.path.abspath(SPR):
        os.makedirs(BAK, exist_ok=True)

    files = sorted(f for f in os.listdir(SPR) if f.endswith('.png'))
    if a.names:
        files = [f for f in files if f[:-4] in a.names]
    total = 0
    for f in files:
        src = os.path.join(SPR, f)
        im = Image.open(src)
        dst = os.path.join(out_dir, f)
        if a.dry_run:
            sz = im.width * a.factor * im.height * a.factor
            print('%-24s %4dx%-4d -> %dx%d' % (f, im.width, im.height,
                                               im.width * a.factor, im.height * a.factor))
            continue
        if os.path.abspath(out_dir) == os.path.abspath(SPR):
            bak = os.path.join(BAK, f)
            if not os.path.exists(bak):
                Image.open(src).save(bak)
            src_im = Image.open(bak)          # siempre parte de la 1x
        else:
            src_im = im
        out = upsample(dst, src_im, a.factor, sharp=a.sharp, quantize=not a.no_quantize)
        total += os.path.getsize(dst)
        print('%-24s %4dx%-4d -> %4dx%-4d  %5d KB' % (f, src_im.width, src_im.height,
                                                      out.width, out.height,
                                                      os.path.getsize(dst) // 1024))
    if not a.dry_run:
        print('TOTAL %d KB' % (total // 1024))


if __name__ == '__main__':
    main()
