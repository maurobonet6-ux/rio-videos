# Escena 3D del vídeo promocional de RÍO: mesa de póker de fieltro granate vista desde arriba, fichas y cartas,
# y un móvil con la app real en pantalla (pantalla.py) que se levanta de la mesa. Tiempos en guion.py.
# Usa Blender como librería de Python (pip install bpy) y renderiza con Cycles en CPU.
# Uso: python3.11 promo3d/escena.py --salida DIR [--ancho 720] [--muestras 8] [--desde 1] [--hasta 780] [--cada 1]
import bpy, bmesh, math, os, sys, time, json, argparse
from mathutils import Matrix, Vector, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import guion as G
import pantalla as P

CAP = os.path.join(AQUI, '..', 'salida', 'promo3d')
TEX = os.path.join(CAP, 'tex')
ROJO = (0.78, 0.03, 0.06)   # #E5304A en lineal

a = argparse.ArgumentParser()
a.add_argument('--salida', required=True)
a.add_argument('--ancho', type=int, default=720)
a.add_argument('--muestras', type=int, default=8)
a.add_argument('--desde', type=int, default=1)
a.add_argument('--hasta', type=int, default=G.TOTAL)
a.add_argument('--cada', type=int, default=1)
a.add_argument('--hilos', type=int, default=0)
a.add_argument('--lista', default='')   # fotogramas sueltos: 1,150,270
args = a.parse_args()
os.makedirs(args.salida, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = G.FPS
sc.frame_start, sc.frame_end = 1, G.TOTAL

# ---------- utilidades ----------
def rectangulo_redondeado(nombre, ancho, alto, radio, grosor=0.0, segmentos=10, enlazar=True):
    """Rectángulo con esquinas redondeadas en el plano XZ (mirando a -Y). Con grosor, se extruye hacia +Y."""
    bm = bmesh.new()
    w, h = ancho / 2, alto / 2
    vs = [bm.verts.new(p) for p in ((-w, 0, -h), (w, 0, -h), (w, 0, h), (-w, 0, h))]
    bm.faces.new(vs)
    bmesh.ops.bevel(bm, geom=vs, offset=radio, segments=segmentos, affect='VERTICES', profile=0.5)
    if grosor:
        bm.faces.ensure_lookup_table(); cara = bm.faces[0]
        ext = bmesh.ops.extrude_face_region(bm, geom=[cara])
        nuevos = [v for v in ext['geom'] if isinstance(v, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, verts=nuevos, vec=(0, grosor, 0))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    uv = bm.loops.layers.uv.new('UVMap')
    for f in bm.faces:
        for l in f.loops:
            l[uv].uv = ((l.vert.co.x + w) / ancho, (l.vert.co.z + h) / alto)
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(nombre, me)
    if enlazar: sc.collection.objects.link(ob)
    return ob

def tumbar(ob):
    """Pasa una malla del plano XZ (mirando a -Y) al plano XY (mirando a +Z): así quedan sobre la mesa."""
    ob.data.transform(Matrix.Rotation(math.radians(-90), 4, 'X'))

def material(nombre, base=(0, 0, 0), metal=0.0, rugosidad=0.5, coat=0.0):
    m = bpy.data.materials.new(nombre); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*base, 1)
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = rugosidad
    p.inputs['Coat Weight'].default_value = coat
    return m

def material_imagen(nombre, ruta, emision=0.0, rugosidad=0.35, coat=0.0, dorso=None, vector=None):
    """Material con una imagen (por UV o por el vector que se le pase). Con emisión, brilla como una pantalla."""
    m = material(nombre, rugosidad=rugosidad, coat=coat); N = m.node_tree.nodes; L = m.node_tree.links
    p = N['Principled BSDF']
    t = N.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(ruta); t.interpolation = 'Cubic'
    if vector is not None: L.new(vector(N, L), t.inputs['Vector'])
    color = t.outputs['Color']
    if dorso:
        t2 = N.new('ShaderNodeTexImage'); t2.image = bpy.data.images.load(dorso)
        uvd = N.new('ShaderNodeTexCoord'); esp = N.new('ShaderNodeMapping')     # el dorso se ve por detrás: se da la vuelta a la imagen
        esp.inputs['Location'].default_value = (1, 0, 0); esp.inputs['Scale'].default_value = (-1, 1, 1)
        L.new(uvd.outputs['UV'], esp.inputs['Vector']); L.new(esp.outputs['Vector'], t2.inputs['Vector'])
        geo = N.new('ShaderNodeNewGeometry'); mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'
        L.new(geo.outputs['Backfacing'], mx.inputs['Factor']); L.new(t.outputs['Color'], mx.inputs[6]); L.new(t2.outputs['Color'], mx.inputs[7])
        color = mx.outputs[2]
    if emision:
        p.inputs['Base Color'].default_value = (0, 0, 0, 1)
        L.new(color, p.inputs['Emission Color']); p.inputs['Emission Strength'].default_value = emision
    else:
        L.new(color, p.inputs['Base Color'])
    return m, t

def animar(ob, claves, ruta='location', interp='BEZIER'):
    """claves: [(fotograma, valor)]; valor en grados si ruta es rotation_euler."""
    for f, v in claves:
        if ruta == 'rotation_euler': v = [math.radians(x) for x in v]
        setattr(ob, ruta, v); ob.keyframe_insert(ruta, frame=f)
    for fc in curvas(ob):
        if fc.data_path != ruta: continue
        for k in fc.keyframe_points:
            k.interpolation = interp
            if interp == 'BEZIER': k.handle_left_type = k.handle_right_type = 'AUTO_CLAMPED'

def curvas(ob):
    act = ob.animation_data.action
    try: return list(act.fcurves)
    except AttributeError:
        return [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]

def visible(ob, desde=None, hasta=None):
    """Oculta el objeto antes de 'desde' y después de 'hasta'."""
    pasos = [(1, desde is not None)]
    if desde is not None: pasos.append((desde, False))
    if hasta is not None: pasos.append((hasta + 1, True))
    for f, oculto in pasos:
        ob.hide_render = oculto; ob.keyframe_insert('hide_render', frame=f)

def vacio(nombre, padre=None):
    e = bpy.data.objects.new(nombre, None); sc.collection.objects.link(e)
    if padre: e.parent = padre
    return e

# ---------- mesa: fieltro granate muy oscuro con textura ----------
mesa = rectangulo_redondeado('Mesa', 40, 40, 0.01); tumbar(mesa)
mf = material('Fieltro', rugosidad=0.95)
N = mf.node_tree.nodes; L = mf.node_tree.links; Pb = N['Principled BSDF']
coord = N.new('ShaderNodeTexCoord')
grano = N.new('ShaderNodeTexNoise'); grano.inputs['Scale'].default_value = 900; grano.inputs['Detail'].default_value = 4
manchas = N.new('ShaderNodeTexNoise'); manchas.inputs['Scale'].default_value = 0.35; manchas.inputs['Detail'].default_value = 6
for n in (grano, manchas): L.new(coord.outputs['Object'], n.inputs['Vector'])
rampa = N.new('ShaderNodeValToRGB')
rampa.color_ramp.elements[0].position = 0.25; rampa.color_ramp.elements[0].color = (0.006, 0.0006, 0.001, 1)
rampa.color_ramp.elements[1].position = 0.75; rampa.color_ramp.elements[1].color = (0.022, 0.0018, 0.0032, 1)
mezcla = N.new('ShaderNodeMath'); mezcla.operation = 'MULTIPLY_ADD'; mezcla.inputs[1].default_value = 0.25
L.new(grano.outputs['Fac'], mezcla.inputs[0]); L.new(manchas.outputs['Fac'], mezcla.inputs[2])
L.new(mezcla.outputs[0], rampa.inputs['Fac']); L.new(rampa.outputs['Color'], Pb.inputs['Base Color'])
bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.35; bump.inputs['Distance'].default_value = 0.02
L.new(grano.outputs['Fac'], bump.inputs['Height']); L.new(bump.outputs['Normal'], Pb.inputs['Normal'])
Pb.inputs['Sheen Weight'].default_value = 0.25; Pb.inputs['Sheen Tint'].default_value = (0.6, 0.12, 0.15, 1)
mesa.data.materials.append(mf)

# ---------- fichas (sin valores) ----------
R_FICHA, H_FICHA = 0.2, 0.034
def malla_ficha(color):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=64, radius1=R_FICHA, radius2=R_FICHA, depth=H_FICHA)
    me = bpy.data.meshes.new('Ficha_' + color); bm.to_mesh(me); bm.free()
    for f in me.polygons: f.use_smooth = True
    def vec(N, L):            # la imagen se proyecta desde arriba: la cara de arriba y, estirada, el canto (rayas)
        c = N.new('ShaderNodeTexCoord'); mp = mapping(N); L.new(c.outputs['Object'], mp.inputs['Vector']); return mp.outputs['Vector']
    m, _ = material_imagen('Ficha_' + color, os.path.join(TEX, f'ficha_{color}.png'), rugosidad=0.45, coat=0.4, vector=vec)
    me.materials.append(m)
    return me
def mapping(N):
    mp = N.new('ShaderNodeMapping'); mp.inputs['Location'].default_value = (0.5, 0.5, 0)
    mp.inputs['Scale'].default_value = (0.5 / R_FICHA, 0.5 / R_FICHA, 1); return mp
MALLAS = {c: malla_ficha(c) for c in ('roja', 'negra', 'blanca', 'gris')}
def ficha(color, x, y, n=0, giro=0.0, padre=None):
    o = bpy.data.objects.new('ficha', MALLAS[color]); sc.collection.objects.link(o)
    o.location = (x, y, H_FICHA / 2 + n * H_FICHA); o.rotation_euler = (0, 0, giro)
    bev = o.modifiers.new('b', 'BEVEL'); bev.width = 0.006; bev.segments = 2
    return o
def pila(x, y, colores, desorden=0.012):
    for i, c in enumerate(colores):
        ficha(c, x + desorden * math.sin(i * 2.3), y + desorden * math.cos(i * 1.7), i, i * 0.9)
pila(1.15, 1.55, ['negra', 'roja', 'roja', 'negra', 'roja', 'blanca'])
pila(-1.35, 2.25, ['blanca', 'blanca', 'gris', 'negra', 'negra', 'roja', 'roja', 'blanca'])
pila(1.55, -2.45, ['roja', 'roja', 'negra', 'gris'])
pila(-1.7, -1.05, ['negra', 'blanca', 'roja', 'roja', 'blanca'])
pila(-0.95, 3.6, ['gris', 'gris', 'negra'])
for x, y, c in ((0.55, 2.0, 'roja'), (-0.45, -2.75, 'negra'), (1.9, 0.3, 'blanca'), (-2.0, 0.6, 'roja'), (0.95, -3.3, 'gris')):
    ficha(c, x, y, 0, x * 3)
# Fichas que caen sobre la primera pila en el gancho, y junto al móvil en la partida (suenan en audio.py)
def cae(color, x, y, n, f, giro):
    o = ficha(color, x, y, n, giro); z = H_FICHA / 2 + n * H_FICHA
    animar(o, [(f - 9, (x + 0.15, y - 0.4, z + 1.6)), (f, (x, y, z))], interp='LINEAR')
    animar(o, [(f - 9, (35, -20, giro * 57)), (f, (0, 0, giro * 57))], ruta='rotation_euler', interp='LINEAR')
for i, f in enumerate((30, 34, 38, 43)): cae(['roja', 'negra', 'roja', 'blanca'][i], 1.15, 1.55, 6 + i, f, i * 1.3)
for i, (x, y) in enumerate(((0.62, 0.35), (0.6, 0.35), (-0.66, -1.05), (0.64, -1.25))):
    cae(['negra', 'roja', 'blanca', 'roja'][i], x, y, 1 if i == 1 else 0, 420 + i * 3, i)

# ---------- cartas ----------
CARTA_W, CARTA_H, CARTA_G = 0.66, 0.92, 0.006       # 63 x 88 mm y algo de grosor de cartón
Z_CARTA = CARTA_G + 0.0005                            # apoyada en el fieltro
PAPEL_L = (0.95, 0.93, 0.89, 1)
def material_carta(c, rayos=False, eje=(0, 0, 1)):
    """Cara, dorso y canto según hacia dónde mira cada cara (normal del objeto). Con rayos=True, el dorso se vuelve
    transparente por donde ya ha pasado el escáner (valor 'scan' animado: y del mundo) y deja ver la carta."""
    m = bpy.data.materials.new('Carta_' + c); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    p = N['Principled BSDF']; p.inputs['Roughness'].default_value = 0.42; p.inputs['Coat Weight'].default_value = 0.25
    p.inputs['Coat Roughness'].default_value = 0.25
    tc = N.new('ShaderNodeTexCoord')
    esp = N.new('ShaderNodeMapping'); esp.inputs['Location'].default_value = (1, 0, 0); esp.inputs['Scale'].default_value = (-1, 1, 1)
    L.new(tc.outputs['UV'], esp.inputs['Vector'])
    def img(nombre, espejo=False):
        t = N.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(TEX, nombre)); t.interpolation = 'Cubic'
        L.new((esp if espejo else tc).outputs['Vector' if espejo else 'UV'], t.inputs['Vector']); return t.outputs['Color']
    cara, dorso = img(f'carta_{c}.png'), img('dorso.png', True)
    dot = N.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'; dot.inputs[1].default_value = eje
    L.new(tc.outputs['Normal'], dot.inputs[0])
    def umbral(op, v):
        n = N.new('ShaderNodeMath'); n.operation = op; n.inputs[1].default_value = v; L.new(dot.outputs['Value'], n.inputs[0]); return n.outputs[0]
    es_cara, es_dorso = umbral('GREATER_THAN', 0.5), umbral('LESS_THAN', -0.5)
    def mezcla(fac, a, b):
        x = N.new('ShaderNodeMix'); x.data_type = 'RGBA'; L.new(fac, x.inputs['Factor'])
        for k, v in ((6, a), (7, b)):
            if isinstance(v, tuple): x.inputs[k].default_value = v
            else: L.new(v, x.inputs[k])
        return x.outputs[2]
    if rayos:
        scan = N.new('ShaderNodeValue'); scan.name = 'scan'; scan.outputs[0].default_value = -9
        geo = N.new('ShaderNodeNewGeometry'); sep = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Position'], sep.inputs[0])
        dif = N.new('ShaderNodeMath'); dif.operation = 'SUBTRACT'; L.new(scan.outputs[0], dif.inputs[0]); L.new(sep.outputs['Y'], dif.inputs[1])
        rev = N.new('ShaderNodeMapRange'); rev.inputs['From Min'].default_value = 0; rev.inputs['From Max'].default_value = 0.035
        L.new(dif.outputs[0], rev.inputs['Value'])                                  # 1 donde ya ha pasado el escáner
        borde = N.new('ShaderNodeMath'); borde.operation = 'ABSOLUTE'; L.new(dif.outputs[0], borde.inputs[0])
        filo = N.new('ShaderNodeMapRange'); filo.inputs['From Min'].default_value = 0.02; filo.inputs['From Max'].default_value = 0.0
        L.new(borde.outputs[0], filo.inputs['Value'])                               # 1 justo en la línea del escáner
        visto = img(f'carta_{c}.png', True)                                         # la cara, vista «a través» del dorso
        tinte = N.new('ShaderNodeMix'); tinte.data_type = 'RGBA'; tinte.blend_type = 'MULTIPLY'; tinte.inputs['Factor'].default_value = 0.35
        L.new(visto, tinte.inputs[6]); tinte.inputs[7].default_value = (1.0, 0.55, 0.6, 1)
        dorso = mezcla(rev.outputs['Result'], dorso, tinte.outputs[2])
        brillo = N.new('ShaderNodeMath'); brillo.operation = 'MULTIPLY'; L.new(es_dorso, brillo.inputs[0])
        suma = N.new('ShaderNodeMath'); suma.operation = 'ADD'; L.new(filo.outputs['Result'], suma.inputs[0])
        luzc = N.new('ShaderNodeMath'); luzc.operation = 'MULTIPLY'; luzc.inputs[1].default_value = 0.35; L.new(rev.outputs['Result'], luzc.inputs[0])
        L.new(luzc.outputs[0], suma.inputs[1]); L.new(suma.outputs[0], brillo.inputs[1])
        emi = mezcla(filo.outputs['Result'], tinte.outputs[2], (1.0, 0.12, 0.2, 1))
        L.new(emi, p.inputs['Emission Color']); L.new(brillo.outputs[0], p.inputs['Emission Strength'])
    color = mezcla(es_cara, PAPEL_L, cara); color = mezcla(es_dorso, color, dorso)
    L.new(color, p.inputs['Base Color'])
    return m
def carta(c, x=0, y=0, giro=0, boca_arriba=True, tumbada=True, padre=None, rayos=False):
    """Carta con grosor y cantos redondeados: en la mesa (tumbada, cara hacia +Z) o, sin tumbar, mirando a -Y como la pantalla."""
    o = rectangulo_redondeado('carta_' + c, CARTA_W, CARTA_H, 0.045, grosor=CARTA_G, segmentos=8)
    for p_ in o.data.polygons: p_.use_smooth = False
    if tumbada: tumbar(o)
    if not boca_arriba: o.data.transform(Matrix.Rotation(math.pi, 4, 'Y' if tumbada else 'Z'))
    o.data.materials.append(material_carta(c, rayos, (0, 0, 1) if tumbada else (0, -1, 0)))
    if padre: o.parent = padre
    else: o.location = (x, y, Z_CARTA); o.rotation_euler = (0, 0, math.radians(giro))
    return o
carta('Js', 1.25, -1.05, 18, False); carta('Td', 1.4, -1.2, -9, False)
VUELAN = {   # cartas que entran volando en el móvil: (posición en la mesa, giro, fotograma de llegada, punto de la pantalla u, v)
    'Ah': ((-0.95, -2.1), -12, G.LLEGA_MANO1, (0.12, 0.25)), 'Kh': ((-0.4, -2.2), 8, G.LLEGA_MANO1, (0.27, 0.25)),
    'Qh': ((-1.35, -0.2), 4, G.LLEGA_FLOP, (0.12, 0.43)), '8c': ((1.4, 0.15), -6, G.LLEGA_FLOP, (0.27, 0.43)),
    '3h': ((-1.25, 0.75), 10, G.LLEGA_FLOP, (0.42, 0.43)),
}
cartas_vuelan = {c: carta(c, x, y, g, rayos=c in ('Ah', 'Kh')) for c, ((x, y), g, _, _) in VUELAN.items()}
# Gancho: tus dos cartas están boca abajo; el escáner del móvil las «atraviesa» (rayos X) y luego se giran solas.
for i, c in enumerate(('Ah', 'Kh')):
    o = cartas_vuelan[c]; g0_ = G.GIRO_CARTAS + i * 4
    for f, r in ((1, (0, 180, 0)), (g0_, (0, 180, 0)), (g0_ + 12, (0, 0, 0))):
        o.delta_rotation_euler = [math.radians(x) for x in r]; o.keyframe_insert('delta_rotation_euler', frame=f)
    animar(o, [(g0_, (0, 0, 0)), (g0_ + 6, (0, 0, 0.25)), (g0_ + 12, (0, 0, 0))], ruta='delta_location')
    sn = o.active_material.node_tree.nodes['scan'].outputs[0]
    for f, v in ((G.ESCANER[0], -2.75), (G.ESCANER[1], -1.55)): sn.default_value = v; sn.keyframe_insert('default_value', frame=f)

# ---------- móvil ----------
movil = vacio('Movil'); movil.rotation_mode = 'YXZ'      # Y: gira sobre su eje largo · X: inclinación · Z: guiño
pivote = vacio('Pivote', movil); pivote.rotation_euler = (math.radians(-90), 0, 0)   # el móvil se modela mirando a -Y
GR = 0.085                                   # grosor
cuerpo = rectangulo_redondeado('Cuerpo', 0.78, 1.62, 0.12, grosor=GR, segmentos=12)
cuerpo.location = (0, -GR / 2, 0); cuerpo.parent = pivote
bev = cuerpo.modifiers.new('Bisel', 'BEVEL'); bev.width = 0.022; bev.segments = 5; bev.limit_method = 'ANGLE'; bev.harden_normals = True
for f in cuerpo.data.polygons: f.use_smooth = True
cuerpo.data.materials.append(material('Titanio', base=(0.05, 0.05, 0.055), metal=1.0, rugosidad=0.22))
marco = rectangulo_redondeado('Marco', 0.75, 1.59, 0.105)
marco.location = (0, -GR / 2 - 0.0015, 0); marco.parent = pivote
marco.data.materials.append(material('Cristal negro', rugosidad=0.04, coat=1.0))
PW = 0.72; PH = PW * P.SH / P.SW
pantalla = rectangulo_redondeado('Pantalla', PW, PH, 0.085)
pantalla.location = (0, -GR / 2 - 0.0025, 0); pantalla.parent = pivote
m_pant, tex_pant = material_imagen('Pantalla', P.ruta(1) if os.path.exists(P.ruta(1)) else os.path.join(CAP, 'inicio.png'), emision=1.0, rugosidad=0.03)
m_pant.node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value = 0.12
m_pant.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.2
m_pant.node_tree.nodes['Principled BSDF'].inputs['Coat Roughness'].default_value = 0.02
tex_pant.interpolation = 'Linear'
pantalla.data.materials.append(m_pant)
isla = rectangulo_redondeado('Isla', 0.2, 0.058, 0.029)
isla.location = (0, -GR / 2 - 0.0035, PH / 2 - 0.06); isla.parent = pivote
isla.data.materials.append(material('Isla', rugosidad=0.1))

def punto_pantalla(u, v, delante=0.004):
    """Punto de la pantalla (u, v en 0..1 desde arriba a la izquierda) en coordenadas del pivote."""
    return Vector((-PW / 2 + u * PW, -GR / 2 - delante, PH / 2 - v * PH))
def uv_caja(x, y, w, h):
    """Centro de una caja en px de la pantalla (1200x2580) → u, v."""
    return (x + w / 2) / P.SW, (y + h / 2) / P.SH

# Poses del móvil: (fotograma, posición, (inclinación X, giro Y, guiño Z))
INCL = 22
ARRIBA = (0, 0.2, 1.6)
MESA = (0, -0.3, GR / 2 + 0.003)
ESCANEA, ESCANEA2 = (-0.67, -1.5, 0.85), (-0.66, -1.47, 0.88)   # flotando sobre tus cartas, con la pantalla hacia ellas
g0, g1 = G.GIRO_INICIO; v0, v1 = G.VUELTA_CARRERA
POSES = [
    (1, (0.4, -0.9, 3.3), (128, 0, -40)), (16, ESCANEA, (128, 0, 0)), (60, ESCANEA2, (126, 0, 3)), (72, ESCANEA2, (122, 0, 3)),
    (g0, ARRIBA, (INCL, 0, 4)),     # gancho: el móvil entra, escanea las cartas desde arriba y se da la vuelta hacia ti
    (g1, ARRIBA, (INCL, 360, -3)), (150, ARRIBA, (INCL, 360, 6)), (188, ARRIBA, (INCL, 360, 0)),
    (198, ARRIBA, (INCL, 360, 0)), (250, ARRIBA, (INCL, 360, -5)), (292, ARRIBA, (INCL, 360, -2)),
    (v0, ARRIBA, (INCL, 360, -2)), (v1, ARRIBA, (INCL, 720, 4)), (360, ARRIBA, (INCL, 720, 8)), (382, ARRIBA, (INCL, 720, 4)),
    (404, MESA, (0, 720, -10)), (480, MESA, (0, 720, -10)),
    (500, ARRIBA, (INCL + 4, 720, 8)), (540, ARRIBA, (INCL, 720, 2)), (578, ARRIBA, (INCL, 720, -4)),
    (606, (0, 0.2, 1.45), (INCL + 6, 720, 0)), (G.TOTAL, (0, 0.2, 1.45), (INCL + 6, 720, 3)),
]
animar(movil, [(f, p) for f, p, _ in POSES])
animar(movil, [(f, r) for f, _, r in POSES], ruta='rotation_euler')

def mundo(f, local):
    """Punto en coordenadas del pivote → mundo, en el fotograma f."""
    sc.frame_set(f); return pivote.matrix_world @ Vector(local)
def ejes(f):
    """Ejes de la pantalla en el mundo en el fotograma f: derecha, arriba, normal (hacia quien mira)."""
    sc.frame_set(f); m = pivote.matrix_world.to_3x3().normalized()
    return m @ Vector((1, 0, 0)), m @ Vector((0, 0, 1)), m @ Vector((0, -1, 0))

# Brillo rojo de marca debajo del móvil: ilumina el fieltro cuando el móvil está levantado
dl = bpy.data.lights.new('Roja', 'AREA'); dl.energy = 45; dl.size = 1.4; dl.color = ROJO
roja = bpy.data.objects.new('Roja', dl); sc.collection.objects.link(roja); roja.parent = movil
roja.location = (0, 0, -0.12)

# Cartas que vuelan: de la mesa, en arco, y entran en la pantalla (se encogen y desaparecen)
for c, ((x, y), giro, llega, (u, v)) in VUELAN.items():
    o = cartas_vuelan[c]; sale = llega - 16 + (2 if c in ('Kh', '8c') else 0) + (4 if c == '3h' else 0)
    fin = mundo(llega, punto_pantalla(u, v, 0.02))
    medio = Vector(((x + fin.x) / 2, (y + fin.y) / 2 - 0.3, 2.2))
    animar(o, [(sale, (x, y, Z_CARTA)), (sale + 8, medio), (llega, fin)])
    animar(o, [(sale, (0, 0, giro)), (sale + 8, (INCL - 30, 20 if x < 0 else -20, giro / 2)), (llega, (INCL, 0, 0))], ruta='rotation_euler')
    animar(o, [(sale + 8, (1.1, 1.1, 1.1)), (llega, (0.2, 0.2, 0.2))], ruta='scale')
    visible(o, hasta=llega)

# ---------- cosas que salen de la pantalla ----------
def tarjeta(nombre, despega, sale, destino, giro):
    """Una tarjeta de la app se despega de la pantalla, flota delante y luego sale disparada hacia la cámara."""
    x, y, w, h = P.caja_pantalla(nombre)
    tw, th = w / P.SW * PW, h / P.SH * PH
    o = rectangulo_redondeado('Tarjeta_' + nombre, tw, th, min(tw, th) * 0.09, grosor=0.012)
    o.parent = pivote
    m, _ = material_imagen('Tarjeta_' + nombre, os.path.join(CAP, f'tarjeta_{nombre}.png'), emision=1.0, rugosidad=0.05)
    m.node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value = 1.0
    o.data.materials.append(m)
    ini = punto_pantalla(*uv_caja(x, y, w, h), 0.006)
    a, b = despega
    dest = ini + Vector(destino)
    animar(o, [(a, ini), (b, dest), (sale - 10, dest + Vector((0, -0.04, 0.02))), (sale, dest + Vector((0, -2.6, 0.4)))])
    animar(o, [(a, (0, 0, 0)), (b, giro), (sale - 10, giro), (sale, (giro[0] - 20, giro[1], giro[2]))], ruta='rotation_euler')
    animar(o, [(a, (1, 1, 1)), (b, (1.3, 1.3, 1.3))], ruta='scale')
    visible(o, desde=a, hasta=sale)
    return dest
DEST_GANAS = tarjeta('ganas', G.DESPEGA_GANAS, v0 + 4, (0.12, -0.42, 0.1), (10, -10, 3))
DEST_CORRECTAS = tarjeta('correctas', G.DESPEGA_CORRECTAS, 566, (0.24, -0.5, 0.14), (8, 10, -4))

# Las cartas que te ayudan salen de la lista de outs en abanico
OUTS_UV = uv_caja(*P.INFO['analisis']['outs'][:2], *P.INFO['analisis']['outs'][2:])
OUTS_UV = (OUTS_UV[0], (P.INFO['analisis']['outs'][1] + P.INFO['analisis']['outs'][3] / 2 - P.SCROLL_MAX['analisis'] + P.BARRA) / P.SH)
a, b = G.SALEN_OUTS
for i, c in enumerate(('Jh', 'Th', '9h', '7h', 'As')):
    o = carta(c, tumbada=False, padre=pivote); k = i - 2
    ini = punto_pantalla(OUTS_UV[0] + k * 0.12, OUTS_UV[1], 0.01)
    medio = Vector((k * 0.24, -0.55 - abs(k) * 0.04, -0.15 + 0.06 * (2 - abs(k))))
    fin = Vector((k * 0.9, -2.2, 0.9 - 0.1 * abs(k)))
    s0 = a + i * 2
    animar(o, [(s0, ini), (s0 + 10, medio), (s0 + 16, medio + Vector((0, -0.08, 0.04))), (b + 6, fin)])
    animar(o, [(s0, (0, 0, 0)), (s0 + 10, (8, k * 9, -k * 4)), (b + 6, (40, k * 40, -k * 20))], ruta='rotation_euler')
    animar(o, [(s0, (0.15, 0.15, 0.15)), (s0 + 10, (0.42, 0.42, 0.42))], ruta='scale')
    visible(o, desde=s0, hasta=b + 6)

# Sello verde de «etapa superada»: salta del círculo de la etapa 3
cb = P.INFO['carrera_b']['nodo3']
NODO_UV = ((cb[0] + cb[2] / 2) / P.SW, (cb[1] + cb[3] / 2 - P.SCROLL_MAX['carrera'] + P.BARRA) / P.SH)
sello = rectangulo_redondeado('Sello', 0.2, 0.2, 0.0999, grosor=0.02, segmentos=16); sello.parent = pivote
ms, _ = material_imagen('Sello', os.path.join(TEX, 'sello.png'), emision=1.6, rugosidad=0.1)
sello.data.materials.append(ms)
m0 = G.MARCA_ETAPA; ini = punto_pantalla(*NODO_UV, 0.01)
animar(sello, [(m0, ini), (m0 + 8, ini + Vector((0.18, -0.35, 0.05))), (m0 + 24, ini + Vector((0.22, -0.4, 0.08))), (386, ini + Vector((0.4, -2.4, 0.6)))])
animar(sello, [(m0, (0, 0, 0)), (m0 + 8, (0, 0, 0)), (m0 + 24, (10, 0, -8)), (386, (60, 0, -30))], ruta='rotation_euler')
animar(sello, [(m0, (0.5, 0.5, 0.5)), (m0 + 6, (1.35, 1.35, 1.35)), (m0 + 10, (1.15, 1.15, 1.15))], ruta='scale')
visible(sello, desde=m0, hasta=386)

# En la partida: el móvil, tumbado en la mesa, «reparte» dos cartas sobre el fieltro
for i, (dx, dy, giro) in enumerate(((-0.6, 0.35, -14), (0.62, 0.0, 12))):
    o = carta('Js', boca_arriba=False); f0 = 432 + i * 4
    ini = mundo(f0, punto_pantalla(0.5, 0.6, 0.03))
    animar(o, [(f0, (ini.x, ini.y, 0.07)), (f0 + 10, (dx, dy - 0.3, Z_CARTA))])
    animar(o, [(f0, (0, 0, 0)), (f0 + 10, (0, 0, giro))], ruta='rotation_euler')
    animar(o, [(f0, (0.3, 0.3, 0.3)), (f0 + 10, (0.8, 0.8, 0.8))], ruta='scale')
    visible(o, desde=f0, hasta=482)

# ---------- gancho: escáner (luz roja que barre la mesa) y contador 3D ----------
def emisivo(nombre, color, fuerza, alfa=1.0):
    m = bpy.data.materials.new(nombre); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    for n in list(N): N.remove(n)
    e = N.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (*color, 1); e.inputs['Strength'].default_value = fuerza
    out = N.new('ShaderNodeOutputMaterial')
    if alfa < 1:
        t = N.new('ShaderNodeBsdfTransparent'); mx = N.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = alfa
        L.new(t.outputs[0], mx.inputs[1]); L.new(e.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs['Surface'])
    else: L.new(e.outputs[0], out.inputs['Surface'])
    return m
e0, e1 = G.ESCANER
X_ESC = (-1.4, 0.1)                                    # ancho de la línea: cubre las dos cartas
linea = rectangulo_redondeado('LineaEscaner', X_ESC[1] - X_ESC[0], 0.014, 0.006); tumbar(linea)
linea.data.materials.append(emisivo('Linea', (1.0, 0.1, 0.16), 14))
animar(linea, [(e0, ((X_ESC[0] + X_ESC[1]) / 2, -2.75, 0.015)), (e1, ((X_ESC[0] + X_ESC[1]) / 2, -1.55, 0.015))], interp='LINEAR')
visible(linea, desde=e0 - 2, hasta=e1 + 2)
dle = bpy.data.lights.new('LuzEscaner', 'AREA'); dle.shape = 'RECTANGLE'; dle.size = 1.5; dle.size_y = 0.08; dle.energy = 6; dle.color = ROJO
luz_esc = bpy.data.objects.new('LuzEscaner', dle); sc.collection.objects.link(luz_esc); luz_esc.parent = linea; luz_esc.location = (0, 0, 0.12)
for fr, e in ((1, 0), (e0 - 2, 0), (e0 + 2, 6), (e1 - 2, 6), (e1 + 2, 0)):
    dle.energy = e; dle.keyframe_insert('energy', frame=fr)
# El haz: un abanico de luz de la pantalla del móvil a la línea (se recoloca en cada fotograma)
me = bpy.data.meshes.new('Haz'); me.from_pydata([(0, 0, 0)] * 4, [], [(0, 1, 2, 3)])
haz = bpy.data.objects.new('Haz', me); sc.collection.objects.link(haz); me.materials.append(emisivo('Haz', (1.0, 0.15, 0.22), 2.5, 0.16))
visible(haz, desde=e0 - 2, hasta=e1 + 2)
haz.visible_shadow = False
def colocar_haz():
    a = pivote.matrix_world @ punto_pantalla(0.08, 0.55, 0.01); b = pivote.matrix_world @ punto_pantalla(0.92, 0.55, 0.01)
    y = linea.matrix_world.translation.y
    for v, co in zip(me.vertices, (a, b, (X_ESC[1], y, 0.016), (X_ESC[0], y, 0.016))): v.co = co
    me.update()
# El 69 % que sube encima de las cartas (el «Ganas 69% de las veces» del análisis)
fuente = bpy.data.fonts.load('/usr/share/fonts/opentype/inter/InterDisplay-Black.otf')
tc_ = bpy.data.curves.new('Contador', 'FONT'); tc_.body = '0%'; tc_.font = fuente; tc_.align_x = 'CENTER'; tc_.align_y = 'CENTER'
tc_.size = 0.34; tc_.extrude = 0.018; tc_.bevel_depth = 0.004
contador = bpy.data.objects.new('Contador', tc_); sc.collection.objects.link(contador)
contador.data.materials.append(emisivo('Contador', (0.9, 0.035, 0.06), 1.6))
c0, c1 = G.CONTADOR; n0, n1 = G.VUELA_NUMERO
destino = mundo(n1, punto_pantalla(0.5, 0.35, 0.02))
animar(contador, [(c0 - 2, (-0.67, -2.15, 0.12)), (c0 + 6, (-0.67, -2.15, 0.42)), (n0, (-0.67, -2.13, 0.45)), (n1, destino)])
animar(contador, [(c0 - 2, (45, 0, 0)), (n0, (45, 0, 0)), (n1, (INCL, 0, 0))], ruta='rotation_euler')
animar(contador, [(c0 - 2, (0.2, 0.2, 0.2)), (c0 + 6, (1.15, 1.15, 1.15)), (c0 + 10, (1, 1, 1)), (n0, (1, 1, 1)), (n1, (0.15, 0.15, 0.15))], ruta='scale')
visible(contador, desde=c0 - 2, hasta=n1)
def poner_contador(f):
    k = max(0.0, min(1.0, (f - c0) / (c1 - c0))); k = 1 - (1 - k) ** 3
    tc_.body = f'{round(69 * k)}%'

# ---------- luces ----------
def luz(nombre, loc, potencia, tam, color=(1, 1, 1), mira=(0, 0, 0)):
    d = bpy.data.lights.new(nombre, 'AREA'); d.energy = potencia; d.size = tam; d.color = color
    o = bpy.data.objects.new(nombre, d); o.location = loc; sc.collection.objects.link(o)
    dirv = Vector(mira) - Vector(loc); o.rotation_euler = dirv.to_track_quat('-Z', 'Y').to_euler()
    return o
luz('Clave', (-4.8, -0.6, 6.0), 300, 3.0, mira=(0, 0, 0.6))
luz('Contra', (3.0, 3.2, 4.0), 380, 1.6, (0.85, 0.9, 1.0), mira=(0, 0, 1.0))
barra = luz('Barra', (1.8, -2.6, 5.5), 3, 0.3, mira=(0, 0.2, 1.6)); barra.data.shape = 'RECTANGLE'; barra.data.size_y = 5.0

# ---------- cámara: cada clave dice dónde está y a qué mira ----------
cd = bpy.data.cameras.new('Cam'); cd.lens = 50; cd.sensor_fit = 'VERTICAL'; cd.sensor_height = 36
cam = bpy.data.objects.new('Cam', cd); sc.collection.objects.link(cam); sc.camera = cam
cam.rotation_mode = 'QUATERNION'
cd.dof.use_dof = True; cd.dof.aperture_fstop = 2.8
for fr, fs in ((1, 5.0), (90, 5.0), (104, 2.8)):           # en el gancho, más profundidad de campo: cartas y número nítidos
    cd.dof.aperture_fstop = fs; cd.dof.keyframe_insert('aperture_fstop', frame=fr)
foco = vacio('Foco'); cd.dof.focus_object = foco
def mirar(pos, obj, rodar=0.0):
    """Rotación de la cámara en pos mirando a obj (con giro 'rodar' en grados alrededor de la mirada)."""
    f = (Vector(obj) - Vector(pos)).normalized()
    arriba = Vector((0, 0, 1)) if abs(f.z) < 0.97 else Vector((0, 1, 0))
    z = -f; x = arriba.cross(z).normalized(); y = z.cross(x)
    q = Matrix((x, y, z)).transposed().to_quaternion()
    return q @ Quaternion((0, 0, 1), math.radians(rodar))
def frente(f, d, u=0.5, v=0.5, lado=0.0, alto=0.0, sube=0.0, rodar=0.0):
    """Cámara frente a la pantalla en el fotograma f, a distancia d del punto (u, v), desplazada 'lado'/'alto' en el plano
    de la pantalla; 'sube' apunta por encima del punto (el móvil queda más abajo y deja sitio a los subtítulos)."""
    r, a_, n = ejes(f); p = mundo(f, punto_pantalla(u, v, 0))
    pos = p + n * d + r * lado + a_ * alto
    return f, tuple(pos), tuple(p + a_ * sube), rodar
GANAS_UV = uv_caja(*P.caja_pantalla('ganas'))
S = 0.3            # cuánto se apunta por encima en los planos generales
CAM = [
    (1, (-0.62, -5.1, 3.35), (-0.67, -1.75, 0.3), 0), (56, (-0.64, -4.75, 2.95), (-0.67, -1.95, 0.42), 0),   # gancho: las cartas y el móvil encima
    (74, (-0.5, -3.9, 2.55), (-0.55, -1.75, 0.45), 0), frente(g0, 2.6, sube=S), frente(g1, 2.9, lado=-0.3, sube=S),
    frente(132, 2.9, lado=-1.2, alto=-0.5, sube=0.2, rodar=-4), frente(170, 2.7, lado=-0.5, alto=-0.2, sube=0.25),
    frente(188, 2.8, sube=0.15), frente(197, 0.95), frente(198, 0.9),
    frente(214, 1.55, *GANAS_UV, sube=0.05), frente(240, 1.9, *GANAS_UV, lado=0.15, sube=-0.05),
    frente(268, 1.6, OUTS_UV[0], OUTS_UV[1] - 0.05, sube=0.12), frente(292, 3.0, sube=S),
    frente(v1, 3.0, lado=0.15, sube=S, rodar=3), frente(346, 1.9, *NODO_UV, lado=0.1, sube=0.12),
    frente(370, 1.8, NODO_UV[0] + 0.15, NODO_UV[1], lado=0.3, sube=0.1), frente(384, 2.8, sube=S),
    (404, (0.0, -0.1, 3.4), (0.0, -0.1, 0.0), -14), (480, (0.05, -0.1, 3.6), (0.05, -0.1, 0.0), 12),
    frente(500, 3.0, lado=-0.7, alto=-0.4, sube=S), frente(526, 1.7, *uv_caja(*P.caja_pantalla('correctas')), lado=0.2, sube=0.05),
    frente(552, 2.0, 0.5, 0.55, lado=0.1, sube=0.1), frente(578, 3.0, sube=S),
    frente(606, 3.9, sube=0.72), frente(G.TOTAL, 3.6, sube=0.68),
]
cam_q = None
for f, pos, obj, rodar in CAM:
    q = mirar(pos, obj, rodar)
    if cam_q is not None and cam_q.dot(q) < 0: q.negate()      # el camino corto entre giros
    cam_q = q
    cam.location = pos; cam.keyframe_insert('location', frame=f)
    cam.rotation_quaternion = q; cam.keyframe_insert('rotation_quaternion', frame=f)
    foco.location = obj; foco.keyframe_insert('location', frame=f)
for ob in (cam, foco):
    for fc in curvas(ob):
        for k in fc.keyframe_points: k.interpolation = 'BEZIER'; k.handle_left_type = k.handle_right_type = 'AUTO_CLAMPED'
# Atravesar la pantalla: el último tramo hacia dentro va rápido (corte limpio en CORTE_ANALISIS)

# ---------- render ----------
w = bpy.data.worlds.new('Mundo'); w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.002, 0.002, 0.0025, 1)
sc.world = w
r = sc.render
r.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = args.muestras; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.03
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.max_bounces = 3; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.cycles.blur_glossy = 1.0
if args.hilos: r.threads_mode = 'FIXED'; r.threads = args.hilos
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
r.resolution_x = args.ancho; r.resolution_y = round(args.ancho * 16 / 9); r.resolution_percentage = 100
r.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'

tiempos = {}
LISTA = [int(x) for x in args.lista.split(',')] if args.lista else range(args.desde, args.hasta + 1, args.cada)
for f in LISTA:
    tex_pant.image.filepath = P.ruta(f); tex_pant.image.reload()
    sc.frame_set(f); poner_contador(f); colocar_haz()
    r.filepath = os.path.join(args.salida, f'f{f:04d}.png')
    t = time.time(); bpy.ops.render.render(write_still=True); tiempos[f] = round(time.time() - t, 2)
    print(f'fotograma {f}: {tiempos[f]} s', flush=True)
json.dump(tiempos, open(os.path.join(args.salida, f'tiempos_{args.desde}.json'), 'w'))
