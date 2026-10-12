# Guion del vídeo promocional 3D (versión 2): tiempos comunes a la escena (escena.py), la pantalla del móvil (pantalla.py),
# los subtítulos y el logo (post.py) y el sonido (audio.py). Fotogramas a 30 fps, empezando en 1.
FPS = 30
TOTAL = 720                       # 24 s

# (nombre, primer fotograma, último fotograma)
ESCENAS = [
    ('gancho',   1,   108),       # 1. el móvil escanea dos cartas boca abajo (rayos X), sube un 69 % y vuela a la pantalla
    ('analiza',  109, 195),       # 2. el móvil gira: «Analiza tu mano»; las cartas de la mesa entran volando
    ('analisis', 196, 305),       # 3. la cámara atraviesa la pantalla; «Ganas 69%» se despega; salen las cartas que te ayudan
    ('carrera',  306, 392),       # 4. el móvil gira; la etapa 3 se marca y salta un sello verde
    ('partida',  393, 490),       # 5. el móvil se tumba en la mesa (plano cenital): partida de práctica
    ('progreso', 491, 585),       # 6. el móvil se levanta; «Decisiones correctas 82%» se despega
    ('final',    586, TOTAL),     # 7. logo, «Empieza gratis» y riopoker.es
]

# Voz (ElevenLabs, promo3d/voz.py): id, texto, fotograma en el que empieza
VOZ = [
    ('v1', '¿Y si pudieras ver lo que hay detrás de cada mano?', 14),
    ('v2', 'Mete tu mano en Río en segundos.', 112),
    ('v3', 'Mira tus probabilidades y las cartas que te ayudan.', 200),
    ('v4', 'Avanza nivel a nivel en tu carrera.', 312),
    ('v5', 'Practica contra rivales con su propio estilo.', 398),
    ('v6', 'Y descubre tus errores para corregirlos.', 496),
    ('v7', 'Empieza gratis en río poker punto es.', 600),
]
# Subtítulos: lo que se lee para cada frase (mismas palabras que la voz, salvo cómo se escribe la marca) y las que van en rojo
SUBTITULOS = {
    'v1': '¿Y si pudieras ver lo que hay detrás de cada mano?',
    'v2': 'Mete tu mano en RÍO en segundos.',
    'v3': 'Mira tus probabilidades y las cartas que te ayudan.',
    'v4': 'Avanza nivel a nivel en tu carrera.',
    'v5': 'Practica contra rivales con su propio estilo.',
    'v6': 'Y descubre tus errores para corregirlos.',
}
ROJAS = {'ver', 'mano?', 'RÍO', 'segundos.', 'probabilidades', 'ayudan.', 'nivel', 'carrera.', 'rivales', 'estilo.', 'errores', 'corregirlos.'}
LOGO = 590                        # el logo final empieza a enfocarse
ESLOGAN = 606                     # «Empieza gratis»
WEB = 622                         # «riopoker.es»

# Pantalla del móvil (pantalla.py)
ESCANER = (24, 48)                # el móvil barre las cartas boca abajo con su luz (rayos X)
CONTADOR = (46, 66)               # el 69 % sube encima de las cartas
VUELA_NUMERO = (72, 94)           # el número vuela a la pantalla del móvil
GIRO_CARTAS = 76                  # las cartas se giran solas (A♥ K♥)
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
EFECTOS = [('fichas', 1), ('whoosh2', 6), ('escaner', 24), ('contador', 46), ('whoosh', 74), ('cartas', 78), ('whoosh', 96), ('cartas', 134), ('cartas', 154),
           ('whoosh2', 188), ('pop', 216), ('cartas', 268), ('whoosh', 296), ('logro', 356), ('whoosh', 384),
           ('fichas', 420), ('cartas', 440), ('whoosh', 482), ('pop', 508), ('whoosh', 578), ('golpe', 590), ('pop', 622)]


def escena(f):
    for n, a, b in ESCENAS:
        if a <= f <= b: return n
    return ESCENAS[-1][0]


def suave(x):                     # 0..1 con entrada y salida suaves
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def tramo(f, ab):                 # avance 0..1 dentro de un tramo (a, b)
    a, b = ab; return suave((f - a) / max(1, b - a))
