"""Aplica cortes puntuales para quitar restos que los algoritmos genericos no
detectaron (tira superior de virus_normal, fragmento derecho de virus_grande)."""
import os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from clean import SPR

# nombre -> [(eje, desde, hasta)] en pixeles; se pone alfa a 0 en ese rango
CORTES = {
    'virus_normal': [('fila', 0, 9)],        # tira de etiqueta morada arriba
    'virus_grande': [('columna', 47, 94)],  # mitad de otro virus a la derecha
}

for name, cortes in CORTES.items():
    p = os.path.join(SPR, name + '.png')
    a = np.asarray(Image.open(p).convert('RGBA')).copy()
    for eje, d, h in cortes:
        if eje == 'fila':
            a[d:h, :, 3] = 0
        else:
            a[:, d:h, 3] = 0
    out = Image.fromarray(a)
    bb = out.getbbox()
    if bb:
        out = out.crop(bb)
    out.save(p)
    print(name, '->', out.size)
