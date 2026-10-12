# Posproducción del vídeo promocional (versión 2): subtítulos palabra a palabra sincronizados con la voz (palabras clave
# en rojo), y al final logo + «Empieza gratis» + riopoker.es. Viñeta y grano. Tiempos en guion.py.
# Uso: python3.11 promo3d/post.py FOTOGRAMAS_DIR SALIDA_DIR [--ancho 1080] [--desde 1] [--hasta 720]  → SALIDA_DIR/p0001.png …
import os, sys, json, random, argparse
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import guion as G

BLACK = '/usr/share/fonts/opentype/inter/InterDisplay-Black.otf'
BOLD = '/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf'
SEMI = '/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf'
BLANCO = (245, 245, 247); ROJO = (229, 48, 74)

a = argparse.ArgumentParser(); a.add_argument('dir'); a.add_argument('out'); a.add_argument('--ancho', type=int, default=1080)
a.add_argument('--desde', type=int, default=1); a.add_argument('--hasta', type=int, default=G.TOTAL)
args = a.parse_args()
W = args.ancho; H = round(W * 16 / 9)
os.makedirs(args.out, exist_ok=True)

def suave(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3

# ---------- subtítulos: trozos de hasta 3 palabras; cada palabra aparece cuando se dice ----------
def trozos():
    out = []
    for i_, (vid, _, f0) in enumerate(G.VOZ):
        if vid not in G.SUBTITULOS: continue
        dichas = json.load(open(os.path.join(AQUI, 'voz', vid + '.json')))['palabras']
        escritas = G.SUBTITULOS[vid].split()
        if len(escritas) == len(dichas): tiempos = [f0 + s * G.FPS for _, s, _ in dichas]
        else:                                            # si no cuadran, se reparten a lo largo de la frase
            dur = dichas[-1][2]; tiempos = [f0 + i * dur / len(escritas) * G.FPS for i in range(len(escritas))]
        fin = f0 + dichas[-1][2] * G.FPS + 6
        if i_ + 1 < len(G.VOZ): fin = min(fin, G.VOZ[i_ + 1][2] - 1)   # no pisa la frase siguiente
        grupo = []
        for w, t in zip(escritas, tiempos):
            if grupo and (len(grupo) == 3 or sum(len(x) for x, _ in grupo) + len(w) > 17): out.append(grupo); grupo = []
            grupo.append((w, t))
        out.append(grupo)
        out[-1] = out[-1] + [('', fin)]                  # marca el final de la frase
    return out
TROZOS = trozos()

def subtitulo(lienzo, f):
    for i, tr in enumerate(TROZOS):
        palabras = [(w, t) for w, t in tr if w]
        ini = palabras[0][1]
        fin = tr[-1][1] if tr[-1][0] == '' else (TROZOS[i + 1][0][1] if i + 1 < len(TROZOS) else ini + 60)
        if not (ini - 1 <= f < fin): continue
        tam = int(W * 0.088); fnt = ImageFont.truetype(BLACK, tam)
        d = ImageDraw.Draw(lienzo)
        esp = d.textlength(' ', font=fnt)
        anchos = [d.textlength(w, font=fnt) for w, _ in palabras]
        total = sum(anchos) + esp * (len(palabras) - 1)
        if total > W * 0.92:                             # si no cabe, más pequeño
            tam = int(tam * W * 0.92 / total); fnt = ImageFont.truetype(BLACK, tam)
            esp = d.textlength(' ', font=fnt); anchos = [d.textlength(w, font=fnt) for w, _ in palabras]; total = sum(anchos) + esp * (len(palabras) - 1)
        x = (W - total) / 2; cy = H * 0.125
        for (w, t), aw in zip(palabras, anchos):
            k = (f - t) / 5
            if k < 0: x += aw + esp; continue
            k = suave(k); esc = 1.0 + 0.35 * (1 - k)
            fw = ImageFont.truetype(BLACK, max(8, int(tam * esc)))
            ww = d.textlength(w, font=fw); bb = d.textbbox((0, 0), w, font=fw)
            px = x + aw / 2 - ww / 2; py = cy - (bb[1] + bb[3]) / 2
            color = ROJO if w in G.ROJAS else BLANCO
            capa = Image.new('L', (W, H)); ImageDraw.Draw(capa).text((px, py), w, font=fw, fill=int(255 * min(1, k * 1.5)))
            sombra = capa.filter(ImageFilter.GaussianBlur(W * 0.01))
            lienzo.paste((0, 0, 0), (0, 0), sombra.point(lambda p: min(255, int(p * 1.3))))
            borde = capa.filter(ImageFilter.MaxFilter(5))
            lienzo.paste((10, 10, 12), (0, 0), borde)
            lienzo.paste(color, (0, 0), capa)
            x += aw + esp

# ---------- textos grandes con desenfoque (marca y final) ----------
def texto(lienzo, t, cy, tam, f, ini, fin=None, fuente=BLACK, color=BLANCO, acento=None, entra=14, desenfoque=0.04, sube=0.0):
    t_in = suave((f - ini) / entra)
    t_out = suave((fin - f) / 7) if fin is not None and f > fin - 7 else 1
    vis = t_in * t_out
    if vis <= 0: return
    fnt = ImageFont.truetype(fuente, max(8, int(W * tam * (1.0 + 0.12 * (1 - t_in)))))
    capa = Image.new('L', (W, H)); d = ImageDraw.Draw(capa)
    bb = d.textbbox((0, 0), t, font=fnt)
    x = (W - (bb[2] - bb[0])) / 2 - bb[0]; y = H * cy - (bb[1] + bb[3]) / 2 + (1 - t_in) * W * sube
    d.text((x, y), t, font=fnt, fill=int(255 * vis))
    tilde = None
    if acento and 'Í' in t:
        m2 = Image.new('L', (W, H)); ImageDraw.Draw(m2).text((x, y), t.replace('Í', 'I'), font=fnt, fill=int(255 * vis))
        tilde = ImageChops.subtract(capa, m2); capa = ImageChops.subtract(capa, tilde)
    radio = W * desenfoque * (1 - t_in) + W * 0.02 * (1 - t_out)
    if radio > 0.3:
        capa = capa.filter(ImageFilter.GaussianBlur(radio))
        if tilde: tilde = tilde.filter(ImageFilter.GaussianBlur(radio))
    sombra = capa.filter(ImageFilter.GaussianBlur(W * 0.014)).point(lambda p: int(p * 0.8))
    lienzo.paste((0, 0, 0), (0, 0), sombra)
    lienzo.paste(color, (0, 0), capa)
    if tilde: lienzo.paste(acento, (0, 0), tilde)

def pastilla(lienzo, t, cy, tam, f, ini):
    """«riopoker.es» en una pastilla roja que late suavemente."""
    k = suave((f - ini) / 10)
    if k <= 0: return
    late = 1 + 0.03 * max(0, 1 - ((f - ini - 30) % 45) / 12) if f > ini + 30 else 1
    fnt = ImageFont.truetype(BOLD, int(W * tam * late)); d = ImageDraw.Draw(lienzo)
    bb = d.textbbox((0, 0), t, font=fnt); tw, th = bb[2] - bb[0], bb[3] - bb[1]
    px, py = W * 0.06 * late, W * 0.035 * late
    caja = Image.new('L', (W, H)); dc = ImageDraw.Draw(caja)
    x0 = (W - tw) / 2 - px; y0 = H * cy - th / 2 - py + (1 - k) * W * 0.04
    dc.rounded_rectangle((x0, y0, x0 + tw + 2 * px, y0 + th + 2 * py), radius=(th + 2 * py) / 2, fill=int(255 * k))
    lienzo.paste((0, 0, 0), (0, 0), caja.filter(ImageFilter.GaussianBlur(W * 0.02)).point(lambda p: int(p * 0.6)))
    lienzo.paste(ROJO, (0, 0), caja)
    m = Image.new('L', (W, H)); ImageDraw.Draw(m).text((x0 + px - bb[0], y0 + py - bb[1]), t, font=fnt, fill=int(255 * k))
    lienzo.paste(BLANCO, (0, 0), m)

def aviso(lienzo):
    """TikTok: aviso fijo «EDUCACIÓN · sin dinero real» arriba a la izquierda."""
    fnt = ImageFont.truetype(BOLD, int(W * 0.03)); d = ImageDraw.Draw(lienzo); t = 'EDUCACIÓN · sin dinero real'
    bb = d.textbbox((0, 0), t, font=fnt); px, py = W * 0.022, W * 0.012; x0, y0 = W * 0.04, H * 0.035
    caja = Image.new('L', (W, H)); ImageDraw.Draw(caja).rounded_rectangle((x0, y0, x0 + bb[2] - bb[0] + 2 * px, y0 + bb[3] - bb[1] + 2 * py), radius=W * 0.02, fill=150)
    lienzo.paste((12, 12, 14), (0, 0), caja)
    d.text((x0 + px - bb[0], y0 + py - bb[1]), t, font=fnt, fill=(235, 235, 240))

def vineta():
    v = Image.radial_gradient('L').resize((W, H))
    return v.point(lambda p: int(255 - 120 * (p / 255) ** 2))
V = Image.merge('RGB', [vineta()] * 3)
ARRIBA_OSC = Image.linear_gradient('L').resize((W, H)).point(lambda p: int(255 * (0.35 + 0.65 * min(1, p / 255 / 0.55))))   # oscurece la parte de arriba
random.seed(1)
ruido = [Image.effect_noise((W // 2, H // 2), 22).resize((W, H)) for _ in range(6)]
for f in range(args.desde, args.hasta + 1):
    ruta = os.path.join(args.dir, f'f{f:04d}.png')
    if not os.path.exists(ruta): continue
    im = Image.open(ruta).convert('RGB').resize((W, H), Image.LANCZOS)
    k = suave((f - (G.LOGO - 10)) / 20)                  # final: la parte de arriba se oscurece para el logo
    if k > 0: im = Image.composite(im, ImageChops.multiply(im, Image.merge('RGB', [ARRIBA_OSC] * 3)), Image.new('L', (W, H), int(255 * (1 - k))))
    im = ImageChops.multiply(im, V)
    subtitulo(im, f)
    texto(im, 'RÍO', 0.15, 0.27, f, G.LOGO, acento=ROJO, entra=16, desenfoque=0.06)
    texto(im, 'Empieza gratis', 0.255, 0.095, f, G.ESLOGAN, sube=0.02)
    pastilla(im, 'enlace en el perfil' if G.TIKTOK else 'riopoker.es', 0.335, 0.062 if G.TIKTOK else 0.07, f, G.WEB)
    if G.TIKTOK: aviso(im)
    g = ruido[f % len(ruido)]
    im = Image.blend(im, ImageChops.overlay(im, Image.merge('RGB', [g] * 3)), 0.05)
    im.save(os.path.join(args.out, f'p{f:04d}.png'))
print('post ok', args.desde, args.hasta)
