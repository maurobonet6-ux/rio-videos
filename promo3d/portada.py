# Render de portada: reutiliza la escena del vídeo en el fotograma F con cámara y lámpara propias.
import sys, os, json
F = int(os.environ.get('F', 240)); ANCHO = int(os.environ.get('ANCHO', 360)); MU = int(os.environ.get('MU', 16))
CAM = json.loads(os.environ['CAM']); LAMP = json.loads(os.environ['LAMP'])
src = open('promo3d/escena.py').read(); src = src[:src.index('tiempos = {}')]
sys.argv = ['promo3d/escena.py', '--salida', os.environ.get('DIR', '/tmp'), '--ancho', str(ANCHO), '--muestras', str(MU), '--lista', '1']
sys.path.insert(0, os.path.abspath('promo3d'))
g = {'__file__': os.path.abspath('promo3d/escena.py'), '__name__': '__main__'}
exec(compile(src, g['__file__'], 'exec'), g)
from mathutils import Vector
sc, cam, cd, foco = g['sc'], g['cam'], g['cd'], g['foco']
sc.frame_set(F)
g['tex_pant'].image.filepath = g['P'].ruta(F); g['tex_pant'].image.reload()
# lámpara y sala: visibles, encendidas, encima del móvil
lx, ly, lz = LAMP
for n, dz in (('Tulipa', 0.17), ('Cable', 0.34 + 3.0), ('Bombilla', 0.1), ('Colgante', 0.08)):
    o = g['bpy'].data.objects[n]; o.animation_data_clear(); o.hide_render = False; o.location = (lx, ly, lz + dz)
g['dcol'].animation_data_clear(); g['dcol'].energy = float(os.environ.get('LUZ', 380))
g['mb'].node_tree.animation_data_clear(); g['em'].inputs['Strength'].default_value = 40
for o in g['bpy'].data.objects:
    if o.name.startswith('Lejana'): o.animation_data_clear(); o.hide_render = False
for L, e in ((g['clave'].data, float(os.environ.get('CLAVE', 120))), (g['contra'].data, float(os.environ.get('CONTRA', 200)))):
    L.animation_data_clear(); L.energy = e
for o in list(g['bpy'].data.objects):
    if o.name.startswith('ficha') and o.matrix_world.translation.z > 0.3: o.hide_render = True
# cámara
pos, mira, lente, fs = CAM
for o in (cam, foco): o.animation_data_clear(); o.parent = None
cd.animation_data_clear(); cd.lens = lente; cd.dof.aperture_fstop = fs
cam.location = pos; cam.rotation_quaternion = g['mirar'](pos, mira)
foco.location = json.loads(os.environ.get('FOCO', json.dumps(mira)))
r = sc.render; r.resolution_x = ANCHO; r.resolution_y = round(ANCHO * 16 / 9)
r.filepath = os.environ.get('OUT', 'portada.png')
g['bpy'].ops.render.render(write_still=True)
