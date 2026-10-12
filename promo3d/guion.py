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
TIKTOK = _os.environ.get('VARIANTE', '') == 'tiktok'
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

# ---------- Anuncio de Instagram «¿Jugaste bien tu última mano?» (VARIANTE=anuncio, 16 s) ----------
# Usa trozos de la misma escena 3D con otra velocidad (cámara lenta en el giro, corte seco a la carrera y al final):
# MAPA dice, para cada fotograma del anuncio, qué instante de la escena se renderiza (con decimales: escena.py usa subframes).
# Añade una captura de pantalla de una mano que entra volando y se pega en el móvil (escena.py, CAPTURA_VUELA, en tiempo de escena).
ANUNCIO = _os.environ.get('VARIANTE', '') == 'anuncio'
CAPTURA_VUELA = (132, 147)        # (tiempo de escena) la captura sale de delante de la cámara y se pega en la pantalla
MAPA = [((1, 92), (75, 122)),     # gancho: el móvil se levanta y gira a cámara lenta (0,4×)
        ((75, 122), (165, 172)),  # foto: la captura se pega (anuncio 120) y llegan las cartas (0,55×)
        ((165, 172), (300, 300)), # matemáticas: la cámara entra en la pantalla y «Ganas 69 %» se despega
        ((301, 330), (360, 378)), # corte: la carrera, la etapa se marca (anuncio ~333)
        ((361, 586), (480, 720))] # corte: final con el logo
CORTES = [301, 361]               # cortes secos (destello y golpe de zoom en post.py)
GOLPES = [120, 211, 333]          # golpes de zoom: la captura se pega, «Ganas» se despega, sello de la carrera
GANCHO = ['¿Jugaste *bien*', 'tu *última* mano?']   # texto grande desde el primer fotograma (rojo entre asteriscos)
GANCHO_PALABRAS = 5               # palabras de a1 que ya están en el gancho (sin subtítulo)
ROTULO = (160, 198)
SUB_Y = {'a3': 0.7}               # subtítulos más abajo mientras «Ganas 69 %» flota arriba (fracción del alto)               # «o por voz · o pega tu historial»
if ANUNCIO:
    TOTAL = 480                   # 16 s
    VOZ = [('a1', '¿Jugaste bien tu última mano? Compruébalo en diez segundos.', 2),
           ('a2', 'Hazle una foto y Río la lee sola.', 128),
           ('a3', 'Cuánto ganas, cuánto necesitas y por qué.', 208),
           ('a4', 'Y avanza nivel a nivel.', 304),
           ('a5', 'Pruébalo gratis en río poker punto es.', 374)]
    SUBTITULOS = {'a1': '¿Jugaste bien tu última mano? Compruébalo en diez segundos.', 'a2': 'Hazle una foto y RÍO la lee sola.',
                  'a3': 'Cuánto ganas, cuánto necesitas y por qué.', 'a4': 'Y avanza nivel a nivel.'}
    ROJAS = {'diez', 'segundos.', 'foto', 'RÍO', 'sola.', 'ganas,', 'necesitas', 'qué.', 'nivel', 'nivel.'}
    LOGO, ESLOGAN, WEB = 366, 380, 394
    EFECTOS = [('whoosh', 4), ('whoosh2', 96), ('pop', 120), ('cartas', 122), ('cartas', 152), ('whoosh2', 190), ('pop', 211),
               ('cartas', 268), ('whoosh', 301), ('logro', 333), ('whoosh', 361), ('golpe', 366), ('pop', 394)]

def orig(f):
    """Instante de la escena 3D (con decimales) que se ve en el fotograma f. Sin anuncio, el mismo f."""
    if not ANUNCIO: return float(f)
    for (a0, o0), (a1, o1) in MAPA:
        if a0 <= f <= a1: return o0 + (f - a0) * (o1 - o0) / max(1, a1 - a0)
    return float(MAPA[-1][1][1])

def escena(f):
    for n, a, b in ESCENAS:
        if a <= f <= b: return n
    return ESCENAS[-1][0]


def suave(x):                     # 0..1 con entrada y salida suaves
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def tramo(f, ab):                 # avance 0..1 dentro de un tramo (a, b)
    a, b = ab; return suave((f - a) / max(1, b - a))
