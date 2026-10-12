# Texturas de la mesa: caras de las cartas, dorso con «RÍO» y fichas (sin valores). → salida/promo3d/tex/
import os
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(AQUI, '..', 'salida', 'promo3d', 'tex'); os.makedirs(OUT, exist_ok=True)
INTER = '/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf'
INTER_N = '/usr/share/fonts/opentype/inter/InterDisplay-Black.otf'
DEJAVU = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
ROJO = (229, 48, 74)
PALOS = {'h': ('♥', (214, 32, 58)), 'd': ('♦', (214, 32, 58)), 's': ('♠', (22, 22, 26)), 'c': ('♣', (22, 22, 26))}
CW, CH = 630, 880

def carta(c):
    im = Image.new('RGB', (CW, CH), (248, 246, 242)); d = ImageDraw.Draw(im)
    v = '10' if c[0] == 'T' else c[0]; sim, col = PALOS[c[1]]
    fv = ImageFont.truetype(INTER, 150); fs = ImageFont.truetype(DEJAVU, 120); fg = ImageFont.truetype(DEJAVU, 380)
    for rot in (0, 180):
        capa = Image.new('RGBA', (CW, CH)); dc = ImageDraw.Draw(capa)
        dc.text((58, 40), v, font=fv, fill=col); dc.text((62, 200), sim, font=fs, fill=col)
        capa = capa.rotate(rot); im.paste(capa, (0, 0), capa)
    bb = d.textbbox((0, 0), sim, font=fg)
    d.text(((CW - bb[2] - bb[0]) / 2, (CH - bb[3] - bb[1]) / 2), sim, font=fg, fill=col)
    im.save(os.path.join(OUT, f'carta_{c}.png'))

def dorso():
    im = Image.new('RGB', (CW, CH), (248, 246, 242)); d = ImageDraw.Draw(im)
    dib = Image.new('RGB', (CW, CH), (120, 12, 26)); dd = ImageDraw.Draw(dib)
    for i in range(-CH, CW + CH, 34):
        dd.line((i, 0, i + CH, CH), fill=(140, 22, 38), width=8)
        dd.line((i, 0, i - CH, CH), fill=(140, 22, 38), width=8)
    m = Image.new('L', (CW, CH)); ImageDraw.Draw(m).rounded_rectangle((34, 34, CW - 34, CH - 34), 36, fill=255)
    im.paste(dib, (0, 0), m)
    d.rounded_rectangle((34, 34, CW - 34, CH - 34), 36, outline=(248, 246, 242), width=10)
    marca(im, CW / 2, CH / 2, 150, (248, 246, 242), (248, 246, 242))
    im.save(os.path.join(OUT, 'dorso.png'))

def marca(im, cx, cy, tam, color, acento):
    """«RÍO» con la tilde de color (la marca)."""
    f = ImageFont.truetype(INTER_N, tam); d = ImageDraw.Draw(im)
    bb = d.textbbox((0, 0), 'RÍO', font=f); x = cx - (bb[2] + bb[0]) / 2; y = cy - (bb[3] + bb[1]) / 2
    d.text((x, y), 'RÍO', font=f, fill=color)
    m1 = Image.new('L', im.size); ImageDraw.Draw(m1).text((x, y), 'RÍO', font=f, fill=255)
    m2 = Image.new('L', im.size); ImageDraw.Draw(m2).text((x, y), 'RIO', font=f, fill=255)
    from PIL import ImageChops
    im.paste(acento, (0, 0), ImageChops.subtract(m1, m2))

def ficha(nombre, base, borde):
    S = 1024; im = Image.new('RGB', (S, S), base); d = ImageDraw.Draw(im); c = S / 2
    for i in range(8):                                  # marcas del canto
        import math
        a = i * math.pi / 4
        x, y = c + math.cos(a) * 455, c + math.sin(a) * 455
        p = Image.new('L', (S, S)); dp = ImageDraw.Draw(p)
        dp.rectangle((c - 40, 0, c + 40, 140), fill=255)
        p = p.rotate(-math.degrees(a) - 90, center=(c, c))
        im.paste(borde, (0, 0), p)
    d.ellipse((c - 330, c - 330, c + 330, c + 330), outline=borde, width=14)
    d.ellipse((c - 300, c - 300, c + 300, c + 300), fill=tuple(int(v * 0.85) for v in base))
    marca(im, c, c, 170, borde, (24, 24, 28) if base[0] > 150 and base[1] < 100 else ROJO)
    im.save(os.path.join(OUT, f'ficha_{nombre}.png'))

def sello():
    """Sello verde de «etapa superada» (sale de la pantalla en la carrera)."""
    S = 1024; im = Image.new('RGB', (S, S), (34, 197, 94)); d = ImageDraw.Draw(im)
    d.ellipse((40, 40, S - 40, S - 40), outline=(220, 252, 231), width=26)
    d.line((300, 530, 450, 680, 740, 360), fill=(255, 255, 255), width=110, joint='curve')
    for x, y in ((300, 530), (740, 360)): d.ellipse((x - 55, y - 55, x + 55, y + 55), fill=(255, 255, 255))
    im.save(os.path.join(OUT, 'sello.png'))

if __name__ == '__main__':
    for c in ('Ah', 'Kh', 'Qh', '8c', '3h', 'Js', 'Td', 'Jh', 'Th', '9h', '7h', 'As'): carta(c)
    sello()
    dorso()
    ficha('roja', (190, 24, 44), (245, 240, 235))
    ficha('negra', (24, 24, 28), (229, 48, 74))
    ficha('blanca', (232, 228, 222), (160, 18, 36))
    ficha('gris', (70, 72, 80), (240, 236, 230))
    print('texturas ok')
