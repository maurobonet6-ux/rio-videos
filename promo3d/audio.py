# Sonido del vídeo promocional (versión 2): voz (promo3d/voz, ElevenLabs), música y efectos (promo3d/sonidos, ElevenLabs),
# todo colocado con los tiempos de guion.py. La música baja cuando habla la voz y se apaga al final.
# Uso: python3.11 promo3d/audio.py → salida/promo3d/audio.wav (44,1 kHz, estéreo)
import os, sys, wave, subprocess
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import guion as G

SR = 44100
CAP = os.path.join(AQUI, '..', 'salida', 'promo3d'); os.makedirs(CAP, exist_ok=True)
N = int(SR * G.TOTAL / G.FPS)
seg = lambda f: int((f - 1) / G.FPS * SR)

def leer(ruta, canales=2):
    x = subprocess.run(['ffmpeg', '-v', 'error', '-i', ruta, '-ac', str(canales), '-ar', str(SR), '-f', 'f32le', '-'],
                       capture_output=True, check=True).stdout
    return np.frombuffer(x, dtype=np.float32).reshape(-1, canales).copy()

def poner(pista, x, i, gan=1.0):
    if i < 0: x = x[-i:]; i = 0
    x = x[:max(0, len(pista) - i)]; pista[i:i + len(x)] += x * gan

voz = np.zeros((N, 2), np.float32)
for vid, _, f in G.VOZ: poner(voz, leer(os.path.join(AQUI, 'voz', vid + '.mp3')), seg(f))
voz *= 0.9 / (np.abs(voz).max() + 1e-9)

GAN = {'escaner': 0.4, 'contador': 0.35, 'whoosh': 0.45, 'whoosh2': 0.55, 'fichas': 0.5, 'cartas': 0.45, 'pop': 0.4, 'logro': 0.45, 'golpe': 0.6, 'interruptor': 0.7}
efectos = np.zeros((N, 2), np.float32)
cache = {}
for n, f in G.EFECTOS:
    if n not in cache: x = leer(os.path.join(AQUI, 'sonidos', n + '.mp3')); cache[n] = x / (np.abs(x).max() + 1e-9)
    adelanto = int(SR * 0.3) if n.startswith('whoosh') else 0      # el whoosh llega a su punto en el movimiento
    poner(efectos, cache[n], seg(f) - adelanto, GAN[n])

musica = leer(os.path.join(AQUI, 'sonidos', 'musica.mp3'))[:N]
musica = np.pad(musica, ((0, N - len(musica)), (0, 0)))
musica *= 0.5 / (np.sqrt((musica ** 2).mean()) * 4 + 1e-9)        # nivel de fondo
nivel = np.convolve(np.abs(voz[:, 0]), np.ones(SR // 8) / (SR // 8), 'same')
duck = 1 - 0.45 * np.clip(nivel / (nivel.max() * 0.2 + 1e-9), 0, 1)
fin = np.clip((N - np.arange(N)) / (SR * 1.5), 0, 1)
mezcla = voz + efectos + musica * (duck * fin)[:, None]
mezcla /= max(1.0, np.abs(mezcla).max() / 0.95)
with wave.open(os.path.join(CAP, 'audio.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mezcla * 32767).astype(np.int16).tobytes())
print('audio ok', round(N / SR, 2), 's')
