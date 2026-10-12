# Guion del vídeo promocional 3D (versión 2): tiempos comunes a la escena (escena.py), la pantalla del móvil (pantalla.py),
# los subtítulos y el logo (post.py) y el sonido (audio.py). Fotogramas a 30 fps, empezando en 1.
FPS = 30
TOTAL = 720                       # 24 s
ESCENA_TOTAL = TOTAL              # la escena 3D siempre dura esto (el anuncio usa trozos de ella, ver más abajo)

# (nombre, primer fotograma, último fotograma)
ESCENAS = [
    ('gancho',   1,   108),       # 1. la mesa vacía: se enciende la lámpara, la cámara avanza a ras del fieltro; el móvil se enciende
    ('analiza',  109, 195),       # 2. el móvil gira: «Analiza tu mano»; las cartas de la mesa entran volando
    ('analisis', 196, 305),       # 3. la cámara atraviesa la pantalla; «Ganas 69%» se despega; salen las cartas que te ayudan
    ('carrera',  306, 392),       # 4. el móvil gira; la etapa 3 se marca y salta un sello verde
    ('partida',  393, 490),       # 5. el móvil se tumba en la mesa (plano cenital): partida de práctica
    ('progreso', 491, 585),       # 6. el móvil se levanta; «Decisiones correctas 82%» se despega
    ('final',    586, TOTAL),     # 7. logo, «Empieza gratis» y riopoker.es
]

# Voz (ElevenLabs, promo3d/voz.py): id, texto, fotograma en el que empieza
VOZ = [
    ('v1', 'Los mejores estudian antes de sentarse a la mesa.', 9),
    ('v2', 'Mete tu mano en Río en segundos.', 112),
    ('v3', 'Mira tus probabilidades y las cartas que te ayudan.', 200),
    ('v4', 'Avanza nivel a nivel en tu carrera.', 312),
    ('v5', 'Practica contra rivales con su propio estilo.', 398),
    ('v6', 'Y descubre tus errores para corregirlos.', 496),
    ('v7', 'Empieza gratis en río poker punto es.', 600),
]
# Subtítulos: lo que se lee para cada frase (mismas palabras que la voz, salvo cómo se escribe la marca) y las que van en rojo
SUBTITULOS = {
    'v1': 'Los mejores estudian antes de sentarse a la mesa.',
    'v2': 'Mete tu mano en RÍO en segundos.',
    'v3': 'Mira tus probabilidades y las cartas que te ayudan.',
    'v4': 'Avanza nivel a nivel en tu carrera.',
    'v5': 'Practica contra rivales con su propio estilo.',
    'v6': 'Y descubre tus errores para corregirlos.',
}
ROJAS = {'estudian', 'mesa.', 'mano?', 'RÍO', 'segundos.', 'probabilidades', 'ayudan.', 'nivel', 'carrera.', 'rivales', 'estilo.', 'errores', 'corregirlos.'}
LOGO = 590                        # el logo final empieza a enfocarse
ESLOGAN = 606                     # «Empieza gratis»
WEB = 622                         # «riopoker.es»

# Pantalla del móvil (pantalla.py)
MIRA_AS = (6, 16, 32, 42)         # el jugador levanta el borde del A♥ para mirarla (sube, arriba, baja)
MIRA_REY = (40, 50, 62, 72)       # y luego el del K♥
LAMPARA = 8                       # clic: la lámpara colgante de la mesa se enciende (con un parpadeo)
ENCIENDE = 70                     # la pantalla del móvil, apagado sobre la mesa, se enciende con el análisis
GIRO_INICIO = (96, 118)           # el móvil gira sobre sí mismo: del análisis (gancho) a «Analiza tu mano»
LLEGA_MANO1 = 150                 # llegan tus dos cartas
LLEGA_FLOP = 168                  # llega el flop
CORTE_ANALISIS = 198              # la cámara está «dentro» de la pantalla: cambio a análisis
DESPEGA_GANAS = (216, 236)        # la tarjeta «Ganas / Necesitas» sale de la pantalla
SCROLL_ANALISIS = (250, 280)
SALEN_OUTS = (270, 296)           # las cartas que te ayudan salen de la pantalla
VUELTA_CARRERA = (298, 318)       # el móvil gira; a mitad de vuelta, carrera
SCROLL_CARRERA = (320, 346)
MARCA_ETAPA = 356                 # la etapa 3 pasa a «Superada» (sello verde)
DESLIZA_PARTIDA = (386, 398)
DESLIZA_PROGRESO = (484, 496)
DESPEGA_CORRECTAS = (508, 528)
SCROLL_PROGRESO = (540, 570)
DESLIZA_FINAL = (586, 598)

# Efectos (promo3d/sonidos): (efecto, fotograma)
EFECTOS = [('interruptor', 7), ('pop', 70), ('whoosh', 84), ('whoosh', 96), ('cartas', 134), ('cartas', 154),
           ('whoosh2', 188), ('pop', 216), ('cartas', 268), ('whoosh', 296), ('logro', 356), ('whoosh', 384),
           ('fichas', 420), ('cartas', 440), ('whoosh', 482), ('pop', 508), ('whoosh', 578), ('golpe', 590), ('pop', 622)]



# ---------- Versión para TikTok (VARIANTE=tiktok) ----------
# TikTok quitó vídeos de RÍO por «bienes y servicios regulados» (lo ve como juego): esta versión no lleva mesa, cartas ni fichas,
# lleva el aviso «EDUCACIÓN», la escena 5 enseña Aprender en vez de la partida y el final no nombra la web.
import os as _os
TIKTOK = _os.environ.get('VARIANTE', '') in ('tiktok', 'anuncio_tiktok')
if TIKTOK:
    _cambia = {'v1': ('v1t', '¿Sabrías calcular tus probabilidades en cada mano?'),
               'v5': ('v5t', 'Aprende con guías, tablas y lecciones cortas.'),
               'v7': ('v7t', 'Empieza gratis. Enlace en el perfil.')}
    VOZ = [(_cambia[v][0], _cambia[v][1], f) if v in _cambia else (v, t, f) for v, t, f in VOZ]
    VOZ = [(v, t, 390 if v == 'v5t' else 14 if v == 'v1t' else f) for v, t, f in VOZ]   # «Aprende…» es más larga: empieza antes
    SUBTITULOS = {_cambia.get(k, (k,))[0]: (_cambia[k][1] if k in _cambia else t) for k, t in SUBTITULOS.items()}
    SUBTITULOS.pop('v7t', None)
    ROJAS = ROJAS | {'calcular', 'probabilidades', 'guías,', 'lecciones'}
    ENCIENDE = 10                                     # el móvil se enciende casi al empezar
    EFECTOS = [(n, f) for n, f in EFECTOS if n not in ('fichas', 'cartas', 'interruptor') and (n, f) != ('pop', 70)] + [('pop', 10)]

# ---------- Anuncio de Instagram «¿Jugaste bien tu última mano?» (VARIANTE=anuncio, ~18 s) ----------
# Usa trozos de la misma escena 3D con otra velocidad: MAPA dice, para fotogramas clave del anuncio, qué instante de la escena se ve.
# Dentro de cada tramo la velocidad cambia de forma suave (curva monótona por los puntos, sin tirones); entre tramos hay un corte
# con barrido (post.py). escena.py renderiza con subframes. Todos los tiempos se dan en tiempo de escena y se pasan al anuncio con ad().
ANUNCIO = _os.environ.get('VARIANTE', '') in ('anuncio', 'anuncio_tiktok')   # anuncio_tiktok: el anuncio en versión TikTok
MAPA = [[(1, 92), (75, 122), (165, 172), (300, 300)],   # gancho a cámara lenta → llegan las cartas → matemáticas
        [(301, 328), (362, 378)],                     # carrera: la etapa se marca
        [(363, 400), (452, 480)],                     # partida de práctica: el móvil se tumba, caen fichas
        [(453, 586), (572, 720)]]                     # final con el logo
if TIKTOK:                        # TikTok: la frase de Aprender es más larga: ese tramo dura algo más
    MAPA[2:] = [[(363, 400), (466, 486)], [(467, 586), (586, 720)]]
# Huecos de las cartas en la pantalla «Analiza tu mano» (u, v medidos en la captura) y su tamaño en la escena
HUECOS = {'Ah': (0.155, 0.341), 'Kh': (0.29, 0.341), 'Qh': (0.155, 0.464), '8c': (0.282, 0.464), '3h': (0.41, 0.464)}
ESCALA_HUECO = 0.125
GANCHO = ['¿Jugaste *bien*', 'tu *última* mano?']   # texto grande desde el primer fotograma (rojo entre asteriscos)
GANCHO_PALABRAS = 5               # palabras de a1 que ya están en el gancho (sin subtítulo)
SUB_Y = {'a3': 0.7}               # subtítulos más abajo mientras «Ganas 69 %» flota arriba (fracción del alto)

def _pchip(xs, ys, x):
    """Interpolación monótona (Fritsch-Carlson): pasa por los puntos sin pasarse ni ir hacia atrás."""
    n = len(xs); h = [xs[i + 1] - xs[i] for i in range(n - 1)]; d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [d[0]] + [0.0 if d[i - 1] * d[i] <= 0 else 3 * (h[i - 1] + h[i]) / ((2 * h[i] + h[i - 1]) / d[i - 1] + (h[i] + 2 * h[i - 1]) / d[i]) for i in range(1, n - 1)] + [d[-1]]
    for i in range(n - 1):
        if xs[i] <= x <= xs[i + 1]:
            t = (x - xs[i]) / h[i]; t2, t3 = t * t, t * t * t
            return (2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h[i] * m[i] + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h[i] * m[i + 1]
    return None

def orig(f):
    """Instante de la escena 3D (con decimales) que se ve en el fotograma f. Sin anuncio, el mismo f."""
    if not ANUNCIO: return float(f)
    for tr in MAPA:
        v = _pchip([a for a, _ in tr], [o for _, o in tr], f)
        if v is not None: return v
    return float(MAPA[-1][-1][1])

def ad(o):
    """Primer fotograma del anuncio que ya enseña el instante de escena o."""
    for tr in MAPA:
        if tr[0][1] <= o <= tr[-1][1]:
            return next(f for f in range(tr[0][0], tr[-1][0] + 1) if orig(f) >= o - 1e-6)
    raise ValueError(f'el instante {o} no sale en el anuncio')

if ANUNCIO:
    TOTAL = MAPA[-1][-1][0]       # 572 = 19 s
    CORTES = [tr[0][0] for tr in MAPA[1:]]
    GOLPES = [ad(150), ad(216), ad(356), ad(421)]   # tus cartas se pegan, «Ganas» se despega, sello de la carrera, caen las fichas
    LOGO, ESLOGAN, WEB = ad(590), ad(606), ad(622)
    ROTULO = (ad(160), ad(180) + 18)                # «o por voz» · «o pega tu historial», mientras se rellenan las cartas
    VOZ = [('a1', '¿Jugaste bien tu última mano? Compruébalo en diez segundos.', 2),
           ('a2', 'Hazle una foto y Río la lee sola.', 128),
           ('a3', 'Cuánto ganas, cuánto necesitas y por qué.', ad(212) - 4),
           ('a4', 'Y avanza nivel a nivel.', CORTES[0] + 3),
           ('a6', 'Y juega partidas de práctica contra rivales.', CORTES[1] + 3),
           ('a5', 'Pruébalo gratis en río poker punto es.', LOGO + 8)]
    SUBTITULOS = {'a1': '¿Jugaste bien tu última mano? Compruébalo en diez segundos.', 'a2': 'Hazle una foto y RÍO la lee sola.',
                  'a3': 'Cuánto ganas, cuánto necesitas y por qué.', 'a4': 'Y avanza nivel a nivel.',
                  'a6': 'Y juega partidas de práctica contra rivales.'}
    ROJAS = {'diez', 'segundos.', 'foto', 'RÍO', 'sola.', 'ganas,', 'necesitas', 'qué.', 'nivel', 'nivel.', 'práctica', 'rivales.'}
    EFECTOS = [('whoosh', 4), ('cartas', ad(134)), ('cartas', ad(152)), ('whoosh2', ad(190)), ('pop', ad(216)), ('cartas', ad(268)),
               ('whoosh', CORTES[0]), ('logro', ad(356)), ('whoosh', CORTES[1]), ('fichas', ad(420)), ('whoosh', CORTES[2]),
               ('golpe', LOGO), ('pop', WEB)]
    if TIKTOK:                    # TikTok: el tramo de práctica enseña Aprender; sin web ni «póker» en la voz; sin cartas ni fichas
        VOZ = [('v5t', 'Aprende con guías, tablas y lecciones cortas.', f) if v == 'a6' else
               ('a5t', 'Pruébalo gratis. Enlace en el perfil.', f) if v == 'a5' else (v, t, f) for v, t, f in VOZ]
        SUBTITULOS = {('v5t' if k == 'a6' else k): ('Aprende con guías, tablas y lecciones cortas.' if k == 'a6' else t) for k, t in SUBTITULOS.items()}
        ROJAS = ROJAS | {'guías,', 'lecciones'}
        EFECTOS = [(n, f) for n, f in EFECTOS if n not in ('fichas', 'cartas')]

def escena(f):
    for n, a, b in ESCENAS:
        if a <= f <= b: return n
    return ESCENAS[-1][0]


def suave(x):                     # 0..1 con entrada y salida suaves
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def tramo(f, ab):                 # avance 0..1 dentro de un tramo (a, b)
    a, b = ab; return suave((f - a) / max(1, b - a))
