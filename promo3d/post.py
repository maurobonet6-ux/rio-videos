# Posproducción del vídeo promocional (versión 2): subtítulos palabra a palabra sincronizados con la voz (palabras clave
# en rojo), y al final logo + «Empieza gratis» + riopoker.es. Viñeta y grano. Tiempos en guion.py.
# Uso: python3.11 promo3d/post.py FOTOGRAMAS_DIR SALIDA_DIR [--ancho 1080] [--desde 1] [--hasta 720]  → SALIDA_DIR/p0001.png …
import os, sys, json, random, argparse, math
import numpy as np
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
        n0 = len(out)
        if vid not in G.SUBTITULOS: continue
        dichas = json.load(open(os.path.join(AQUI, 'voz', vid + '.json')))['palabras']
        escritas = G.SUBTITULOS[vid].split()
        if G.ANUNCIO and i_ == 0:                        # anuncio: las primeras palabras ya están en el gancho grande
            dichas, escritas = dichas[G.GANCHO_PALABRAS:], escritas[G.GANCHO_PALABRAS:]
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
        out[-1] = out[-1] + [('', fin)]
        for g_ in out[n0:]: POS_Y[id(g_)] = G.SUB_Y.get(vid, 0.125) if G.ANUNCIO else 0.125                  # marca el final de la frase
    return out
POS_Y = {}
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
        x = (W - total) / 2; cy = H * POS_Y.get(id(tr), 0.125)
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
            if color == ROJO:                            # brillo rojo suave detrás de las palabras clave
                lienzo.paste(ROJO, (0, 0), capa.filter(ImageFilter.GaussianBlur(W * 0.028)).point(lambda p: int(p * 0.55)))
            borde = capa.filter(ImageFilter.MaxFilter(5))
            lienzo.paste((10, 10, 12), (0, 0), borde)
            lienzo.paste(color, (0, 0), capa)
            x += aw + esp

# ---------- textos grandes con desenfoque (marca y final) ----------
def letras(d, xy, t, fnt, fill, trk):
    """Escribe t letra a letra con trk px de más entre letras (interletrado). Devuelve el ancho."""
    x, y = xy
    for i, ch in enumerate(t):
        if d is not None: d.text((x, y), ch, font=fnt, fill=fill)
        x += d0.textlength(ch, font=fnt) + (trk if i < len(t) - 1 else 0)
    return x - xy[0]
d0 = ImageDraw.Draw(Image.new('L', (1, 1)))

def texto(lienzo, t, cy, tam, f, ini, fin=None, fuente=BLACK, color=BLANCO, acento=None, entra=14, desenfoque=0.04, sube=0.0, trk=0.06):
    t_in = suave((f - ini) / entra)
    t_out = suave((fin - f) / 7) if fin is not None and f > fin - 7 else 1
    vis = t_in * t_out
    if vis <= 0: return
    fnt = ImageFont.truetype(fuente, max(8, int(W * tam * (1.0 + 0.12 * (1 - t_in)))))
    capa = Image.new('L', (W, H)); d = ImageDraw.Draw(capa)
    bb = d.textbbox((0, 0), t, font=fnt); tr = fnt.size * trk     # interletrado: un 6 % del cuerpo
    x = (W - letras(None, (0, 0), t, fnt, 0, tr)) / 2 - bb[0]; y = H * cy - (bb[1] + bb[3]) / 2 + (1 - t_in) * W * sube
    letras(d, (x, y), t, fnt, int(255 * vis), tr)
    tilde = None
    if acento and 'Í' in t:
        m2 = Image.new('L', (W, H)); letras(ImageDraw.Draw(m2), (x, y), t.replace('Í', 'I'), fnt, int(255 * vis), tr)
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

# ---------- anuncio: gancho grande, barra de progreso, destellos y golpes de zoom en los cortes, rótulo de voz/historial ----------
def linea_grande(lienzo, texto_, cy, tam, k):
    """Una línea de palabras (rojas entre *asteriscos*) centrada, con el estilo de los subtítulos y brillo rojo."""
    trozos_ = [(t.replace('*', ''), ROJO if '*' in t else BLANCO) for t in texto_.split()]
    fnt = ImageFont.truetype(BLACK, tam); d = ImageDraw.Draw(lienzo); esp = d.textlength(' ', font=fnt)
    anchos = [d.textlength(t, font=fnt) for t, _ in trozos_]; total = sum(anchos) + esp * (len(trozos_) - 1)
    if total > W * 0.9: return linea_grande(lienzo, texto_, cy, int(tam * W * 0.9 / total), k)
    x = (W - total) / 2
    for (t, color), aw in zip(trozos_, anchos):
        fw = ImageFont.truetype(BLACK, max(8, int(tam * (1 + 0.25 * (1 - k))))); ww = d.textlength(t, font=fw); bb = d.textbbox((0, 0), t, font=fw)
        capa = Image.new('L', (W, H)); ImageDraw.Draw(capa).text((x + aw / 2 - ww / 2, cy - (bb[1] + bb[3]) / 2), t, font=fw, fill=int(255 * k))
        if k < 1: capa = capa.filter(ImageFilter.GaussianBlur(W * 0.02 * (1 - k)))
        lienzo.paste((0, 0, 0), (0, 0), capa.filter(ImageFilter.GaussianBlur(W * 0.012)).point(lambda p: min(255, int(p * 1.3))))
        if color == ROJO: lienzo.paste(ROJO, (0, 0), capa.filter(ImageFilter.GaussianBlur(W * 0.03)).point(lambda p: int(p * 0.6)))
        lienzo.paste((10, 10, 12), (0, 0), capa.filter(ImageFilter.MaxFilter(5)))
        lienzo.paste(color, (0, 0), capa); x += aw + esp

def fin_gancho():
    dichas = json.load(open(os.path.join(AQUI, 'voz', G.VOZ[0][0] + '.json')))['palabras']
    return G.VOZ[0][2] + dichas[G.GANCHO_PALABRAS][1] * G.FPS - 2      # justo cuando empieza «Compruébalo»

def gancho(lienzo, f):
    """El gancho entero y grande desde el primer fotograma (sin intro); late un poco y se va con desenfoque."""
    fin = fin_gancho()
    if f > fin: return
    k = suave((fin - f) / 5); n = len(G.GANCHO); tam = int(W * 0.112 * (1 + 0.015 * math.sin(f / 4)))
    for j, l in enumerate(G.GANCHO): linea_grande(lienzo, l, H * (0.13 + (j - (n - 1) / 2) * 0.07), tam, k)

def golpe(im, f):
    """Golpe de zoom (1,06 → 1) y destello blanco en los cortes y momentos clave."""
    for g in G.GOLPES + G.CORTES:
        t = f - g
        if 0 <= t < 8:
            e = 1 + 0.06 * (1 - suave(t / 8)); w2, h2 = int(W * e), int(H * e)
            im = im.resize((w2, h2), Image.BICUBIC).crop(((w2 - W) // 2, (h2 - H) // 2, (w2 - W) // 2 + W, (h2 - H) // 2 + H))
        if 0 <= t < 5 and (g in G.CORTES or g == G.GOLPES[0]):
            im = Image.blend(im, Image.new('RGB', (W, H), (255, 244, 240)), 0.5 * (1 - t / 5))
    return im

def progreso(lienzo, f):
    """Barra fina de progreso arriba (las barras de progreso hacen que la gente aguante hasta el final)."""
    d = ImageDraw.Draw(lienzo); alto = max(2, round(W * 0.006)); y = round(H * 0.012)
    d.rectangle((0, y, W, y + alto), fill=(60, 60, 64)); d.rectangle((0, y, W * f / G.TOTAL, y + alto), fill=ROJO)

def icono_micro(d, cx, cy, s, col):
    d.rounded_rectangle((cx - s * 0.22, cy - s * 0.5, cx + s * 0.22, cy + s * 0.12), radius=s * 0.22, fill=col)
    d.arc((cx - s * 0.38, cy - s * 0.25, cx + s * 0.38, cy + s * 0.3), 0, 180, fill=col, width=max(2, int(s * 0.09)))
    d.line((cx, cy + s * 0.3, cx, cy + s * 0.48), fill=col, width=max(2, int(s * 0.09)))
def icono_texto(d, cx, cy, s, col):
    d.rounded_rectangle((cx - s * 0.36, cy - s * 0.46, cx + s * 0.36, cy + s * 0.46), radius=s * 0.1, outline=col, width=max(2, int(s * 0.09)))
    for i in range(3): d.line((cx - s * 0.2, cy - s * 0.2 + i * s * 0.2, cx + s * (0.2 if i < 2 else 0.05), cy - s * 0.2 + i * s * 0.2), fill=col, width=max(2, int(s * 0.08)))

def rotulo(lienzo, f):
    """«o por voz» · «o pega tu historial»: dos pastillas con icono que entran una tras otra."""
    a, b = G.ROTULO
    for i, (t, icono) in enumerate((('o por voz', icono_micro), ('o pega tu historial', icono_texto))):
        k = suave((f - a - i * 6) / 7) * suave((b - f) / 6)
        if k <= 0: continue
        fnt = ImageFont.truetype(BOLD, int(W * 0.05)); d = ImageDraw.Draw(lienzo); tw = d.textlength(t, font=fnt)
        s_ = W * 0.055; pw = tw + s_ * 1.9 + W * 0.07; ph = W * 0.1
        x0 = (W - pw) / 2 + (1 - k) * W * (0.12 if i == 0 else -0.12); y0 = H * (0.62 + i * 0.075)
        caja = Image.new('L', (W, H)); ImageDraw.Draw(caja).rounded_rectangle((x0, y0, x0 + pw, y0 + ph), radius=ph / 2, fill=int(235 * k))
        lienzo.paste((0, 0, 0), (0, 0), caja.filter(ImageFilter.GaussianBlur(W * 0.02)).point(lambda p: int(p * 0.6)))
        lienzo.paste((22, 22, 26), (0, 0), caja)
        capa = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dc = ImageDraw.Draw(capa)
        icono(dc, x0 + W * 0.035 + s_ * 0.6, y0 + ph / 2, s_, ROJO + (int(255 * k),))
        bb = dc.textbbox((0, 0), t, font=fnt); dc.text((x0 + W * 0.035 + s_ * 1.5, y0 + ph / 2 - (bb[1] + bb[3]) / 2), t, font=fnt, fill=BLANCO + (int(255 * k),))
        lienzo.paste(capa, (0, 0), capa)

def vineta():
    v = Image.radial_gradient('L').resize((W, H))
    return v.point(lambda p: int(255 - 120 * (p / 255) ** 2))
V = Image.merge('RGB', [vineta()] * 3)
ARRIBA_OSC = Image.linear_gradient('L').resize((W, H)).point(lambda p: int(255 * (0.35 + 0.65 * min(1, p / 255 / 0.55))))   # oscurece la parte de arriba
random.seed(1)
ruido = [Image.effect_noise((W, H), 18) for _ in range(6)]       # grano fino a resolución completa
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
R2 = (((xx - W / 2) / (W / 2)) ** 2 * 0.5 + ((yy - H / 2) / (H / 2)) ** 2 * 0.5)[..., None]   # 0 en el centro, ~1 en las esquinas

def etalonaje(im):
    """Look de cine: negros con un punto rojo, altas luces cálidas y aberración cromática mínima en los bordes."""
    a = np.asarray(im).astype(np.float32) / 255
    lum = (a @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    a = a + (1 - lum) ** 4 * np.array([0.022, 0.0, 0.006], np.float32)                 # sombras: punto rojo
    a = a * (1 + lum ** 2 * np.array([0.03, 0.0, -0.035], np.float32))                # luces: cálidas
    desp = max(1, round(W / 900))                                                       # aberración: 1-2 px en las esquinas
    r = np.roll(a[..., 0], -desp, axis=1); b = np.roll(a[..., 2], desp, axis=1)
    k = np.clip(R2[..., 0] - 0.35, 0, 1) / 0.65
    a[..., 0] = a[..., 0] * (1 - k) + r * k; a[..., 2] = a[..., 2] * (1 - k) + b * k
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))
for f in range(args.desde, args.hasta + 1):
    ruta = os.path.join(args.dir, f'f{f:04d}.png')
    if not os.path.exists(ruta): continue
    im = Image.open(ruta).convert('RGB').resize((W, H), Image.LANCZOS)
    k = suave((f - (G.LOGO - 10)) / 20)                  # final: la parte de arriba se oscurece para el logo
    if k > 0: im = Image.composite(im, ImageChops.multiply(im, Image.merge('RGB', [ARRIBA_OSC] * 3)), Image.new('L', (W, H), int(255 * (1 - k))))
    im = ImageChops.multiply(im, V)
    im = etalonaje(im)
    if G.ANUNCIO: im = golpe(im, f); gancho(im, f); rotulo(im, f)
    subtitulo(im, f)
    texto(im, 'RÍO', 0.15, 0.27, f, G.LOGO, acento=ROJO, entra=16, desenfoque=0.06, trk=0.1)
    texto(im, 'Empieza gratis', 0.255, 0.095, f, G.ESLOGAN, sube=0.02, trk=0.025)
    pastilla(im, 'enlace en el perfil' if G.TIKTOK else 'riopoker.es', 0.335, 0.062 if G.TIKTOK else 0.07, f, G.WEB)
    if G.TIKTOK: aviso(im)
    if G.ANUNCIO: progreso(im, f)
    g = ruido[f % len(ruido)]
    im = Image.blend(im, ImageChops.overlay(im, Image.merge('RGB', [g] * 3)), 0.06)
    im.save(os.path.join(args.out, f'p{f:04d}.png'))
print('post ok', args.desde, args.hasta)
