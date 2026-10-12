# rio-videos

Render de los vídeos 3D de [RÍO](https://riopoker.es). Es público para que GitHub Actions sea gratis y sin límite de minutos.

Aquí solo hay lo necesario para renderizar: los scripts de Blender y de posproducción (`promo3d/`), las capturas de la app
(`salida/promo3d/`), la voz y la música. El código de la app y las claves están en el repositorio privado, que es el original
(`marketing/videos/promo3d`); los cambios se copian aquí.

- Todo el vídeo: push con «[render]» en el mensaje, o Actions → Render → Run workflow.
- Un tramo: «[render 1-144]» (o el campo «rango» al lanzarlo a mano). Los trozos quedan como artefactos.
- El vídeo completo sale como artefacto `rio-promo3d`.
