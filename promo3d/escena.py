# Escena 3D del vídeo promocional de RÍO: mesa de póker de fieltro granate vista desde arriba, fichas y cartas,
# y un móvil con la app real en pantalla (pantalla.py) que se levanta de la mesa. Tiempos en guion.py.
# Usa Blender como librería de Python (pip install bpy) y renderiza con Cycles en CPU.
# Uso: python3.11 promo3d/escena.py --salida DIR [--ancho 720] [--muestras 8] [--desde 1] [--hasta 780] [--cada 1]
import bpy, bmesh, math, os, sys, time, json, argparse
from mathutils import Matrix, Vector, Quaternion, Euler

AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import guion as G
import pantalla as P
import recursos as RC
HAY_PH = RC.hay()                  # recursos CC0 de Poly Haven (HDRI y texturas reales); sin ellos, todo procedural como antes
if not HAY_PH: print('AVISO: faltan los recursos de Poly Haven (python3.11 promo3d/recursos.py): se usa la versión procedural', flush=True)

CAP = os.path.join(AQUI, '..', 'salida', 'promo3d')
TEX = os.path.join(CAP, 'tex')
ROJO = (0.78, 0.03, 0.06)   # #E5304A en lineal
EXPOSICION = 0.0             # AgX comprime las luces: se sube un poco la exposición
HDRI_FUERZA, HDRI_GIRO = 0.12, 0
BRILLO_PANT = 1.3            # con AgX el blanco 1.0 sale gris: la pantalla brilla algo más para que la app se vea como es

a = argparse.ArgumentParser()
a.add_argument('--salida', required=True)
a.add_argument('--ancho', type=int, default=720)
a.add_argument('--muestras', type=int, default=128)   # vídeo: 128-256 con OIDN; pruebas rápidas: 16
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
sc.frame_start, sc.frame_end = 1, G.ESCENA_TOTAL

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

def tex_ph(N, L, nombre, mapa, escala, coord_out, color=True):
    """Mapa de una textura de Poly Haven (recursos.py) repetida cada 1/escala unidades."""
    t = N.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(RC.ruta_tex(nombre, mapa))
    if not color: t.image.colorspace_settings.name = 'Non-Color'
    mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (escala, escala, escala)
    L.new(coord_out, mp.inputs['Vector']); L.new(mp.outputs['Vector'], t.inputs['Vector']); return t
if HAY_PH:                        # tela de lana real (Poly Haven): su dibujo modula el granate, y su relieve y rugosidad
    E_TELA = 0.55                 # una repetición cada ~1,8 unidades (~18 cm a escala)
    dif = tex_ph(N, L, 'caban', 'diff', E_TELA, coord.outputs['Object'])
    bw = N.new('ShaderNodeRGBToBW'); L.new(dif.outputs['Color'], bw.inputs['Color'])
    con = N.new('ShaderNodeMapRange'); con.inputs['From Min'].default_value = 0.05; con.inputs['From Max'].default_value = 0.35
    con.inputs['To Min'].default_value = 0.65; con.inputs['To Max'].default_value = 1.35; L.new(bw.outputs['Val'], con.inputs['Value'])
    tinte = N.new('ShaderNodeMix'); tinte.data_type = 'RGBA'; tinte.blend_type = 'MULTIPLY'; tinte.inputs['Factor'].default_value = 1.0
    L.new(rampa.outputs['Color'], tinte.inputs[6]); L.new(con.outputs['Result'], tinte.inputs[7]); L.new(tinte.outputs[2], Pb.inputs['Base Color'])
    nor = tex_ph(N, L, 'caban', 'nor_gl', E_TELA, coord.outputs['Object'], color=False)
    nm = N.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 0.8; L.new(nor.outputs['Color'], nm.inputs['Color'])
    L.new(nm.outputs['Normal'], bump.inputs['Normal'])                    # el grano fino va encima del relieve de la tela
    ru = tex_ph(N, L, 'caban', 'rough', E_TELA, coord.outputs['Object'], color=False)
    rr = N.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.82; rr.inputs['To Max'].default_value = 1.0
    L.new(ru.outputs['Color'], rr.inputs['Value']); L.new(rr.outputs['Result'], Pb.inputs['Roughness'])
    Pb.inputs['Sheen Weight'].default_value = 0.45; Pb.inputs['Sheen Roughness'].default_value = 0.4
if G.TIKTOK:                     # TikTok: sin mesa de póker; una superficie de estudio gris muy oscura, algo satinada
    rampa.color_ramp.elements[0].color = (0.006, 0.006, 0.007, 1); rampa.color_ramp.elements[1].color = (0.016, 0.016, 0.018, 1)
    Pb.inputs['Sheen Weight'].default_value = 0.0; Pb.inputs['Roughness'].default_value = 0.38; bump.inputs['Strength'].default_value = 0.05
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
    m, _ = material_imagen('Ficha_' + color, os.path.join(TEX, f'ficha_{color}.png'), rugosidad=0.5, coat=0.15, vector=vec)
    N, L = m.node_tree.nodes, m.node_tree.links; p = N['Principled BSDF']   # arcilla: poro fino y leve desgaste en el canto
    c = N.new('ShaderNodeTexCoord'); poro = N.new('ShaderNodeTexNoise'); poro.inputs['Scale'].default_value = 260; poro.inputs['Detail'].default_value = 6
    L.new(c.outputs['Object'], poro.inputs['Vector'])
    bu = N.new('ShaderNodeBump'); bu.inputs['Strength'].default_value = 0.18; bu.inputs['Distance'].default_value = 0.002
    L.new(poro.outputs['Fac'], bu.inputs['Height']); L.new(bu.outputs['Normal'], p.inputs['Normal'])
    ru = N.new('ShaderNodeMapRange'); ru.inputs['To Min'].default_value = 0.42; ru.inputs['To Max'].default_value = 0.62
    L.new(poro.outputs['Fac'], ru.inputs['Value']); L.new(ru.outputs['Result'], p.inputs['Roughness'])
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
for x, y, c in ((0.55, 2.0, 'roja'), (-1.95, -2.95, 'negra'), (1.9, 0.3, 'blanca'), (-2.0, 0.6, 'roja'), (0.95, -3.3, 'gris')):
    ficha(c, x, y, 0, x * 3)
# Fichas que caen sobre la primera pila en el gancho, y junto al móvil en la partida (suenan en audio.py)
def cae(color, x, y, n, f, giro):
    o = ficha(color, x, y, n, giro); z = H_FICHA / 2 + n * H_FICHA
    animar(o, [(f - 9, (x + 0.15, y - 0.4, z + 1.6)), (f, (x, y, z))], interp='LINEAR')
    animar(o, [(f - 9, (35, -20, giro * 57)), (f, (0, 0, giro * 57))], ruta='rotation_euler', interp='LINEAR')
for i in range(4):                # (antes caían en el gancho; ahora ya están en la pila, en la misma posición final)
    ficha(['roja', 'negra', 'roja', 'blanca'][i], 1.15, 1.55, 6 + i, math.radians(i * 1.3 * 57))
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
    p = N['Principled BSDF']; p.inputs['Roughness'].default_value = 0.34; p.inputs['Coat Weight'].default_value = 0.4   # satinada
    p.inputs['Coat Roughness'].default_value = 0.14
    tc = N.new('ShaderNodeTexCoord')
    lino = N.new('ShaderNodeTexNoise'); lino.inputs['Scale'].default_value = 600; L.new(tc.outputs['Object'], lino.inputs['Vector'])  # acabado «lino» del cartón
    bl = N.new('ShaderNodeBump'); bl.inputs['Strength'].default_value = 0.06; bl.inputs['Distance'].default_value = 0.001
    L.new(lino.outputs['Fac'], bl.inputs['Height']); L.new(bl.outputs['Normal'], p.inputs['Normal'])
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
    if not boca_arriba: o.delta_rotation_euler = (0, math.pi, 0) if tumbada else (0, 0, math.pi)   # boca abajo: se gira el objeto, no la malla (el material mira la normal de la malla)
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
cartas_vuelan = {c: carta(c, x, y, g) for c, ((x, y), g, _, _) in VUELAN.items()}
# Gancho: tus dos cartas, boca abajo, esperando en la mesa vacía (ángulo 0: nadie las mira);
# se dan la vuelta mientras vuelan al móvil. Va en un vacío padre y en los «delta»: al acabar valen 0 y lo demás no cambia.
def esquina(c, dx, dy):
    (x, y), giro = VUELAN[c][0], VUELAN[c][1]
    return Vector((x, y, 0)) + Matrix.Rotation(math.radians(giro), 3, 'Z') @ Vector((dx, dy, 0))
for c, (a0, a1, a2, a3), ang in (('Ah', G.MIRA_AS, 0), ('Kh', G.MIRA_REY, 0)):
    o = cartas_vuelan[c]; (x, y), giro = VUELAN[c][0], VUELAN[c][1]
    eje = Matrix.Rotation(math.radians(giro), 3, 'Z') @ Vector((1, 0, 0))
    p = esquina(c, 0, CARTA_H / 2); p.z = 0                                   # borde de atrás, sobre el fieltro
    mano = vacio('Mira_' + c); mano.rotation_mode = 'QUATERNION'; o.parent = mano
    for f, a in ((1, 0), (a0, 0), (a1, ang), (a2, ang), (a3, 0)):
        R = Matrix.Rotation(math.radians(-a), 3, eje)
        mano.location = p - R @ p; mano.keyframe_insert('location', frame=f)
        mano.rotation_quaternion = R.to_quaternion(); mano.keyframe_insert('rotation_quaternion', frame=f)
    vuela = VUELAN[c][2] - 16 + (2 if c == 'Kh' else 0)
    for f, r in ((1, (0, 180, 0)), (vuela, (0, 180, 0)), (vuela + 8, (0, 0, 0))):
        o.delta_rotation_euler = [math.radians(v) for v in r]; o.keyframe_insert('delta_rotation_euler', frame=f)

# ---------- móvil ----------
movil = vacio('Movil'); movil.rotation_mode = 'YXZ'      # Y: gira sobre su eje largo · X: inclinación · Z: guiño
pivote = vacio('Pivote', movil); pivote.rotation_euler = (math.radians(-90), 0, 0)   # el móvil se modela mirando a -Y
GR = 0.085                                   # grosor
cuerpo = rectangulo_redondeado('Cuerpo', 0.78, 1.62, 0.12, grosor=GR, segmentos=12)
cuerpo.location = (0, -GR / 2, 0); cuerpo.parent = pivote
bev = cuerpo.modifiers.new('Bisel', 'BEVEL'); bev.width = 0.022; bev.segments = 5; bev.limit_method = 'ANGLE'; bev.harden_normals = True
for f in cuerpo.data.polygons: f.use_smooth = True
def titanio():
    """Titanio con micro-rayado: brillo anisótropo a lo largo del móvil y rugosidad que varía en rayas finas."""
    m = material('Titanio', base=(0.05, 0.05, 0.055), metal=1.0, rugosidad=0.22); N, L = m.node_tree.nodes, m.node_tree.links
    p = N['Principled BSDF']; p.inputs['Anisotropic'].default_value = 0.55
    tg = N.new('ShaderNodeTangent'); tg.direction_type = 'RADIAL'; tg.axis = 'X'   # en la tapa de atrás: a lo largo del móvil
    L.new(tg.outputs['Tangent'], p.inputs['Tangent'])
    c = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (900, 900, 6)   # rayas a lo largo
    ra = N.new('ShaderNodeTexNoise'); ra.inputs['Detail'].default_value = 2
    L.new(c.outputs['Object'], mp.inputs['Vector']); L.new(mp.outputs['Vector'], ra.inputs['Vector'])
    rr = N.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.17; rr.inputs['To Max'].default_value = 0.3
    L.new(ra.outputs['Fac'], rr.inputs['Value']); L.new(rr.outputs['Result'], p.inputs['Roughness'])
    return m
cuerpo.data.materials.append(titanio())
marco = rectangulo_redondeado('Marco', 0.75, 1.59, 0.105)
marco.location = (0, -GR / 2 - 0.0015, 0); marco.parent = pivote
marco.data.materials.append(material('Cristal negro', rugosidad=0.04, coat=1.0))
PW = 0.72; PH = PW * P.SH / P.SW
pantalla = rectangulo_redondeado('Pantalla', PW, PH, 0.085)
pantalla.location = (0, -GR / 2 - 0.0025, 0); pantalla.parent = pivote
m_pant, tex_pant = material_imagen('Pantalla', P.ruta(1) if os.path.exists(P.ruta(1)) else os.path.join(CAP, 'inicio.png'), emision=1.0, rugosidad=0.03)
m_pant.node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value = 0.2       # cristal: reflejo suave del HDRI
m_pant.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = BRILLO_PANT
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
g0, g1 = G.GIRO_INICIO; v0, v1 = G.VUELTA_CARRERA
POSES = [
    (1, MESA, (0, 0, 0)), (80, MESA, (0, 0, 0)), (g0, ARRIBA, (INCL, 0, 4)),     # gancho: apagado en la mesa; se enciende y se levanta
    (g1, ARRIBA, (INCL, 360, -3)), (150, ARRIBA, (INCL, 360, 6)), (188, ARRIBA, (INCL, 360, 0)),
    (198, ARRIBA, (INCL, 360, 0)), (250, ARRIBA, (INCL, 360, -5)), (292, ARRIBA, (INCL, 360, -2)),
    (v0, ARRIBA, (INCL, 360, -2)), (v1, ARRIBA, (INCL, 720, 4)), (360, ARRIBA, (INCL, 720, 8)), (382, ARRIBA, (INCL, 720, 4)),
    (404, MESA, (0, 720, -10)), (480, MESA, (0, 720, -10)),
    (500, ARRIBA, (INCL + 4, 720, 8)), (540, ARRIBA, (INCL, 720, 2)), (578, ARRIBA, (INCL, 720, -4)),
    (606, (0, 0.2, 1.45), (INCL + 6, 720, 0)), (G.ESCENA_TOTAL, (0, 0.2, 1.45), (INCL + 6, 720, 3)),
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
    if G.ANUNCIO:                 # anuncio: la carta vuela más baja y aterriza plana justo en su hueco de la pantalla
        u, v = G.HUECOS[c]
        sc.frame_set(llega); R = (pivote.matrix_world.to_3x3().normalized() @ Matrix.Rotation(math.radians(90), 3, 'X'))
        fin = mundo(llega, punto_pantalla(u, v, 0.006)); antes = mundo(llega - 3, punto_pantalla(u, v, 0.07))
        medio = Vector((x, y, Z_CARTA)).lerp(fin, 0.6) + Vector((0, -0.12, 0.28))   # arco corto y cerca del móvil (no tapa la cámara)
        e_mid = Vector((math.radians(INCL - 30), math.radians(20 if x < 0 else -20), math.radians(giro / 2)))
        e_fin = R.to_euler('XYZ', Euler(e_mid))
        animar(o, [(sale, (x, y, Z_CARTA)), (sale + 7, medio), (llega - 3, antes), (llega, fin)])
        animar(o, [(sale, (0, 0, giro)), (sale + 7, [math.degrees(a) for a in e_mid]), (llega - 3, [math.degrees(a) for a in e_fin]),
                   (llega, [math.degrees(a) for a in e_fin])], ruta='rotation_euler')
        k = G.ESCALA_HUECO; animar(o, [(sale + 7, (0.5,) * 3), (llega - 3, (k * 1.08,) * 3), (llega, (k,) * 3)], ruta='scale')
        visible(o, hasta=llega - 1)
        continue
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

# ---------- luces ----------
def luz(nombre, loc, potencia, tam, color=(1, 1, 1), mira=(0, 0, 0)):
    d = bpy.data.lights.new(nombre, 'AREA'); d.energy = potencia; d.size = tam; d.color = color
    o = bpy.data.objects.new(nombre, d); o.location = loc; sc.collection.objects.link(o)
    dirv = Vector(mira) - Vector(loc); o.rotation_euler = dirv.to_track_quat('-Z', 'Y').to_euler()
    return o
clave = luz('Clave', (-4.8, -0.6, 6.0), 300, 3.0, mira=(0, 0, 0.6))
contra = luz('Contra', (3.0, 3.2, 4.0), 380, 1.6, (0.85, 0.9, 1.0), mira=(0, 0, 1.0))
# Gancho: luz de sala de póker (una lámpara cálida encima de las cartas, el resto en penumbra); a partir del 104, la de siempre
dlamp = bpy.data.lights.new('Lampara', 'SPOT'); dlamp.spot_size = math.radians(60); dlamp.spot_blend = 0.8
dlamp.color = (1.0, 0.8, 0.6); dlamp.shadow_soft_size = 0.25
lampara = bpy.data.objects.new('Lampara', dlamp); sc.collection.objects.link(lampara); lampara.location = (-0.85, -2.25, 3.0)
for ob, valores in ((clave.data, ((1, 70), (86, 70), (104, 300))), (contra.data, ((1, 90), (86, 90), (104, 380))),
                    (dlamp, ((1, 650), (86, 650), (104, 0)))):
    if not G.TIKTOK: valores = {clave.data: ((1, 28), (G.LAMPARA, 28), (G.LAMPARA + 6, 70), (86, 70), (104, 300)),
                                contra.data: ((1, 38), (G.LAMPARA, 38), (G.LAMPARA + 6, 90), (86, 90), (104, 380)),
                                dlamp: ((1, 0), (104, 0))}[ob]          # apagada: la del gancho es la colgante
    for fr, e in valores: ob.energy = e; ob.keyframe_insert('energy', frame=fr)
# Gancho (Instagram): sala en penumbra; una lámpara colgante encima de la mesa se enciende con un parpadeo (clic en G.LAMPARA)
# y al fondo brillan, desenfocadas, las lámparas de otras mesas. Todo se oculta antes del 86: lo demás no cambia.
if not G.TIKTOK:
    LX, LY, LZ = -0.4, -1.45, 2.35                          # borde de abajo de la pantalla de la lámpara
    dcol = bpy.data.lights.new('Colgante', 'SPOT'); dcol.spot_size = math.radians(100); dcol.spot_blend = 0.6
    dcol.color = (1.0, 0.8, 0.6); dcol.shadow_soft_size = 0.06
    colgante = bpy.data.objects.new('Colgante', dcol); sc.collection.objects.link(colgante); colgante.location = (LX, LY, LZ + 0.08)
    l0 = G.LAMPARA; PARPADEO = ((1, 0), (l0, 1), (l0 + 1, 0.05), (l0 + 3, 0.7), (l0 + 4, 0.15), (l0 + 6, 1))
    for fr, k in PARPADEO: dcol.energy = 380 * k; dcol.keyframe_insert('energy', frame=fr)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=64, radius1=0.42, radius2=0.1, depth=0.34)
    me = bpy.data.meshes.new('Tulipa'); bm.to_mesh(me); bm.free()
    for f_ in me.polygons: f_.use_smooth = True
    tulipa = bpy.data.objects.new('Tulipa', me); sc.collection.objects.link(tulipa); tulipa.location = (LX, LY, LZ + 0.17)
    sol = tulipa.modifiers.new('g', 'SOLIDIFY'); sol.thickness = 0.012
    mt = material('Tulipa', base=(0.012, 0.012, 0.014), metal=0.9, rugosidad=0.3)
    if HAY_PH:                    # chapa real (Poly Haven): rugosidad y relieve del metal, pintada casi negra
        N, L = mt.node_tree.nodes, mt.node_tree.links; p_ = N['Principled BSDF']; co = N.new('ShaderNodeTexCoord')
        ru = tex_ph(N, L, 'metal_plate', 'rough', 1.6, co.outputs['Object'], color=False)
        rr = N.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.22; rr.inputs['To Max'].default_value = 0.5
        L.new(ru.outputs['Color'], rr.inputs['Value']); L.new(rr.outputs['Result'], p_.inputs['Roughness'])
        no = tex_ph(N, L, 'metal_plate', 'nor_gl', 1.6, co.outputs['Object'], color=False)
        nm = N.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 0.5
        L.new(no.outputs['Color'], nm.inputs['Color']); L.new(nm.outputs['Normal'], p_.inputs['Normal'])
        p_.inputs['Metallic'].default_value = 0.7; p_.inputs['Coat Weight'].default_value = 0.3; p_.inputs['Coat Roughness'].default_value = 0.2
    tulipa.data.materials.append(mt)
    tulipa.data.materials.append(material('Tulipa dentro', base=(0.8, 0.75, 0.68), rugosidad=0.6)); sol.material_offset = 1
    cable = bpy.data.objects.new('Cable', bpy.data.meshes.new('Cable')); sc.collection.objects.link(cable)
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.008, radius2=0.008, depth=6.0); bm.to_mesh(cable.data); bm.free()
    cable.location = (LX, LY, LZ + 0.34 + 3.0); cable.data.materials.append(tulipa.data.materials[0])
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.07)
    bombilla = bpy.data.objects.new('Bombilla', bpy.data.meshes.new('Bombilla')); bm.to_mesh(bombilla.data); bm.free()
    sc.collection.objects.link(bombilla); bombilla.location = (LX, LY, LZ + 0.1)
    mb = bpy.data.materials.new('Bombilla'); mb.use_nodes = True; nb = mb.node_tree.nodes
    nb.remove(nb['Principled BSDF']); em = nb.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1.0, 0.72, 0.42, 1)
    mb.node_tree.links.new(em.outputs[0], nb['Material Output'].inputs['Surface']); bombilla.data.materials.append(mb)
    for fr, k in PARPADEO: em.inputs['Strength'].default_value = 40 * k; em.inputs['Strength'].keyframe_insert('default_value', frame=fr)
    for fc in mb.node_tree.animation_data.action.fcurves if hasattr(mb.node_tree.animation_data.action, 'fcurves') else []:
        for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
    for ob in (clave.data, contra.data, dcol):
        for fc in curvas(ob):
            for k in fc.keyframe_points:
                if k.co[0] <= l0 + 6: k.interpolation = 'CONSTANT'
    fondo = [tulipa, cable, bombilla, colgante]
    me_b = bpy.data.meshes.new('Lejana'); bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.22); bm.to_mesh(me_b); bm.free()
    ml = bpy.data.materials.new('Lejana'); ml.use_nodes = True; nl = ml.node_tree.nodes
    nl.remove(nl['Principled BSDF']); el = nl.new('ShaderNodeEmission'); el.inputs['Color'].default_value = (1.0, 0.62, 0.32, 1)
    el.inputs['Strength'].default_value = 5; ml.node_tree.links.new(el.outputs[0], nl['Material Output'].inputs['Surface']); me_b.materials.append(ml)
    for x, y, z in ((-3.4, 7.5, 2.0), (2.8, 9.5, 3.1), (6.5, 6.5, 2.4), (-7.5, 11.0, 3.4), (0.9, 15.0, 2.2)):
        o = bpy.data.objects.new('Lejana', me_b); sc.collection.objects.link(o); o.location = (x, y, z); fondo.append(o)
        dlj = bpy.data.lights.new('LejanaLuz', 'SPOT'); dlj.energy = 120; dlj.spot_size = math.radians(70); dlj.color = (1.0, 0.75, 0.5)
        lj = bpy.data.objects.new('LejanaLuz', dlj); sc.collection.objects.link(lj); lj.location = (x, y, z - 0.05)
        fondo.append(lj)
    # Neblina muy suave en la sala: se ve el cono de luz de la lámpara. Es cara: solo en el gancho
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); niebla = bpy.data.objects.new('Niebla', bpy.data.meshes.new('Niebla'))
    bm.to_mesh(niebla.data); bm.free(); sc.collection.objects.link(niebla); niebla.location = (0, 4, 3); niebla.scale = (30, 30, 6.2)
    mn = bpy.data.materials.new('Niebla'); mn.use_nodes = True; nn = mn.node_tree.nodes; nn.remove(nn['Principled BSDF'])
    vs = nn.new('ShaderNodeVolumeScatter'); vs.inputs['Density'].default_value = 0.006; vs.inputs['Anisotropy'].default_value = 0.35
    mn.node_tree.links.new(vs.outputs[0], nn['Material Output'].inputs['Volume']); niebla.data.materials.append(mn)
    niebla.visible_shadow = False; fondo.append(niebla)
    for o in fondo: visible(o, hasta=85)
barra = luz('Barra', (1.8, -2.6, 5.5), 3, 0.3, mira=(0, 0.2, 1.6)); barra.data.shape = 'RECTANGLE'; barra.data.size_y = 5.0

# ---------- cámara: cada clave dice dónde está y a qué mira ----------
cd = bpy.data.cameras.new('Cam'); cd.lens = 50; cd.sensor_fit = 'VERTICAL'; cd.sensor_height = 36
cam = bpy.data.objects.new('Cam', cd); sc.collection.objects.link(cam); sc.camera = cam
cam.rotation_mode = 'QUATERNION'
cd.dof.use_dof = True; cd.dof.aperture_fstop = 2.8
cd.dof.aperture_blades = 7; cd.dof.aperture_rotation = math.radians(12)   # bokeh de lente real (heptágono suave)
for fr, fs in (((1, 2.0), (66, 2.0), (90, 2.8), (104, 2.8)) if G.TIKTOK else ((1, 0.25), (36, 0.4), (66, 2.0), (90, 2.8), (104, 2.8))):   # gancho en macro: poca profundidad de campo, como una lente de cine
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
# Gancho: cámara macro casi a ras del fieltro, a mano (con un leve temblor), primero en la esquina del A♥ y luego en la del K♥;
# después sube hacia el móvil, que se enciende sobre la mesa
import random as _r; _r.seed(4)
def _t(v, k=0.004): return tuple(c + _r.uniform(-k, k) for c in v)
c1, c2 = esquina('Ah', -CARTA_W / 2, -CARTA_H / 2), esquina('Kh', -CARTA_W / 2, -CARTA_H / 2)
GANCHO = [(f, _t(c1 + Vector(d), 0.006), tuple(c1 + Vector((0.2, 0.18, 0.2))), 0) for f, d in
          ((1, (0.55, -2.15, 0.36)), (14, (0.52, -2.05, 0.34)), (28, (0.5, -1.98, 0.33)), (36, (0.5, -1.96, 0.33)))]
GANCHO += [(f, _t(c2 + Vector(d), 0.006), tuple(c2 + Vector((0.2, 0.18, 0.2))), 0) for f, d in ((50, (0.45, -2.0, 0.33)), (60, (0.42, -1.94, 0.32)), (68, (0.41, -1.9, 0.32)))]
GANCHO += [(82, (0.12, -1.9, 0.8), (0.0, -0.35, 0.06), 0)]
# Instagram: «la mesa vacía». Plano desde el borde de la mesa hacia la lámpara, que se enciende; la cámara avanza despacio
# y baja a ras del fieltro, entre las fichas y tus cartas boca abajo, hasta el móvil. Las claves de la cámara siguen siendo
# las de antes (el suavizado de Blender arrastraría cualquier cambio a los fotogramas de después): este recorrido lo pone
# un vacío padre, fotograma a fotograma, que en el 82 vale 0 (ver «Grúa» más abajo)
SALA = [(1, (0.5, -5.6, 1.2), (-0.3, -1.5, 1.75)), (14, (0.47, -5.35, 1.13), (-0.3, -1.5, 1.7)),
        (36, (0.4, -4.3, 0.78), (-0.2, -1.3, 0.7)), (60, (0.24, -3.1, 0.52), (-0.05, -0.8, 0.14)), GANCHO[-1][:3]]
if G.TIKTOK:                      # TikTok: sin cartas; primer plano del móvil en la mesa, que se enciende con el análisis
    def _pp(f, u, v): return tuple(mundo(f, punto_pantalla(u, v, 0)))
    gu, gv = uv_caja(*P.caja_pantalla('ganas'))
    GANCHO = [(1, _t(Vector((0.62, -1.45, 0.2)), 0.006), (0.05, -0.2, 0.04), 0), (20, _t(Vector((0.5, -1.25, 0.26)), 0.006), (0.04, -0.15, 0.05), 0),
              (44, _t(Vector((0.22, -0.95, 0.42)), 0.006), _pp(44, gu, gv), 0), (62, _t(Vector((0.18, -0.85, 0.46)), 0.006), _pp(62, gu, gv), 0),
              (82, (0.12, -1.9, 0.8), (0.0, -0.35, 0.06), 0)]
# Teleobjetivo en el gancho (85 mm: menos deformación, como un plano de cine); a partir del 92, el de siempre
for fr, ln in (((1, 85), (70, 85), (92, 50)) if G.TIKTOK else ((1, 38), (60, 42), (92, 50))): cd.lens = ln; cd.keyframe_insert('lens', frame=fr)
# Luz de relleno suave y baja: ilumina la cara de la carta cuando se levanta
drel = bpy.data.lights.new('Relleno', 'AREA'); drel.size = 0.35; drel.color = (1.0, 0.9, 0.82)
relleno = bpy.data.objects.new('Relleno', drel); sc.collection.objects.link(relleno)
for fr, base in ((1, c1), (36, c1), (48, c2), (72, c2)):
    relleno.location = base + Vector((0.15, -0.75, 0.13)); relleno.keyframe_insert('location', frame=fr)
    relleno.rotation_euler = ((base + Vector((0.2, 0.2, 0.08))) - relleno.location).to_track_quat('-Z', 'Y').to_euler(); relleno.keyframe_insert('rotation_euler', frame=fr)
for fr, e in ((1, 2.5), (72, 2.5), (84, 0)): drel.energy = e if G.TIKTOK else 0; drel.keyframe_insert('energy', frame=fr)
if G.TIKTOK:
    for fr in (1, 72, 84): drel.energy = 0; drel.keyframe_insert('energy', frame=fr)
    lampara.location = (0.0, -0.35, 3.0)
CAM = [
    *GANCHO, frente(g0, 2.6, sube=S), frente(g1, 2.9, lado=-0.3, sube=S),
    frente(132, 2.9, lado=-1.2, alto=-0.5, sube=0.2, rodar=-4), frente(170, 2.7, lado=-0.5, alto=-0.2, sube=0.25),
    frente(188, 2.8, sube=0.15), frente(197, 0.95), frente(198, 0.9),
    frente(214, 1.55, *GANAS_UV, sube=0.05), frente(240, 1.9, *GANAS_UV, lado=0.15, sube=-0.05),
    frente(268, 1.6, OUTS_UV[0], OUTS_UV[1] - 0.05, sube=0.12), frente(292, 3.0, sube=S),
    frente(v1, 3.0, lado=0.15, sube=S, rodar=3), frente(346, 1.9, *NODO_UV, lado=0.1, sube=0.12),
    frente(370, 1.8, NODO_UV[0] + 0.15, NODO_UV[1], lado=0.3, sube=0.1), frente(384, 2.8, sube=S),
    (404, (0.0, -0.1, 3.4), (0.0, -0.1, 0.0), -14), (480, (0.05, -0.1, 3.6), (0.05, -0.1, 0.0), 12),
    frente(500, 3.0, lado=-0.7, alto=-0.4, sube=S), frente(526, 1.7, *uv_caja(*P.caja_pantalla('correctas')), lado=0.2, sube=0.05),
    frente(552, 2.0, 0.5, 0.55, lado=0.1, sube=0.1), frente(578, 3.0, sube=S),
    frente(606, 3.9, sube=0.72), frente(G.ESCENA_TOTAL, 3.6, sube=0.68),
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
# Grúa (Instagram): lleva la cámara (y el foco) del recorrido SALA a la clave original del 82; desde el 82 vale 0
if not G.TIKTOK:
    guia, guia_foco = vacio('Guia'), vacio('GuiaFoco'); guia.rotation_mode = 'QUATERNION'; q0 = None
    for f, pos, obj in SALA:
        q = mirar(pos, obj)
        if q0 is not None and q0.dot(q) < 0: q.negate()
        q0 = q; guia.location = pos; guia.rotation_quaternion = q; guia_foco.location = obj
        guia.keyframe_insert('location', frame=f); guia.keyframe_insert('rotation_quaternion', frame=f); guia_foco.keyframe_insert('location', frame=f)
    grua, grua_foco = vacio('Grua'), vacio('GruaFoco'); grua.rotation_mode = 'QUATERNION'
    fin = SALA[-1][0]; q0 = None; pasos = []
    for f in range(1, fin):
        sc.frame_set(f); M = guia.matrix_world @ cam.matrix_world.inverted()
        q = M.to_quaternion()
        if q0 is not None and q0.dot(q) < 0: q.negate()
        q0 = q; pasos.append((f, M.to_translation(), q, guia_foco.matrix_world.translation - foco.matrix_world.translation))
    pasos.append((fin, Vector(), Quaternion(), Vector()))
    for f, t, q, tf in pasos:
        grua.location = t; grua.rotation_quaternion = q; grua_foco.location = tf
        grua.keyframe_insert('location', frame=f); grua.keyframe_insert('rotation_quaternion', frame=f); grua_foco.keyframe_insert('location', frame=f)
    for ob in (grua, grua_foco):
        for fc in curvas(ob):
            for k in fc.keyframe_points: k.interpolation = 'LINEAR'
    cam.parent = grua; foco.parent = grua_foco
# Atravesar la pantalla: el último tramo hacia dentro va rápido (corte limpio en CORTE_ANALISIS)

# ---------- render ----------
w = bpy.data.worlds.new('Mundo'); w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.002, 0.002, 0.0025, 1)
if HAY_PH:                        # HDRI de un bar cálido: luz y reflejos suaves; la cámara sigue viendo el fondo negro
    WN, WL = w.node_tree.nodes, w.node_tree.links
    env = WN.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(RC.ruta_hdri())
    wco = WN.new('ShaderNodeTexCoord'); wmp = WN.new('ShaderNodeMapping'); wmp.inputs['Rotation'].default_value = (0, 0, math.radians(HDRI_GIRO))
    WL.new(wco.outputs['Generated'], wmp.inputs['Vector']); WL.new(wmp.outputs['Vector'], env.inputs['Vector'])
    luzh = WN.new('ShaderNodeBackground'); luzh.inputs['Strength'].default_value = HDRI_FUERZA; WL.new(env.outputs['Color'], luzh.inputs['Color'])
    lp = WN.new('ShaderNodeLightPath'); mx = WN.new('ShaderNodeMixShader')
    WL.new(lp.outputs['Is Camera Ray'], mx.inputs['Fac']); WL.new(luzh.outputs[0], mx.inputs[1]); WL.new(WN['Background'].outputs[0], mx.inputs[2])
    WL.new(mx.outputs[0], WN['World Output'].inputs['Surface'])
sc.world = w
r = sc.render
r.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = args.muestras; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.01
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'; sc.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
sc.cycles.max_bounces = 8; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.cycles.volume_bounces = 1; sc.cycles.volume_step_rate = 4.0
sc.cycles.blur_glossy = 0.3
if args.hilos: r.threads_mode = 'FIXED'; r.threads = args.hilos
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
r.resolution_x = args.ancho; r.resolution_y = round(args.ancho * 16 / 9); r.resolution_percentage = 100
r.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'   # color de cine (MEJORAS.md)
sc.view_settings.exposure = EXPOSICION

if G.TIKTOK:                      # TikTok: fuera cartas y fichas (lo marca como juego); el resto de la escena, igual
    for o in [o for o in bpy.data.objects if o.name.startswith(('carta_', 'ficha'))]: bpy.data.objects.remove(o, do_unlink=True)

# Gancho (Instagram): la cámara ve la mesa entera, así que se ocultan las cosas que esperan en el aire a escenas de después
# (fichas y cartas que caen o salen más tarde). Solo en los fotogramas del gancho: lo demás queda igual.
AIRE = []
if not G.TIKTOK:
    def colgado(o):
        p_ = o
        while p_ is not None:
            if p_ == movil: return True
            p_ = p_.parent
        return False
    for f in (1, 30, 60, 85):
        sc.frame_set(f)
        AIRE += [o for o in sc.objects if o.type == 'MESH' and o not in AIRE and not colgado(o)
                 and not o.name.startswith(('Tulipa', 'Cable', 'Bombilla', 'Lejana', 'Mesa', 'Niebla')) and o.matrix_world.translation.z > 0.3]
AIRE_ORIG = {o: o.hide_render for o in AIRE}           # (los que no tienen visibilidad animada)
AIRE_ANIM = {o for o in AIRE if o.animation_data and o.animation_data.action and any(fc.data_path == 'hide_render' for fc in curvas(o))}
tiempos = {}
LISTA = [int(x) for x in args.lista.split(',')] if args.lista else range(args.desde, args.hasta + 1, args.cada)
for f in LISTA:
    fo = G.orig(f)                                      # anuncio: instante de la escena (con decimales) para este fotograma
    tex_pant.image.filepath = P.ruta(round(fo)); tex_pant.image.reload()
    sc.frame_set(int(fo), subframe=fo - int(fo))
    r.motion_blur_shutter = 0.5 * max(0.3, G.orig(f + 1) - fo) if G.ANUNCIO else 0.5   # cámara lenta: menos estela
    for o in AIRE:
        if fo <= 85: o.hide_render = True
        elif o not in AIRE_ANIM: o.hide_render = AIRE_ORIG[o]
    r.filepath = os.path.join(args.salida, f'f{f:04d}.png')
    t = time.time(); bpy.ops.render.render(write_still=True); tiempos[f] = round(time.time() - t, 2)
    print(f'fotograma {f}: {tiempos[f]} s', flush=True)
json.dump(tiempos, open(os.path.join(args.salida, f'tiempos_{args.desde}.json'), 'w'))
