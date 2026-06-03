# docker/ — Sandbox de análisis estático

Define el contenedor `sandbox`: un Debian con las herramientas de análisis
estático. El `engine` se conecta a él por SSH y ejecuta ahí los comandos.

Es el servicio `sandbox` de `docker-compose.yml`.

## Aislamiento

El `sandbox` está en la red Docker `lab-sandbox`, marcada como `internal`:
**sin salida a internet ni acceso al host**. Solo el `engine` lo alcanza. Así una
muestra maliciosa no puede "llamar a casa" durante el análisis.

## La imagen

### `Dockerfile`

Parte de `debian:bookworm-slim` e instala las herramientas de análisis:

| Paquete                  | Aporta                                   |
|--------------------------|------------------------------------------|
| `binutils`               | `strings`, `readelf`                     |
| `file`                   | identificación de tipo de archivo        |
| `bsdmainutils`           | `hexdump` y utilidades                   |
| `ssdeep`                 | hashing difuso (*fuzzy hashing*)         |
| `yara`                   | reglas de detección de patrones          |
| `xxd`                    | volcado hexadecimal + ASCII              |
| `radare2`                | desensamblado (`r2`)                      |
| `libimage-exiftool-perl` | `exiftool` (metadatos)                   |
| `python3`, `procps`      | cálculo de entropía y utilidades         |

Configura `sshd` para aceptar **solo autenticación por llave pública** (sin
contraseñas) y login de `root`.

### `entrypoint.sh`

Al arrancar el contenedor, copia la llave pública del lab — montada en
`/tmp/authorized_keys` desde `lab_keys/id_rsa.pub` — a
`/root/.ssh/authorized_keys`. Así el `engine` puede entrar por SSH.

## Scripts

### `debian.py` — funciones de análisis

Cada función ejecuta un comando dentro del sandbox por SSH y parsea su salida:

| Función              | Herramienta        |
|----------------------|--------------------|
| `hash_archivo`       | `md5sum` / `sha1sum` / `sha256sum` |
| `file_archivo`       | `file`             |
| `strings_archivo`    | `strings -n`       |
| `entropia_archivo`   | cálculo en Python (entropía de Shannon) |
| `exiftool_archivo`   | `exiftool`         |
| `readelf_archivo`    | `readelf -a`       |
| `xxd_archivo`        | `xxd` (hex + ASCII, primeros bytes) |
| `radare_archivo`     | `r2 -A` (`afl`, `pdf @ entry0`, `pdf @ main`) |
| `ssdeep_archivo`     | `ssdeep`           |

El `engine` importa estas funciones (el `engine/Dockerfile` copia este archivo
dentro de su imagen). También se puede correr suelto:
`python3 debian.py hash /ruta/muestra` (usa `config.json`).

### `debian.sh` — shell interactiva

Abre una shell dentro del sandbox en marcha:

```bash
bash docker/debian.sh   # → docker compose exec sandbox bash
```

### `docker.py` — control de contenedor *(utilidad standalone)*

Inicia / detiene / inspecciona un contenedor por nombre (tomado de
`config.json`): `python3 docker.py start|stop|status|logs|...`.

> Es una herramienta independiente, **no la usa** el flujo de Compose. Con
> Compose el contenedor se gestiona con `lab.py up` / `lab.py down`.
