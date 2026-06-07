"""Configuración común de los tests.

Reproduce el `sys.path` que tiene el contenedor del motor para poder importar:
- `compartido.*`  (también instalable con `pip install -e .`, pero lo añadimos
  desde el código para poder correr los tests sin instalar nada).
- `catalogo.*`    (vive en `estatico/`).
- los módulos del motor `principal`/`rutas`/`servicios`/`repositorio` (en
  `estatico/motor/`, como módulos sueltos igual que dentro de la imagen).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

for p in (ROOT, ROOT / "estatico", ROOT / "estatico" / "motor"):
    ruta = str(p)
    if ruta not in sys.path:
        sys.path.insert(0, ruta)
