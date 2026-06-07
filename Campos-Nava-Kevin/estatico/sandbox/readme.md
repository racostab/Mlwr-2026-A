# estatico/sandbox/ — Imagen del contenedor de análisis estático

Define el contenedor `sandbox`: un Debian con las herramientas de análisis
estático. El motor se conecta por SSH y le **envía cada muestra por SFTP**
(ya no hay volumen compartido), luego ejecuta ahí las herramientas.

Es el servicio `sandbox` de `docker-compose.yml` (build con contexto `./estatico`
y `dockerfile: user_data/sandbox/Dockerfile`).

## Contenido

- **`user_data/sandbox/Dockerfile`** — Debian bookworm-slim + `openssh-server`,
  `binutils`, `file`, `ssdeep`, `yara`, `xxd`, `exiftool`, `procps` y **radare2**.
  > radare2 ya no está en el repo `main` de Debian bookworm, así que se instala
  > automáticamente desde el `.deb` oficial detectando la arquitectura
  > (`ARG R2_VERSION`).
- **`user_data/sandbox/entrypoint.sh`** — instala la llave pública del lab en
  `/root/.ssh` y arranca `sshd`.
- **`reglas_yara/`** — reglas YARA (`*.yar`) que se copian a `/rules/` en la
  imagen. El analizador `yara` del catálogo escanea con todas ellas. Añade tus
  reglas como nuevos `.yar` aquí y reconstruye (`docker compose build sandbox`).

## Aislamiento

- Red Docker `internal`: sin salida a internet ni acceso al host.
- `/samples` es scratch efímero: recibe las muestras por SFTP sobre el canal SSH.
- Solo el `engine` puede hablar con él (red `lab-sandbox`).
