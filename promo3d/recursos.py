# Descarga los recursos CC0 de Poly Haven (uso comercial libre, sin atribución) que usan escena.py y portada.py:
# HDRI de un bar cálido (luz y reflejos), tela de lana para el fieltro y chapa de metal para la lámpara. Ver MEJORAS.md.
# Uso: python3.11 promo3d/recursos.py   (solo baja lo que falte; se guarda en promo3d/tex_ph/)
import os, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(AQUI, 'tex_ph')
BASE = 'https://dl.polyhaven.org/file/ph-assets'
HDRI = 'warm_bar'
TEXTURAS = {'caban': '2k', 'metal_plate': '1k'}      # fieltro (lana) y lámpara
MAPAS = {'diff': 'Diffuse', 'nor_gl': 'nor_gl', 'rough': 'Rough'}

def ruta_hdri(): return os.path.join(DIR, f'{HDRI}_2k.hdr')
def ruta_tex(nombre, mapa): return os.path.join(DIR, f'{nombre}_{mapa}_{TEXTURAS[nombre]}.jpg')
def hay(): return os.path.exists(ruta_hdri()) and all(os.path.exists(ruta_tex(n, m)) for n in TEXTURAS for m in MAPAS)

def bajar(url, destino):
    if os.path.exists(destino): return
    print('bajando', url, flush=True)
    urllib.request.urlretrieve(url, destino + '.tmp'); os.replace(destino + '.tmp', destino)

if __name__ == '__main__':
    os.makedirs(DIR, exist_ok=True)
    bajar(f'{BASE}/HDRIs/hdr/2k/{HDRI}_2k.hdr', ruta_hdri())
    for n, res in TEXTURAS.items():
        for m in MAPAS: bajar(f'{BASE}/Textures/jpg/{res}/{n}/{n}_{m}_{res}.jpg', ruta_tex(n, m))
    print('recursos listos en', DIR)
