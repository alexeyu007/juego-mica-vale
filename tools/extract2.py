"""Extracción v2: recorta por componente del arte (no por caja fija), elimina el fondo
casi blanco de la hoja, quita halos y suaviza el borde con alfa antialias.

Uso:
  python tools/extract2.py            # reextrae las celdas 'std' a assets/sprites
  python tools/extract2.py --outdir tools/_sprites_v2
"""
import os
import sys
from collections import deque

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract

SPR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'sprites')

# Celdas que interesan al juego (modo 'std'); las 'keep' (nubes, pañuelos) se conservan.
GAME = [
    'mica_normal', 'mica_feliz', 'mica_riendo', 'mica_sorpresa', 'mica_asustada',
    'mica_preocupada', 'mica_triste', 'mica_enojo', 'mica_estornudo', 'mica_moquito',
    'mica_enferma', 'mica_dormida', 'mica_preparada', 'mica_celebrando',
    'vale_normal', 'vale_feliz', 'vale_sorpresa', 'vale_preocupada', 'vale_triste',
    'vale_estornudo', 'vale_moquito', 'vale_enferma', 'vale_dormida',
    'vale_preparada', 'vale_celebrando',
    'virus_normal', 'virus_enojado', 'virus_sorprendido', 'virus_triste', 'virus_baba',
    'virus2_rojo', 'virus_pequeno', 'virus_mediano', 'virus_grande', 'virus_danado_peq',
    'corazon', 'corazon_gris', 'ui_pausa2', 'estrella_ui', 'patito_ui', 'vida_extra',
    'fx_estrella', 'fx_lluvia', 'fx_moquito', 'panuelo_caja',
]

# margen para buscar el componente del arte alrededor de la caja original
WINDOW = {'virus_grande': 26, 'virus_danado_peq': 30, 'virus_mediano': 22,
          'virus_pequeno': 22, 'corazon': 12, 'corazon_gris': 12, 'vida_extra': 14,
          'ui_pausa2': 10, 'estrella_ui': 10, 'patito_ui': 10, 'fx_lluvia': 10,
          'fx_moquito': 8, 'fx_estrella': 10, 'panuelo_caja': 10}

# margen por defecto para buscar el componente del arte
DEFAULT_WINDOW = 24

# Ajustes por sprite:
#   multi -> conserva todas las piezas (estrellas sueltas, destellos)
#   trim  -> recorta la píldora de etiqueta inferior aunque el modo sea 'keep'
#   erode -> quita halo claro (por defecto en 'std')
CFG = {
    'fx_lluvia': dict(multi=True, erode=False),
    'fx_moquito': dict(multi=True, erode=False),
    'fx_estrella': dict(multi=True, erode=False),
    'vida_extra': dict(multi=True, erode=False, box=(1420, 898, 1496, 968)),
    'panuelo_caja': dict(trim=True, erode=False),
    # iconos donde el arte toca a los vecinos: caja ajustada a mano
    'corazon': dict(box=(1207, 802, 1253, 847)),
    'corazon_gris': dict(box=(1299, 804, 1344, 847)),
    'ui_pausa2': dict(box=(1361, 797, 1422, 858)),
    'estrella_ui': dict(box=(1443, 797, 1505, 857)),
}


def pale_mask(rgb, thr=228, sat=34):
    mn = rgb.min(axis=2)
    mx = rgb.max(axis=2)
    return (mn >= thr) & ((mx - mn) <= sat)


def components(mask):
    """Etiqueta componentes 4-conectados; devuelve lista de arrays de índices."""
    H, W = mask.shape
    lab = np.zeros((H, W), np.int32)
    comps = []
    flat_m = mask
    for sy in range(H):
        row = flat_m[sy]
        for sx in range(W):
            if not row[sx] or lab[sy, sx]:
                continue
            idx = []
            q = deque([(sy, sx)])
            lab[sy, sx] = len(comps) + 1
            while q:
                y, x = q.popleft()
                idx.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and flat_m[ny, nx] and not lab[ny, nx]:
                        lab[ny, nx] = len(comps) + 1
                        q.append((ny, nx))
            comps.append(idx)
    return comps


def auto_box(sheet, box, win):
    """Caja ajustada al componente de arte que más solapa la caja original."""
    x0, y0, x1, y1 = box
    wx0, wy0 = max(0, x0 - win), max(0, y0 - win)
    wx1, wy1 = min(sheet.shape[1], x1 + win), min(sheet.shape[0], y1 + win)
    sub = sheet[wy0:wy1, wx0:wx1]
    m = ~pale_mask(sub)
    comps = components(m)
    if not comps:
        return box
    best, best_score = -1, -1
    for c in comps:
        ys = [p[0] for p in c]
        xs = [p[1] for p in c]
        cy0, cy1, cx0, cx1 = min(ys), max(ys) + 1, min(xs), max(xs) + 1
        ox0, ox1 = max(cx0, x0 - wx0), min(cx1, x1 - wx0)
        oy0, oy1 = max(cy0, y0 - wy0), min(cy1, y1 - wy0)
        ov = max(0, ox1 - ox0) * max(0, oy1 - oy0)
        # pureza: premia al componente contenido dentro de la caja original
        score = ov * (ov / float(len(c)))
        if score > best_score:
            best_score, best = score, (cx0, cy0, cx1, cy1)
    cx0, cy0, cx1, cy1 = best
    m2 = 2
    return (max(0, wx0 + cx0 - m2), max(0, wy0 + cy0 - m2),
            min(sheet.shape[1], wx0 + cx1 + m2), min(sheet.shape[0], wy0 + cy1 + m2))


def flood_outside(pale):
    """Píxeles claros conectados con el borde = fondo."""
    H, W = pale.shape
    out = np.zeros((H, W), bool)
    q = deque()
    for x in range(W):
        for y in (0, H - 1):
            if pale[y, x] and not out[y, x]:
                out[y, x] = True
                q.append((y, x))
    for y in range(H):
        for x in (0, W - 1):
            if pale[y, x] and not out[y, x]:
                out[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and pale[ny, nx] and not out[ny, nx]:
                out[ny, nx] = True
                q.append((ny, nx))
    return out


def erode_pale(obj, rgb, iters=14, thr=205, sat=40, need=5):
    """Quita píxeles claros y desaturados pegados al vacío (halo del recorte)."""
    obj = obj.copy()
    for _ in range(iters):
        pale = (rgb.min(axis=2) > thr) & ((rgb.max(axis=2) - rgb.min(axis=2)) < sat)
        cand = obj & pale
        if not cand.any():
            break
        # cuenta vecinos transparentes con desplazamientos
        t = (~obj).astype(np.int8)
        cnt = np.zeros(obj.shape, np.int8)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            sh = np.zeros(obj.shape, np.int8)
            ys = slice(max(0, dy), obj.shape[0] + min(0, dy))
            xs = slice(max(0, dx), obj.shape[1] + min(0, dx))
            yt = slice(max(0, -dy), obj.shape[0] + min(0, -dy))
            xt = slice(max(0, -dx), obj.shape[1] + min(0, -dx))
            sh[ys, xs] = t[yt, xt]
            cnt += sh
        kill = cand & (cnt >= need)
        if not kill.any():
            break
        obj &= ~kill
    return obj


def fill_holes(obj):
    out = flood_outside(~obj)
    return obj | (~out)


def trim_bottom(rgb, obj):
    """Corta la píldora de etiqueta inferior (texto morado o banda muy clara)."""
    h, w = rgb.shape[:2]

    def row_dark(y):
        r = rgb[y]
        return int(((r.max(axis=1) < 195) & (r[:, 2] > r[:, 1] + 20)).sum())

    def row_pale(y):
        return int(pale_mask(rgb[y:y + 1], 210, 40).sum())

    limit = int(h * 0.45)
    y = h - 1
    while y > limit:
        d, p = row_dark(y), row_pale(y)
        if d >= max(8, w * 0.15) or p >= w * 0.6:
            top = y
            while top > limit:
                d2, p2 = row_dark(top), row_pale(top)
                if d2 >= max(4, w * 0.06) or p2 >= w * 0.6:
                    top -= 1
                else:
                    break
            if 0 < y - top <= 40:
                return top
            y = top
        else:
            y -= 1
    return h


def cut_neighbor(obj, box0, box):
    """Corta restos de arte vecino pegados al borde: se busca un valle claro en el
    perfil de columnas dentro del 45% exterior de cada lado y se corta ahí."""
    obj = obj.copy()
    H, W = obj.shape
    cnt = obj.sum(axis=0).astype(float)
    if cnt.max() == 0 or W < 20:
        return obj
    mx = cnt.max()
    # --- izquierda ---
    lim = int(W * 0.45)
    if lim > 4:
        seg = cnt[:lim]
        pmin = int(seg.argmin())
        if 2 < pmin and seg[pmin] <= mx * 0.15 and cnt[:pmin].max() >= mx * 0.5 \
                and (W - pmin - 1) >= W * 0.55:
            obj[:, :pmin + 1] = False
    # --- derecha ---
    lim = int(W * 0.55)
    if W - lim > 4:
        seg = cnt[lim:]
        pmin = lim + int(seg.argmin())
        if pmin < W - 3 and seg.min() <= mx * 0.15 and cnt[pmin + 1:].max() >= mx * 0.5 \
                and pmin >= W * 0.45:
            obj[:, pmin:] = False
    return obj


def extract_cell(sheet_rgb, cell, out_dir):
    name, mode = cell[1], cell[6]
    cfg = CFG.get(name, {})
    box = tuple(cfg.get('box', cell[2:6]))
    box0 = box
    if 'box' not in cfg:
        box = auto_box(sheet_rgb, box, WINDOW.get(name, DEFAULT_WINDOW))
    x0, y0, x1, y1 = box
    sub = sheet_rgb[y0:y1, x0:x1]
    if sub.size == 0:
        return None
    h, w = sub.shape[:2]
    if (mode == 'std' and 'box' not in cfg) or cfg.get('trim'):
        h = trim_bottom(sub, None)
        sub = sub[:h]
        h, w = sub.shape[:2]

    obj = ~flood_outside(pale_mask(sub))
    if mode == 'std' and cfg.get('erode', True):
        obj = erode_pale(obj, sub)
    # conserva el componente principal y los que estén bien dentro de la caja original
    comps = components(obj)
    if comps:
        bx0, by0, bx1, by1 = box0
        keep = np.zeros(obj.shape, bool)
        if cfg.get('multi'):
            areas = [len(c) for c in comps]
            amax = max(areas)
            for c, a in zip(comps, areas):
                if a >= max(8, amax * 0.02):
                    for (yy, xx) in c:
                        keep[yy, xx] = True
        else:
            best, best_score = -1, -1
            info = []
            for c in comps:
                ys = [p[0] for p in c]
                xs = [p[1] for p in c]
                cy0, cy1, cx0, cx1 = min(ys), max(ys) + 1, min(xs), max(xs) + 1
                ox0, ox1 = max(cx0, x0 - bx0), min(cx1, x1 - bx0)
                oy0, oy1 = max(cy0, y0 - by0), min(cy1, y1 - by0)
                ov = max(0, ox1 - ox0) * max(0, oy1 - oy0)
                info.append((c, ov, cy0, cy1, cx0, cx1))
                score = ov * (ov / float(len(c)))
                if score > best_score:
                    best_score, best = score, len(info) - 1
            for i, (c, ov, cy0, cy1, cx0, cx1) in enumerate(info):
                purity = ov / float(len(c))
                if i == best or purity >= 0.45:
                    for (yy, xx) in c:
                        keep[yy, xx] = True
        obj = keep
    if mode == 'std' and not cfg.get('multi'):
        obj = cut_neighbor(obj, box0, box)
    if mode == 'std':
        obj = fill_holes(obj)

    alpha = np.where(obj, 255, 0).astype(np.uint8)
    im = Image.fromarray(np.dstack([sub, alpha]), 'RGBA')
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    a = im.getchannel('A').filter(ImageFilter.GaussianBlur(0.8))
    a = a.point(lambda v: 0 if v < 40 else min(255, int((v - 40) * 255 / 200)))
    im.putalpha(a)
    path = os.path.join(out_dir, name + '.png')
    im.save(path)
    return im.size


if __name__ == '__main__':
    out_dir = SPR
    if '--outdir' in sys.argv:
        out_dir = sys.argv[sys.argv.index('--outdir') + 1]
    os.makedirs(out_dir, exist_ok=True)
    only = [a for a in sys.argv[1:] if not a.startswith('-') and a != out_dir]
    cells = [c for c in extract.CELLS if (c[6] == 'std' or c[1] in CFG)
             and (not only or c[1] in only)]
    for cell in cells:
        if cell[1] not in GAME and not only:
            continue
        sheet = extract.SHEETS[cell[0]]
        arr = np.asarray(sheet)
        sz = extract_cell(arr, cell, out_dir)
        print('%-20s %s' % (cell[1], sz))
    print('listo ->', out_dir)
