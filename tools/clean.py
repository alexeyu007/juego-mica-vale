"""Limpia sprites extraidos: elimina fragmentos de sprites vecinos (colas en los
bordes), tiras de la hoja y etiquetas de texto, recortando las "tiras" que quedan
fuera de la silueta principal.

Uso:
  python tools/clean.py --dry-run            # solo imprime informe
  python tools/clean.py archivo.png ...      # limpia y guarda (in-place)
"""
import os, sys
import numpy as np
from PIL import Image

SPR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'sprites')
SOLID = 160        # alfa para definir el "solido" de cada parte
GROW = 6           # expansion del bbox unido para decidir pertenencia
MARGIN = 3         # margen que se conserva junto a la silueta


def components(mask):
    """bbox + area exactos de cada componente (8-conectividad, BFS)."""
    H, W = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    for y in range(H):
        xs = np.flatnonzero(mask[y] & ~seen[y])
        for x in xs:
            if seen[y, x]:
                continue
            stack = [(y, int(x))]
            seen[y, x] = True
            minx = maxx = int(x)
            miny = maxy = y
            area = 0
            while stack:
                cy, cx = stack.pop()
                area += 1
                if cx < minx: minx = cx
                if cx > maxx: maxx = cx
                if cy < miny: miny = cy
                if cy > maxy: maxy = cy
                for dy in (-1, 0, 1):
                    ny = cy + dy
                    if ny < 0 or ny >= H:
                        continue
                    for dx in (-1, 0, 1):
                        nx = cx + dx
                        if nx < 0 or nx >= W:
                            continue
                        if mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
            out.append(dict(x0=minx, y0=miny, x1=maxx, y1=maxy, area=area))
    return out


def analyse(path):
    im = Image.open(path).convert('RGBA')
    a = np.asarray(im).copy()
    alpha = a[:, :, 3]
    H, W = alpha.shape
    solid = alpha >= SOLID
    if not solid.any():
        return im, a, [], None, None

    comps = components(solid)
    comps.sort(key=lambda c: -c['area'])
    main = comps[0]
    kept = [main]
    kept_box = [main['x0'], main['y0'], main['x1'], main['y1']]

    # absorcion iterativa de partes que estan cerca de la silueta unida
    changed = True
    while changed:
        changed = False
        ex0, ey0, ex1, ey1 = (kept_box[0] - GROW, kept_box[1] - GROW,
                              kept_box[2] + GROW, kept_box[3] + GROW)
        for c in comps:
            if c in kept:
                continue
            ox = max(0, min(c['x1'], ex1) - max(c['x0'], ex0) + 1)
            oy = max(0, min(c['y1'], ey1) - max(c['y0'], ey0) + 1)
            frac = (ox * oy) / max(1, (c['x1'] - c['x0'] + 1) * (c['y1'] - c['y0'] + 1))
            if frac >= 0.3:
                kept.append(c)
                kept_box = [min(kept_box[0], c['x0']), min(kept_box[1], c['y0']),
                            max(kept_box[2], c['x1']), max(kept_box[3], c['y1'])]
                changed = True

    kx0, ky0, kx1, ky1 = kept_box
    dropped = [c for c in comps if c not in kept]

    strips = []   # (y0, y1, x0, x1, motivo) a poner a cero
    for c in dropped:
        if c['x1'] < kx0 - MARGIN:
            strips.append((0, H - 1, 0, kx0 - MARGIN, 'izq'))
        elif c['x0'] > kx1 + MARGIN:
            strips.append((0, H - 1, kx1 + MARGIN, W - 1, 'der'))
        elif c['y1'] < ky0 - MARGIN:
            strips.append((0, ky0 - MARGIN, 0, W - 1, 'arr'))
        elif c['y0'] > ky1 + MARGIN:
            strips.append((ky1 + MARGIN, H - 1, 0, W - 1, 'aba'))
        else:
            d = 3
            strips.append((max(0, c['y0'] - d), min(H - 1, c['y1'] + d),
                           max(0, c['x0'] - d), min(W - 1, c['x1'] + d), 'int'))

    # fusiona strips del mismo lado (se aplican todos, no solo uno)
    sides = {}
    for y0, y1, x0, x1, tag in strips:
        if tag == 'int':
            sides.setdefault('int', []).append((y0, y1, x0, x1))
    side_boxes = {}
    for y0, y1, x0, x1, tag in strips:
        if tag == 'int':
            continue
        b = side_boxes.get(tag)
        side_boxes[tag] = (y0, y1, x0, x1) if b is None else (
            min(b[0], y0), min(b[1], y1), max(b[2], x0), max(b[3], x1))

    return im, a, dropped, side_boxes, sides.get('int', [])


def fill_holes(a, bright_thr=215):
    """Rellena agujeros internos (alfa ~0 rodeado por el sprite) cuando el color
    subyacente es oscuro/saturado (pelo, contorno) y no fondo blanco."""
    alpha = a[:, :, 3]
    bg = alpha < 16
    H, W = alpha.shape
    seen = np.zeros_like(bg)
    stack = []
    for x in range(W):
        for y in (0, H - 1):
            if bg[y, x] and not seen[y, x]:
                seen[y, x] = True; stack.append((y, x))
    for y in range(H):
        for x in (0, W - 1):
            if bg[y, x] and not seen[y, x]:
                seen[y, x] = True; stack.append((y, x))
    while stack:
        cy, cx = stack.pop()
        for dy in (-1, 0, 1):
            ny = cy + dy
            if ny < 0 or ny >= H: continue
            for dx in (-1, 0, 1):
                nx = cx + dx
                if nx < 0 or nx >= W: continue
                if bg[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True; stack.append((ny, nx))
    holes = bg & ~seen
    if not holes.any():
        return a, 0
    # etiqueta los agujeros y decide uno a uno
    out = a.copy()
    filled = 0
    H2, W2 = holes.shape
    rem = holes.copy()
    for y in range(H2):
        xs = np.flatnonzero(rem[y])
        for x in xs:
            if not rem[y, x]:
                continue
            st = [(y, int(x))]; rem[y, x] = False
            pix = []
            while st:
                cy, cx = st.pop()
                pix.append((cy, cx))
                for dy in (-1, 0, 1):
                    ny = cy + dy
                    if ny < 0 or ny >= H2: continue
                    for dx in (-1, 0, 1):
                        nx = cx + dx
                        if nx < 0 or nx >= W2: continue
                        if rem[ny, nx]:
                            rem[ny, nx] = False
                            st.append((ny, nx))
            ys = [p[0] for p in pix]; xs2 = [p[1] for p in pix]
            rgb = a[np.array(ys), np.array(xs2), :3].astype(np.float32)
            if rgb.mean() <= bright_thr:
                out[np.array(ys), np.array(xs2), 3] = 255
                filled += len(pix)
    return out, filled


def profile_cut(a, side='left', thr=100, run=2, max_loss=.15):
    """Corta la tira lateral que queda antes de un hueco vertical: quita el
    fragmento de sprite vecino que se pegó al borde. Devuelve None si no toca."""
    alpha = a[:, :, 3]
    H, W = alpha.shape
    prof = alpha.max(axis=0) if side == 'left' else alpha.max(axis=0)[::-1]
    cut = None
    r = 1
    while r < len(prof) - run:
        if prof[r] < thr and (prof[r:r + run] < thr).all():
            before = prof[:r].max() if r else 0
            if before >= 150:
                j = r
                while j < len(prof) and prof[j] < 150:
                    j += 1
                if j < len(prof):
                    cut = j
                    break
        r += 1
    if cut is None or cut <= 1:
        return None
    out = a.copy()
    before_px = int((alpha > 16).sum())
    if side == 'left':
        out[:, :cut, 3] = 0
    else:
        out[:, W - cut:, 3] = 0
    after_px = int((out[:, :, 3] > 16).sum())
    if before_px == after_px:
        return None
    if (before_px - after_px) > max_loss * before_px:
        return None            # demasiado grande: no era un fragmento
    return out


def valley_cut(a, side='left', max_cols=60, min_gap=2, max_loss=.30):
    """Corta el fragmento de sprite vecino pegado al borde: busca en el perfil
    de píxeles por columna un 'valle' (hueco) que separe el fragmento de la
    silueta propia, y elimina todo lo que queda a la izquierda del valle."""
    alpha = a[:, :, 3]
    H, W = alpha.shape
    cnt = (alpha > 96).sum(axis=0).astype(float)
    if side == 'right':
        cnt = cnt[::-1]
    lim = min(W, max_cols)
    cut = None
    for i in range(2, lim):
        pre = cnt[max(0, i - 6):i]
        if pre.size == 0:
            continue
        premed = float(np.median(pre))
        if premed < 25:
            continue
        thr = 0.5 * premed
        if cnt[i] > thr:
            continue
        j = i
        while j < lim and cnt[j] <= thr:
            j += 1
        if j - i < min_gap:
            continue
        if j >= W or cnt[j:j + 15].max() < thr:
            continue
        cut = j
        break
    if cut is None or cut < 4:
        return None
    out = a.copy()
    before = int((alpha > 16).sum())
    if side == 'left':
        out[:, :cut, 3] = 0
    else:
        out[:, W - cut:, 3] = 0
    after = int((out[:, :, 3] > 16).sum())
    if before == after:
        return None
    if (before - after) > max_loss * before:
        return None
    return out


def defringe(a, iters=3, palethr=185, satt=50):
    """Quita el 'fringe' blanco: píxeles claros y desaturados que quedaron
    opacos pegados al contorno transparente (restos del fondo blanco)."""
    out = a.copy()
    H, W = out.shape[:2]
    removed = 0
    for _ in range(iters):
        alpha = out[:, :, 3]
        bg = alpha < 16
        # dilatacion manual del fondo 1 px (8-conectividad, sin roll)
        near = bg.copy()
        near[1:, :] |= bg[:-1, :]
        near[:-1, :] |= bg[1:, :]
        near[:, 1:] |= bg[:, :-1]
        near[:, :-1] |= bg[:, 1:]
        near[1:, 1:] |= bg[:-1, :-1]
        near[1:, :-1] |= bg[:-1, 1:]
        near[:-1, 1:] |= bg[1:, :-1]
        near[:-1, :-1] |= bg[1:, 1:]
        rgb = out[:, :, :3].astype(np.int16)
        pale = (rgb.min(axis=2) > palethr) & ((rgb.max(axis=2) - rgb.min(axis=2)) < satt)
        kill = pale & ~bg & near
        if not kill.any():
            break
        out[kill, 3] = 0
        removed += int(kill.sum())
    return out, removed


def harden(a, thr=170):
    """Endurece la alfa: píxeles cuyo color es claramente del personaje (no del
    fondo blanco) pasan a opacos. Quita el aspecto 'empolvado' del pelo."""
    out = a.copy()
    rgb = out[:, :, :3].astype(np.int16)
    m = (out[:, :, 3] > 16) & (rgb.min(axis=2) < thr)
    n = int((out[:, :, 3][m] < 255).sum())
    out[m, 3] = 255
    return out, n


def fill_holes2(a, white_min=205, white_sat=35):
    """Rellena agujeros internos que NO son fondo blanco (pelo claro, brillos),
    usando el color almacenado (idéntico al de la hoja fuente)."""
    alpha = a[:, :, 3]
    bg = alpha < 16
    H, W = alpha.shape
    seen = np.zeros_like(bg)
    stack = []
    for x in range(W):
        for y in (0, H - 1):
            if bg[y, x] and not seen[y, x]:
                seen[y, x] = True; stack.append((y, x))
    for y in range(H):
        for x in (0, W - 1):
            if bg[y, x] and not seen[y, x]:
                seen[y, x] = True; stack.append((y, x))
    while stack:
        cy, cx = stack.pop()
        for dy in (-1, 0, 1):
            ny = cy + dy
            if ny < 0 or ny >= H: continue
            for dx in (-1, 0, 1):
                nx = cx + dx
                if nx < 0 or nx >= W: continue
                if bg[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True; stack.append((ny, nx))
    holes = bg & ~seen
    if not holes.any():
        return a, 0
    out = a.copy()
    filled = 0
    rem = holes.copy()
    for y in range(H):
        xs0 = np.flatnonzero(rem[y])
        for x in xs0:
            if not rem[y, x]:
                continue
            st = [(y, int(x))]; rem[y, x] = False
            pix = []
            while st:
                cy, cx = st.pop()
                pix.append((cy, cx))
                for dy in (-1, 0, 1):
                    ny = cy + dy
                    if ny < 0 or ny >= H: continue
                    for dx in (-1, 0, 1):
                        nx = cx + dx
                        if nx < 0 or nx >= W: continue
                        if rem[ny, nx]:
                            rem[ny, nx] = False
                            st.append((ny, nx))
            ys = np.array([p[0] for p in pix]); xsa = np.array([p[1] for p in pix])
            rgb = a[ys, xsa, :3].astype(np.int16)
            iswhite = (rgb.min(axis=1) > white_min) & ((rgb.max(axis=1) - rgb.min(axis=1)) < white_sat)
            if iswhite.mean() < 0.5:
                out[ys, xsa, 3] = 255
                filled += len(pix)
    return out, filled


def restore_colored(a, dark=160, sat=45):
    """Recupera píxeles que la extracción dejó transparentes pero que claramente
    son del personaje (color oscuro o saturado), no del fondo blanco."""
    out = a.copy()
    rgb = out[:, :, :3].astype(np.int16)
    colored = (rgb.min(axis=2) < dark) | ((rgb.max(axis=2) - rgb.min(axis=2)) > sat)
    m = (out[:, :, 3] < 16) & colored
    n = int(m.sum())
    out[m, 3] = 255
    return out, n


def report(path):
    im, a, dropped, side_boxes, inner = analyse(path)
    alpha = a[:, :, 3]
    before = int((alpha > 16).sum())
    b = a.copy()
    for y0, y1, x0, x1, tag in ([(v[0], v[1], v[2], v[3], k) for k, v in side_boxes.items()] if side_boxes else []):
        b[y0:y1 + 1, x0:x1 + 1, 3] = 0
    for y0, y1, x0, x1 in inner:
        b[y0:y1 + 1, x0:x1 + 1, 3] = 0
    after = int((b[:, :, 3] > 16).sum())
    if before == after and not dropped:
        return None
    info = []
    if side_boxes:
        info.append('tiras ' + ','.join(f'{k}{v}' for k, v in side_boxes.items()))
    if inner:
        info.append(f'{len(inner)} interno(s)')
    lost = (before - after) * 100.0 / max(1, before)
    return f'{os.path.basename(path):26s} solido={len(dropped)} px-{lost:5.1f}%  ' + '; '.join(info)


def clean(path, save=True):
    im, a, dropped, side_boxes, inner = analyse(path)
    if side_boxes is None:
        return None
    b = a.copy()
    if side_boxes:
        for tag, (y0, y1, x0, x1) in side_boxes.items():
            b[y0:y1 + 1, x0:x1 + 1, 3] = 0
    for y0, y1, x0, x1 in inner:
        b[y0:y1 + 1, x0:x1 + 1, 3] = 0
    out = Image.fromarray(b)
    bb = out.getbbox()
    if bb:
        out = out.crop(bb)
    if save:
        out.save(path)
    return out, dropped, side_boxes


def clean_babies(path):
    """Agujeros del pelo + corte del fragmento vecino a la izquierda."""
    im = Image.open(path).convert('RGBA')
    a = np.asarray(im).copy()
    a, holes = fill_holes2(a)
    pc = profile_cut(a, 'left')
    if pc is not None:
        a = pc
    out = Image.fromarray(a)
    bb = out.getbbox()
    if bb:
        out = out.crop(bb)
    if holes or pc is not None:
        out.save(path)
    return holes, bool(pc is not None)


if __name__ == '__main__':
    args = sys.argv[1:]
    dry = '--dry-run' in args
    babies = '--babies' in args
    valley = '--valley' in args
    fringe = '--defringe' in args
    hard = '--harden' in args
    refill = '--refill' in args
    restore = '--restore' in args
    args = [x for x in args if not x.startswith('--')]
    if restore:
        files = args or sorted(f for f in os.listdir(SPR) if f.endswith('.png'))
        for fn in files:
            p = fn if os.path.isabs(fn) else os.path.join(SPR, fn)
            a = np.asarray(Image.open(p).convert('RGBA')).copy()
            r, n = restore_colored(a)
            if not n:
                print(f'{os.path.basename(p):26s} nada que recuperar')
                continue
            out = Image.fromarray(r)
            bb = out.getbbox()
            if bb:
                out = out.crop(bb)
            if not dry:
                out.save(p)
            print(f'{os.path.basename(p):26s} recupero +{n} px' + (' (dry)' if dry else ''))
        sys.exit(0)
    if refill:
        files = args or sorted(f for f in os.listdir(SPR) if f.endswith('.png'))
        for fn in files:
            p = fn if os.path.isabs(fn) else os.path.join(SPR, fn)
            a = np.asarray(Image.open(p).convert('RGBA')).copy()
            r, n = fill_holes2(a)
            if not n:
                print(f'{os.path.basename(p):26s} sin agujeros')
                continue
            out = Image.fromarray(r)
            bb = out.getbbox()
            if bb:
                out = out.crop(bb)
            if not dry:
                out.save(p)
            print(f'{os.path.basename(p):26s} relleno +{n} px' + (' (dry)' if dry else ''))
        sys.exit(0)
    if hard:
        files = args or sorted(f for f in os.listdir(SPR) if f.endswith('.png'))
        for fn in files:
            p = fn if os.path.isabs(fn) else os.path.join(SPR, fn)
            a = np.asarray(Image.open(p).convert('RGBA')).copy()
            r, n = harden(a)
            if not n:
                print(f'{os.path.basename(p):26s} ya opaco')
                continue
            out = Image.fromarray(r)
            bb = out.getbbox()
            if bb:
                out = out.crop(bb)
            if not dry:
                out.save(p)
            print(f'{os.path.basename(p):26s} opaco +{n} px' + (' (dry)' if dry else ''))
        sys.exit(0)
    if fringe:
        files = args or sorted(f for f in os.listdir(SPR) if f.endswith('.png'))
        for fn in files:
            p = fn if os.path.isabs(fn) else os.path.join(SPR, fn)
            a = np.asarray(Image.open(p).convert('RGBA')).copy()
            r, removed = defringe(a)
            if not removed:
                print(f'{os.path.basename(p):26s} sin fringe')
                continue
            out = Image.fromarray(r)
            bb = out.getbbox()
            if bb:
                out = out.crop(bb)
            if not dry:
                out.save(p)
            print(f'{os.path.basename(p):26s} fringe -{removed} px'
                  + (' (dry)' if dry else ''))
        sys.exit(0)
    if valley:
        files = args or [f for f in sorted(os.listdir(SPR))
                         if f.endswith('.png') and (f.startswith('mica_') or f.startswith('vale_'))]
        for fn in files:
            p = fn if os.path.isabs(fn) else os.path.join(SPR, fn)
            im = Image.open(p).convert('RGBA')
            a = np.asarray(im).copy()
            r = valley_cut(a, 'left')
            if r is None:
                print(f'{os.path.basename(p):26s} sin fragmento')
                continue
            out = Image.fromarray(r)
            bb = out.getbbox()
            if bb:
                out = out.crop(bb)
            if dry:
                print(f'{os.path.basename(p):26s} corte izq -> {out.size} (dry)')
                continue
            out.save(p)
            print(f'{os.path.basename(p):26s} corte izq -> {out.size}')
        sys.exit(0)
    if babies:
        for fn in sorted(os.listdir(SPR)):
            if not fn.endswith('.png'):
                continue
            if not (fn.startswith('mica_') or fn.startswith('vale_')):
                continue
            holes, cut = clean_babies(os.path.join(SPR, fn))
            if holes or cut:
                print(f'{fn:26s} agujeros={holes:5d} corte_izq={"si" if cut else "no"}')
        sys.exit(0)
    if not args:
        args = sorted(f for f in os.listdir(SPR) if f.endswith('.png'))
    for fn in args:
        p = fn if os.path.isabs(fn) else os.path.join(SPR, fn)
        if dry:
            r = report(p)
            if r:
                print(r)
        else:
            res = clean(p)
            print('limpio:', os.path.basename(p),
                  '->', res[0].size if res else 'sin cambios')
