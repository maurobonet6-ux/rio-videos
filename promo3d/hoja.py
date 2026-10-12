# Hoja de miniaturas para revisar un render: python3.11 promo3d/hoja.py DIR SALIDA.png [ancho_miniatura] [columnas]
import sys, glob, os
from PIL import Image, ImageDraw
fs = sorted(glob.glob(os.path.join(sys.argv[1], 'f*.png')))
w = int(sys.argv[3]) if len(sys.argv) > 3 else 120; cols = int(sys.argv[4]) if len(sys.argv) > 4 else 13
h = round(w * 16 / 9); filas = (len(fs) + cols - 1) // cols
hoja = Image.new('RGB', (cols * w, filas * h), (40, 40, 40)); d = ImageDraw.Draw(hoja)
for i, f in enumerate(fs):
    x, y = (i % cols) * w, (i // cols) * h
    hoja.paste(Image.open(f).convert('RGB').resize((w, h)), (x, y)); d.text((x + 3, y + 2), os.path.basename(f)[1:5], fill=(255, 255, 0))
hoja.save(sys.argv[2])
