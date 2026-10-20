"""Dibuja las cajas CELLS sobre la hoja fuente para revisar recortes."""
import os, sys
from PIL import Image, ImageDraw
import extract

sheet_name = sys.argv[1] if len(sys.argv) > 1 else 'p'
names = sys.argv[2:]
sheet = extract.SHEETS[sheet_name].convert('RGB')
d = ImageDraw.Draw(sheet)
for cell in extract.CELLS:
    if cell[0] != sheet_name:
        continue
    x0, y0, x1, y1 = cell[2:6]
    col = (255, 0, 0) if (not names or cell[1] in names) else (0, 160, 255)
    d.rectangle([x0, y0, x1, y1], outline=col, width=2)
    if names and cell[1] in names:
        d.text((x0 + 2, y0 - 12), cell[1], fill=(255, 0, 0))
sheet.save(os.path.join(os.path.dirname(__file__), '_sheet_' + sheet_name + '.png'))
print('ok')
