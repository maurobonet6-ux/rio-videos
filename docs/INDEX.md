# Índice — rio-videos

Render de los vídeos 3D promocionales de RÍO (riopoker.es). Es público para que GitHub Actions sea gratis. **El original está en el repo privado `Rio-poker` (`marketing/videos/promo3d`); los cambios se copian aquí.**

| Necesito… | Archivo |
|---|---|
| Escena 3D (Blender) | `promo3d/escena.py`, `promo3d/pantalla.py` |
| Guion y reparto de escenas | `promo3d/guion.py`, `promo3d/hoja.py` |
| Texturas y recursos | `promo3d/texturas.py`, `promo3d/recursos.py`, `promo3d/tex_ph/` |
| Posproducción (montaje) | `promo3d/post.py` |
| Audio, voz y sonidos | `promo3d/audio.py`, `promo3d/voz/`, `promo3d/sonidos/` |
| Portada | `promo3d/portada.py`, `promo3d/portada_texto.py` |
| Capturas de la app | `salida/promo3d/` |
| Lanzar el render | `.github/workflows/render.yml` |

## Render
- Todo: push con «[render]» en el mensaje, o Actions → Render → Run workflow.
- Un tramo: «[render 1-144]». Los trozos quedan como artefactos.
- Vídeo completo: artefacto `rio-promo3d`.

## Mantenimiento
Si añades un archivo importante, añade una línea aquí. Máximo ~50 líneas.
