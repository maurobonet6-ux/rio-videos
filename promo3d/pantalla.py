# Lo que se ve en la pantalla del móvil, fotograma a fotograma (capturas reales de la app + barra de estado + menú inferior),
# con desplazamientos (scroll), deslizamientos entre pantallas y el hueco que dejan las tarjetas que se despegan.
# Uso: python3.11 promo3d/pantalla.py [--desde 1] [--hasta 780]  → salida/promo3d/pantalla/s0001.jpg …
# escena.py lo importa para saber dónde están las tarjetas en la pantalla.
import os, json, argparse
from PIL import Image, ImageDraw, ImageFont
import guion as G

AQUI = os.path.dirname(os.path.abspath(__file__))
CAP = os.path.join(AQUI, '..', 'salida', 'promo3d')
OUT = os.path.join(CAP, 'pantalla' + ('_tiktok' if G.TIKTOK else ''))
SW, SH = 1200, 2580               # 400x860 @3x
BARRA = 132                       # barra de estado (44 pt)
VISTA = SH - BARRA                # alto visible de cada captura
SALIDA_ANCHO = 900                # tamaño de la textura que usa Blender
FONDO = (10, 10, 10)
FUENTE = '/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf'
NAV = {'inicio': 'analizar', 'mano1': 'analizar', 'mano': 'analizar', 'analisis': 'analizar',
       'carrera_a': 'carrera', 'carrera_b': 'carrera', 'aprender': 'aprender', 'progreso': 'progreso'}
INFO = json.load(open(os.path.join(CAP, 'capturas.json')))

# Tarjetas que se despegan: captura, caja en la captura (x, y, an, al) y desde cuándo falta en la pantalla
SCROLL_MAX = {'analisis': INFO['analisis']['alto'] - VISTA, 'carrera': 1650, 'progreso': 1000, 'aprender': 900}
TARJETAS = {
    'ganas':     ('analisis', INFO['analisis']['tarjeta'], G.DESPEGA_GANAS[0]),
    'correctas': ('progreso', INFO['progreso']['tarjeta'], G.DESPEGA_CORRECTAS[0]),
}

_cache = {}
def img(n):
    if n not in _cache: _cache[n] = Image.open(os.path.join(CAP, n + '.png')).convert('RGB')
    return _cache[n]


def barra_estado(d):
    f = ImageFont.truetype(FUENTE, 50)
    d.text((96, 40), '9:41', font=f, fill=(245, 245, 247))
    x = SW - 96                                       # batería, wifi y cobertura (de derecha a izquierda)
    d.rounded_rectangle((x - 74, 50, x, 86), 10, outline=(200, 200, 205), width=4)
    d.rounded_rectangle((x - 68, 56, x - 16, 80), 6, fill=(245, 245, 247))
    d.rounded_rectangle((x + 4, 61, x + 9, 75), 2, fill=(200, 200, 205))
    x -= 118
    for i, r in enumerate((14, 26, 38)):
        d.arc((x - r, 84 - r, x + r, 84 + r), 225, 315, fill=(245, 245, 247), width=7)
    d.ellipse((x - 5, 78, x + 5, 88), fill=(245, 245, 247))
    x -= 120
    for i in range(4):
        d.rounded_rectangle((x + i * 17, 84 - 10 - i * 8, x + i * 17 + 11, 86), 3, fill=(245, 245, 247))


def capa(nombre, scroll=0, sin=()):
    """Una pantalla completa: captura desplazada + barra de estado + menú inferior + huecos de tarjetas."""
    im = Image.new('RGB', (SW, SH), FONDO)
    src = img(nombre)
    scroll = int(max(0, min(scroll, src.height - VISTA)))
    im.paste(src.crop((0, scroll, SW, scroll + VISTA)), (0, BARRA))
    d = ImageDraw.Draw(im)
    for t in sin:                                     # hueco: la tarjeta ya no está
        cap, (x, y, w, h), _ = TARJETAS[t]
        if not nombre.startswith(cap): continue
        y += BARRA - scroll
        fondo = src.getpixel((x + 4, min(src.height - 1, y - BARRA + scroll + 4)))
        d.rounded_rectangle((x, y, x + w, y + h), 30, fill=tuple(int(c * 0.55) for c in fondo), outline=(46, 46, 52), width=3)
    d.rectangle((0, 0, SW, BARRA), fill=FONDO)
    barra_estado(d)
    if nombre in NAV:
        nav = img('nav_' + NAV[nombre]); im.paste(nav, (0, SH - nav.height))
    d.rounded_rectangle((SW / 2 - 200, SH - 30, SW / 2 + 200, SH - 16), 7, fill=(235, 235, 240))   # barra de inicio
    return im


def deslizar(a, b, t):
    """b entra desde la derecha y a se va un poco a la izquierda, oscureciéndose (como al navegar en el móvil)."""
    t = G.suave(t)
    im = Image.new('RGB', (SW, SH), FONDO)
    im.paste(Image.eval(a, lambda v: int(v * (1 - 0.5 * t))), (int(-SW * 0.3 * t), 0))
    im.paste(b, (int(SW * (1 - t)), 0))
    return im


def scroll_de(nombre, f, ab):
    return SCROLL_MAX[nombre] * G.tramo(f, ab)


def caja_pantalla(t):
    """Dónde está la tarjeta t en la pantalla (px de 1200x2580) justo antes de despegarse."""
    cap, (x, y, w, h), _ = TARJETAS[t]
    return x, y + BARRA, w, h


def fotograma(f):
    sin = [t for t, (_, _, desde) in TARJETAS.items() if f >= desde]
    mitad = lambda ab: sum(ab) // 2
    def desliza(a, b, ab): return deslizar(a, b, (f - ab[0]) / (ab[1] - ab[0]))
    if f < G.ENCIENDE: return Image.new('RGB', (SW, SH), (0, 0, 0))          # gancho: el móvil, apagado sobre la mesa
    if f < mitad(G.GIRO_INICIO):                                            # se enciende con el análisis
        im = capa('analisis'); k = min(1, (f - G.ENCIENDE) / 8)
        return im if k >= 1 else Image.eval(im, lambda v: int(v * k))
    if f < G.LLEGA_MANO1: return capa('inicio')
    if f < G.LLEGA_FLOP: return capa('mano1')
    if f < G.CORTE_ANALISIS: return capa('mano')
    if f < mitad(G.VUELTA_CARRERA): return capa('analisis', scroll_de('analisis', f, G.SCROLL_ANALISIS), sin)
    s_c = scroll_de('carrera', f, G.SCROLL_CARRERA)
    carrera = capa('carrera_a', s_c) if f < G.MARCA_ETAPA else Image.blend(capa('carrera_a', s_c), capa('carrera_b', s_c), min(1, (f - G.MARCA_ETAPA) / 4))
    if f < G.DESLIZA_PARTIDA[0]: return carrera
    quinta = capa('aprender', SCROLL_MAX['aprender'] * G.tramo(f, (410, 470))) if G.TIKTOK else capa('partida')
    if f <= G.DESLIZA_PARTIDA[1]: return desliza(carrera, quinta, G.DESLIZA_PARTIDA)
    if f < G.DESLIZA_PROGRESO[0]: return quinta
    prog = capa('progreso', scroll_de('progreso', f, G.SCROLL_PROGRESO), sin)
    if f <= G.DESLIZA_PROGRESO[1]: return desliza(capa('aprender', SCROLL_MAX['aprender']) if G.TIKTOK else capa('partida'), prog, G.DESLIZA_PROGRESO)
    if f < G.DESLIZA_FINAL[0]: return prog
    if f <= G.DESLIZA_FINAL[1]: return desliza(prog, capa('inicio'), G.DESLIZA_FINAL)
    return capa('inicio')


def recortes():
    """Texturas de las tarjetas que flotan: el mismo trozo de la captura."""
    for t, (cap, (x, y, w, h), _) in TARJETAS.items():
        r = img(cap).crop((x, y, x + w, y + h))
        ImageDraw.Draw(r).rounded_rectangle((3, 3, w - 4, h - 4), 34, outline=(229, 48, 74), width=7)   # borde rojo: se distingue al flotar
        r.save(os.path.join(CAP, f'tarjeta_{t}.png'))


def ruta(f): return os.path.join(OUT, f's{f:04d}.jpg')


if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('--desde', type=int, default=1); a.add_argument('--hasta', type=int, default=G.TOTAL)
    a.add_argument('--cada', type=int, default=1)
    args = a.parse_args()
    os.makedirs(OUT, exist_ok=True); recortes()
    alto = round(SALIDA_ANCHO * SH / SW)
    # (anuncio: cada fotograma usa la pantalla del instante de escena que le toca, G.orig)
    for f in sorted({round(G.orig(f)) for f in range(args.desde, args.hasta + 1, args.cada)}):
        fotograma(f).resize((SALIDA_ANCHO, alto), Image.LANCZOS).save(ruta(f), quality=90)
    print('pantalla ok', args.desde, args.hasta)
