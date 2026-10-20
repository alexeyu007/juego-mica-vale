"""Extrae sprites de los dos sheet y genera PNGs con fondo transparente."""
import os
from collections import Counter
from PIL import Image, ImageFilter

OUT = 'assets/sprites'
os.makedirs(OUT, exist_ok=True)

SHEETS = {
    'g': Image.open('Arte/linea_grafica.png').convert('RGB'),
    'p': Image.open('personajes/ultimo_personas_sin_fondo.png').convert('RGB'),
}

# (hoja, nombre, x0, y0, x1, y1, modo)
# modo 'std'  -> limpia halos claros y píldoras de etiqueta (cabezas, virus, ui sólida)
# modo 'keep' -> conserva blancos (efectos de nube, caja de pañuelos, oso)
CELLS = [
    # ---- linea_grafica: gemelas ----
    ('g', 'cuna_mica', 1036, 664, 1236, 806, 'std'),
    ('g', 'cuna_vale', 1258, 664, 1466, 806, 'std'),
    ('g', 'cabeza_mica', 1032, 56, 1238, 200, 'std'),
    ('g', 'cabeza_vale', 1256, 56, 1466, 200, 'std'),
    # ---- linea_grafica: virus ----
    ('g', 'virus_normal', 30, 858, 174, 962, 'std'),
    ('g', 'virus_enojado', 202, 858, 354, 962, 'std'),
    ('g', 'virus_sorprendido', 346, 858, 490, 962, 'std'),
    ('g', 'virus_triste', 476, 858, 624, 962, 'std'),
    ('g', 'virus_baba', 636, 858, 777, 962, 'std'),
    ('g', 'virus_puf', 820, 842, 994, 942, 'keep'),
    ('g', 'ui_puf_efecto', 1370, 840, 1514, 908, 'keep'),
    ('g', 'ui_patito', 1038, 928, 1122, 1002, 'std'),
    ('g', 'ui_bloque', 1152, 928, 1238, 1002, 'std'),
    ('g', 'ui_oso', 1392, 926, 1484, 1004, 'keep'),
    # ---- personas: expresiones Mica ----
    ('p', 'mica_normal', 26, 54, 157, 176, 'std'),
    ('p', 'mica_feliz', 155, 54, 288, 176, 'std'),
    ('p', 'mica_riendo', 287, 54, 428, 176, 'std'),
    ('p', 'mica_sorpresa', 425, 54, 563, 176, 'std'),
    ('p', 'mica_asustada', 559, 54, 698, 176, 'std'),
    ('p', 'mica_preocupada', 695, 54, 833, 176, 'std'),
    ('p', 'mica_triste', 829, 54, 968, 176, 'std'),
    ('p', 'mica_enojo', 964, 54, 1103, 176, 'std'),
    ('p', 'mica_estornudo', 26, 218, 158, 346, 'std'),
    ('p', 'mica_moquito', 155, 218, 288, 346, 'std'),
    ('p', 'mica_enferma', 289, 218, 428, 346, 'std'),
    ('p', 'mica_dormida', 964, 218, 1103, 346, 'std'),
    # ---- personas: expresiones Vale ----
    ('p', 'vale_normal', 26, 448, 157, 563, 'std'),
    ('p', 'vale_feliz', 155, 448, 288, 563, 'std'),
    ('p', 'vale_sorpresa', 425, 448, 563, 563, 'std'),
    ('p', 'vale_preocupada', 695, 448, 833, 563, 'std'),
    ('p', 'vale_triste', 829, 448, 968, 563, 'std'),
    ('p', 'vale_estornudo', 26, 603, 158, 716, 'std'),
    ('p', 'vale_moquito', 155, 603, 288, 716, 'std'),
    ('p', 'vale_enferma', 289, 603, 428, 716, 'std'),
    ('p', 'vale_dormida', 964, 603, 1103, 716, 'std'),
    # ---- personas: acciones ----
    ('p', 'mica_preparada', 1136, 226, 1264, 348, 'std'),
    ('p', 'mica_celebrando', 1262, 226, 1394, 348, 'std'),
    ('p', 'mica_golpeando', 1388, 90, 1522, 182, 'std'),
    ('p', 'vale_preparada', 1136, 604, 1264, 718, 'std'),
    ('p', 'vale_celebrando', 1262, 604, 1394, 718, 'std'),
    ('p', 'vale_golpeando', 1388, 456, 1522, 564, 'std'),
    # ---- personas: virus ----
    ('p', 'virus2_rojo', 656, 794, 772, 884, 'std'),
    ('p', 'virus_pequeno', 48, 904, 110, 982, 'std'),
    ('p', 'virus_mediano', 126, 904, 204, 982, 'std'),
    ('p', 'virus_grande', 216, 900, 310, 982, 'std'),
    ('p', 'virus_danado_peq', 386, 906, 470, 982, 'std'),
    # ---- personas: efectos (blancos, conservar) ----
    ('p', 'fx_puf', 834, 790, 950, 886, 'keep'),
    ('p', 'fx_achis', 939, 792, 1050, 886, 'keep'),
    ('p', 'fx_estrella', 1024, 798, 1134, 878, 'std'),
    ('p', 'fx_lluvia', 826, 894, 950, 978, 'std'),
    ('p', 'fx_moquito', 936, 888, 1014, 978, 'std'),
    # ---- personas: ui ----
    ('p', 'corazon', 1204, 798, 1256, 858, 'std'),
    ('p', 'corazon_gris', 1294, 798, 1352, 858, 'std'),
    ('p', 'ui_pausa2', 1358, 794, 1422, 862, 'std'),
    ('p', 'estrella_ui', 1438, 788, 1506, 864, 'std'),
    ('p', 'panuelo_caja', 1202, 892, 1307, 990, 'keep'),
    ('p', 'patito_ui', 1310, 894, 1400, 990, 'std'),
    ('p', 'vida_extra', 1406, 892, 1508, 990, 'std'),
]

PALE_MIN = 210   # px claros y desaturados = candidatos a halo/píldora


def is_pale(r, g, b):
    return min(r, g, b) > PALE_MIN and (max(r, g, b) - min(r, g, b)) < 40


def border_clusters(ring):
    q = Counter((r // 16 * 16 + 8, g // 16 * 16 + 8, b // 16 * 16 + 8) for r, g, b in ring)
    centers = []
    for col, n in q.most_common(16):
        if n < len(ring) * 0.006:
            break
        if all(abs(col[0] - c[0]) + abs(col[1] - c[1]) + abs(col[2] - c[2]) > 40 for c in centers):
            centers.append(col)
        if len(centers) >= 6:
            break
    return centers


def trim_bottom(w, h, src, mode):
    """Corta píldora de etiqueta inferior (banda ancha clara o texto)."""
    def row_dark(y):
        return sum(1 for x in range(w)
                   if max(src[x, y][:3]) < 195 and src[x, y][2] > src[x, y][1] + 20)
    def row_pale(y):
        return sum(1 for x in range(w) if is_pale(*src[x, y][:3]))
    limit = int(h * 0.42)
    y = h - 1
    while y > limit:
        d, p = row_dark(y), row_pale(y)
        if d >= max(10, w * 0.18) or (mode == 'std' and p >= w * 0.62):
            top = y
            while top > limit:
                d2, p2 = row_dark(top), row_pale(top)
                if d2 >= max(5, w * 0.08) or (mode == 'std' and p2 >= w * 0.62):
                    top -= 1
                else:
                    break
            if y - top <= 40:
                return top
            y = top
        else:
            y -= 1
    return h


def cutout(sheet, cell):
    name, (x0, y0, x1, y1, mode) = cell[1], cell[2:7]
    crop = sheet.crop((x0, y0, x1, y1))
    w, h = crop.size
    src = crop.load()
    h = trim_bottom(w, h, src, mode)
    crop = crop.crop((0, 0, w, h))
    w, h = crop.size
    src = crop.load()

    ring = [src[x, 0][:3] for x in range(w)] + [src[x, h - 1][:3] for x in range(w)] \
        + [src[0, y][:3] for y in range(h)] + [src[w - 1, y][:3] for y in range(h)]
    centers = border_clusters(ring)

    def is_bg(x, y):
        r, g, b = src[x, y][:3]
        for c in centers:
            if abs(r - c[0]) <= 18 and abs(g - c[1]) <= 18 and abs(b - c[2]) <= 18:
                return True
        return False

    alpha = bytearray([255]) * (w * h)
    stack = [(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)] \
        + [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)]
    while stack:
        x, y = stack.pop()
        i = y * w + x
        if alpha[i] == 0 or not is_bg(x, y):
            continue
        alpha[i] = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and alpha[ny * w + nx]:
                    stack.append((nx, ny))

    # en modo 'std' erosiona halos claros pegados al vacío (no toca ojos ni dientes
    # porque esos blancos están rodeados de contorno oscuro, lejos del vacío)
    if mode == 'std':
        for _ in range(12):
            changed = 0
            doomed = []
            for y in range(h):
                for x in range(w):
                    i = y * w + x
                    if alpha[i] == 0:
                        continue
                    r, g, b = src[x, y][:3]
                    if not is_pale(r, g, b):
                        continue
                    nb = 0
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < w and 0 <= ny < h and alpha[ny * w + nx] == 0:
                                nb += 1
                    if nb >= 5:
                        doomed.append(i)
            for i in doomed:
                alpha[i] = 0
                changed += 1
            if not changed:
                break

    out = Image.new('RGBA', (w, h))
    opx = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b = src[x, y][:3]
            opx[x, y] = (r, g, b, alpha[y * w + x])
    out = out.crop(out.getbbox())
    r, g, b, a = out.split()
    a = a.filter(ImageFilter.GaussianBlur(0.7))
    return Image.merge('RGBA', (r, g, b, a))


if __name__ == '__main__':
    for cell in CELLS:
        img = cutout(SHEETS[cell[0]], cell)
        img.save(os.path.join(OUT, cell[1] + '.png'))
        print(cell[1], img.size)
    print('total', len(CELLS))
