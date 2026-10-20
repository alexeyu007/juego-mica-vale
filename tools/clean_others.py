"""Limpieza de los sprites que no son bebés (virus, UI, cuna, efectos simples).
Aplica: recuperar coloreados -> endurecer alfa -> quitar fringe blanco ->
cortar fragmentos vecinos a izquierda/derecha."""
import os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from clean import (SPR, restore_colored, harden, defringe, valley_cut, clean)

ARCHIVOS = [
    'virus_normal', 'virus_enojado', 'virus_sorprendido', 'virus_triste',
    'virus_baba', 'virus_grande', 'virus_pequeno', 'virus2_rojo',
    'corazon', 'corazon_gris', 'estrella_ui', 'ui_pausa2', 'patito_ui',
    'vida_extra', 'cuna_mica', 'cuna_vale', 'fx_lluvia', 'fx_moquito',
]


def proceso(name):
    p = os.path.join(SPR, name + '.png')
    a = np.asarray(Image.open(p).convert('RGBA')).copy()
    notas = []
    a, n = restore_colored(a)
    if n: notas.append(f'recupero={n}')
    a, n = harden(a)
    if n: notas.append(f'opaco={n}')
    a, n = defringe(a)
    if n: notas.append(f'fringe={n}')
    for side in ('left', 'right'):
        r = valley_cut(a, side)
        if r is not None:
            a = r
            notas.append(f'corte_{side}')
    out = Image.fromarray(a)
    bb = out.getbbox()
    if bb:
        out = out.crop(bb)
    out.save(p)
    return out.size, notas


if __name__ == '__main__':
    names = sys.argv[1:] or ARCHIVOS
    for name in names:
        size, notas = proceso(name)
        print(f'{name:22s} -> {str(size):12s} {" ".join(notas)}')
    # la etiqueta de texto de vida_extra se elimina con la limpieza por tiras
    print()
    print(clean(os.path.join(SPR, 'vida_extra.png'))[0].size)
