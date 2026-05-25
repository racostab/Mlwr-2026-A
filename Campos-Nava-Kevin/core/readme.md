# core/ — Módulos compartidos

Código Python reutilizado por varias partes del lab. No se ejecuta por sí solo.

## Archivos

### `ssh.py` — helper SSH (paramiko)

Funciones para hablar con los entornos por SSH:

| Función                                  | Qué hace                                          |
|-------------------------------------------|---------------------------------------------------|
| `conectar(host, port, user, key_path)`    | Abre una conexión SSH con llave privada RSA       |
| `subir(client, local, remoto)`            | Copia un archivo al entorno remoto vía SFTP       |
| `ejecutar(client, comando)`               | Ejecuta un comando y devuelve su salida           |

`conectar` ajusta los permisos de la llave a `600` antes de usarla (si la llave
está montada read-only desde un volumen Docker, ignora el error).

Lo usa el **engine** para conectarse al `sandbox` (el `engine/Dockerfile` copia
este archivo dentro de su imagen).

### `config.py` — lector de `config.json`

Carga `config.json` desde la raíz del proyecto (una sola vez, en memoria) y lo
expone:

- `docker()` → bloque `docker` del JSON
- `kali()`   → bloque `kali` del JSON

Si `config.json` no existe, lanza un error pidiendo copiarlo desde
`config.example.json`.

> `config.json` lo usa **solo la parte de Kali** (`kali/api.py`) y los scripts
> standalone de `docker/`. El flujo principal de Docker Compose no lo necesita:
> esa configuración vive en `.env`.
