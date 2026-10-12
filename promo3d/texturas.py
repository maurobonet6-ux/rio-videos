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
CW, CH = 945, 1320                       # proporción de una carta de póker (63 x 88 mm)
SERIF = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
PAPEL = (250, 248, 243)
# Posición de los palos en las cartas de número, como en una baraja de verdad (x, y en fracción de la carta)
L, C, R = 0.31, 0.5, 0.69
PIPS = {2: [(C, .2), (C, .8)], 3: [(C, .2), (C, .5), (C, .8)], 4: [(L, .2), (R, .2), (L, .8), (R, .8)],
        5: [(L, .2), (R, .2), (C, .5), (L, .8), (R, .8)], 6: [(L, .2), (R, .2), (L, .5), (R, .5), (L, .8), (R, .8)],
        7: [(L, .2), (R, .2), (C, .35), (L, .5), (R, .5), (L, .8), (R, .8)],
        8: [(L, .2), (R, .2), (C, .35), (L, .5), (R, .5), (C, .65), (L, .8), (R, .8)],
        9: [(L, .2), (R, .2), (L, .4), (R, .4), (C, .5), (L, .6), (R, .6), (L, .8), (R, .8)],
        10: [(L, .2), (R, .2), (C, .3), (L, .4), (R, .4), (L, .6), (R, .6), (C, .7), (L, .8), (R, .8)]}

def papel():
    im = Image.new('RGB', (CW, CH), PAPEL)
    ruido = Image.effect_noise((CW, CH), 6).point(lambda p: p - 128 + 128)
    return Image.blend(im, Image.merge('RGB', [ruido] * 3), 0.035)

def palo(im, sim, col, cx, cy, tam, girar=False):
    """Un palo centrado en (cx, cy); girado 180° si está en la mitad de abajo."""
    f = ImageFont.truetype(DEJAVU, tam); capa = Image.new('L', (tam * 2, tam * 2)); d = ImageDraw.Draw(capa)
    bb = d.textbbox((0, 0), sim, font=f); d.text((tam - (bb[0] + bb[2]) / 2, tam - (bb[1] + bb[3]) / 2), sim, font=f, fill=255)
    if girar: capa = capa.rotate(180)
    im.paste(col, (int(cx - tam), int(cy - tam)), capa)

def indice(im, v, sim, col):
    """Índices de las esquinas (valor y palo pequeño), arriba a la izquierda y, girados, abajo a la derecha."""
    capa = Image.new('RGBA', (CW, CH)); d = ImageDraw.Draw(capa)
    f = ImageFont.truetype(SERIF, 118 if len(v) == 1 else 100)
    bb = d.textbbox((0, 0), v, font=f); cx = 92
    d.text((cx - (bb[0] + bb[2]) / 2, 52 - bb[1]), v, font=f, fill=col)
    palo(capa, sim, col, cx, 52 + (bb[3] - bb[1]) + 62, 70)
    im.paste(capa, (0, 0), capa); r = capa.rotate(180); im.paste(r, (0, 0), r)

def carta(c):
    im = papel(); d = ImageDraw.Draw(im)
    v = '10' if c[0] == 'T' else c[0]; sim, col = PALOS[c[1]]
    indice(im, v, sim, col)
    if v == 'A':
        palo(im, sim, col, CW / 2, CH / 2, 300 if c[1] != 's' else 380)
    elif v in 'JQK':                                    # figura: marco con la letra a doble cabeza, como en las barajas clásicas
        x0, y0, x1, y1 = CW * 0.2, CH * 0.13, CW * 0.8, CH * 0.87
        d.rectangle((x0, y0, x1, y1), outline=col, width=6); d.rectangle((x0 + 16, y0 + 16, x1 - 16, y1 - 16), outline=col, width=2)
        mitad = Image.new('RGBA', (int(x1 - x0), int((y1 - y0) / 2))); dm = ImageDraw.Draw(mitad)
        f = ImageFont.truetype(SERIF, 300); bb = dm.textbbox((0, 0), v, font=f)
        dm.text(((mitad.width - (bb[0] + bb[2])) / 2, mitad.height * 0.56 - (bb[1] + bb[3]) / 2), v, font=f, fill=col)
        if v == 'K':                                    # corona sencilla
            cx, base = mitad.width / 2, mitad.height * 0.2
            dm.polygon([(cx - 90, base + 40), (cx - 90, base - 20), (cx - 45, base + 15), (cx, base - 45), (cx + 45, base + 15), (cx + 90, base - 20), (cx + 90, base + 40)], fill=(201, 162, 39))
        palo(mitad, sim, col, 70, mitad.height * 0.2, 60)
        im.paste(mitad, (int(x0), int(y0)), mitad); m2 = mitad.rotate(180); im.paste(m2, (int(x0), int(y0 + mitad.height)), m2)
        d.line((x0 + 30, CH / 2, x1 - 30, CH / 2), fill=col, width=3)
    else:
        for x, y in PIPS[int(v)]: palo(im, sim, col, CW * x, CH * y, 128, girar=y > 0.5)
    im.save(os.path.join(OUT, f'carta_{c}.png'))

def dorso():
    """Dorso elegante: rombos finos granates, borde blanco y la marca pequeña en el centro."""
    im = Image.new('RGB', (CW, CH), PAPEL); d = ImageDraw.Draw(im)
    m = 48; dib = Image.new('RGB', (CW, CH), (118, 12, 28)); dd = ImageDraw.Draw(dib)
    for i in range(-CH, CW + CH, 30):
        dd.line((i, 0, i + CH, CH), fill=(150, 30, 46), width=3); dd.line((i, 0, i - CH, CH), fill=(150, 30, 46), width=3)
    mk = Image.new('L', (CW, CH)); ImageDraw.Draw(mk).rounded_rectangle((m, m, CW - m, CH - m), 30, fill=255)
    im.paste(dib, (0, 0), mk)
    d.rounded_rectangle((m + 18, m + 18, CW - m - 18, CH - m - 18), 22, outline=(230, 200, 205), width=3)
    r = 120; d.ellipse((CW / 2 - r, CH / 2 - r, CW / 2 + r, CH / 2 + r), fill=(118, 12, 28), outline=(230, 200, 205), width=4)
    marca(im, CW / 2, CH / 2, 74, PAPEL, (229, 48, 74))
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
