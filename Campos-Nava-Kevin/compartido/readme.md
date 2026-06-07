# compartido/ — Paquete Python común del lab

Biblioteca instalable (`pip install -e .` desde la raíz, vía `pyproject.toml`)
con el código que usan **ambas** familias de análisis: el motor (estático,
dentro del contenedor) y el runner del análisis dinámico (en el host). Se importa
como `compartido.*`; **no hay parches `sys.path.insert`**.

Solo contiene lo realmente transversal. Lo específico de cada familia vive en su
carpeta (`estatico/`, `dinamico/`).

## Contenido

### `sftp/conexion.py` — conexión SSH y transferencia SFTP

- `conectar(host, port, user, key_path, label)` → cliente SSH (paramiko).
- `subir(client, local, remoto)` → `sftp.put` simple.
- `asegurar_remoto(client, local, remoto)` → sube por SFTP **solo si falta**
  (mismo tamaño ⇒ mismo contenido, porque las muestras se nombran por sha256).
  Es lo que sustituye al volumen compartido entre el motor y el sandbox.
- `ejecutar(client, comando)` → corre un comando e imprime salida/errores.

Lo usan el motor (`estatico/motor/servicios.py`, host→sandbox) y el runner
dinámico (`dinamico/scripts/analizador_dinamico.py`, host→VM).

### `configuracion.py` — config del host

Lee `config.json` de la raíz. `kali()` devuelve la sección de la VM. (El motor no
lo usa: corre con variables de entorno y compose, no con `config.json`.)
