# Guion del vídeo promocional 3D (versión 2): tiempos comunes a la escena (escena.py), la pantalla del móvil (pantalla.py),
# los subtítulos y el logo (post.py) y el sonido (audio.py). Fotogramas a 30 fps, empezando en 1.
FPS = 30
TOTAL = 720                       # 24 s

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

def escena(f):
    for n, a, b in ESCENAS:
        if a <= f <= b: return n
    return ESCENAS[-1][0]


def suave(x):                     # 0..1 con entrada y salida suaves
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def tramo(f, ab):                 # avance 0..1 dentro de un tramo (a, b)
    a, b = ab; return suave((f - a) / max(1, b - a))
