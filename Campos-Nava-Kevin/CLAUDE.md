# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es

Laboratorio de análisis de malware. El usuario sube muestras (binarios ELF de
botnets) por una web y elige qué herramientas correr. El **análisis estático**
corre dentro de un contenedor sandbox aislado; el **análisis dinámico** corre en
una VM Kali aparte (fuera de Docker, necesita su propio kernel).

La documentación está en español; los `readme.md` por carpeta son la fuente de
detalle. Mantén ese idioma en comentarios y docs nuevos.

## Principio de organización (importante)

El árbol está clasificado por familia de análisis. Antes de crear o mover algo,
ubícalo en la familia correcta:

- **`estatico/`** — TODO el análisis estático (motor/API, catálogo y sandbox).
- **`dinamico/`** — TODO el análisis dinámico (VM Kali, runner, firewall).
- **`base_de_datos/`** — esquema/servidor PostgreSQL.
- **Compartido en la raíz** — lo que usan ambas familias: `compartido/` (paquete
  Python de conexión SSH/SFTP + config), `web/` (UI única), `dataset/`, `lab_keys/`.

Dentro de `estatico/` y `dinamico/` la convención es:
- **`user_data/`** — scripts que *construyen/configuran* el contenedor o la VM al
  crearse (Dockerfiles, entrypoints, provisioning). Análogo a un cloud-init.
- **`scripts/`** — operaciones del proyecto que se corren *durante el uso*.

## Comandos

```bash
bash setup.sh                       # instala deps, genera llaves, crea .env/config.json, levanta el lab
docker compose up -d --build        # levantar manualmente (4 servicios)
docker compose down                 # apagar (los volúmenes samples/db-data se conservan)
docker compose logs -f engine       # logs de un servicio (engine = motor)
docker compose exec sandbox bash    # shell directa en el sandbox
pip install -e .                    # instalar el paquete `compartido` editable (para el análisis dinámico)
bash dinamico/scripts/ssh_maquina_virtual.sh   # SSH a la VM Kali

# Análisis dinámico (host, fuera de Docker):
(cd dinamico/maquina_virtual && vagrant up)                     # crear/provisionar la VM
python3 dinamico/scripts/analizador_dinamico.py <muestra> 20    # ejecutar muestra en la VM 20 s
```

Web → http://localhost:8000 · API → http://localhost:8001

No hay suite de tests ni linter configurados. La API se prueba a mano con `curl`
contra `:8001` (ver `estatico/motor/readme.md`).

## Arquitectura

Cuatro servicios en `docker-compose.yml`, conectados por dos redes:

- **`web`** (Django, `:8000`) — UI. Cliente delgado: cada vista hace `requests`
  contra el motor vía `ENGINE_URL`. No toca la DB ni el sandbox. Lógica en
  `web/analizador/servicios.py` (las "views" de Django).
- **`engine`/motor** (FastAPI, `:8001`) — orquesta todo. Rutas en
  `estatico/motor/rutas.py`, lógica en `estatico/motor/servicios.py`,
  persistencia en `estatico/motor/repositorio.py` (cliente PostgreSQL). Es el
  **único** que habla con el sandbox.
- **`db`** (PostgreSQL 16) — historial de muestras y caché de reportes; esquema
  en `base_de_datos/init.sql`.
- **`sandbox`** (Debian + binutils/file/ssdeep/yara/exiftool/radare2…) — ejecuta
  las herramientas. Está en la red `lab-sandbox` con `internal: true`: **sin
  salida a internet ni acceso al host**. Solo el motor lo alcanza.

```
web ──HTTP──▶ motor ──SSH+SFTP──▶ sandbox
                 │
                 └──▶ db (Postgres)
```

> Mapa completo de comunicación entre dockers + flujo de transferencia:
> **`docs/comunicacion.md`**.

### Cómo llega la muestra al sandbox (SFTP — punto clave)

**No hay volumen compartido entre el motor y el sandbox** (a propósito). El motor
guarda cada muestra en su volumen `samples:/samples`, nombrada por su `sha256`.
Para analizar:

1. `estatico/motor/servicios.py::ejecutar()` abre una conexión SSH al sandbox
   (`ssh()` → `compartido/sftp/conexion.py::conectar`, con `paramiko` y la llave
   `/keys/id_rsa` montada read-only).
2. `compartido/sftp/conexion.py::asegurar_remoto()` abre un canal SFTP
   (`client.open_sftp()`) y sube el archivo a `/samples/<sha256>` en el sandbox
   **solo si falta** (compara `st_size`; nombrado por sha256 ⇒ igual tamaño =
   mismo contenido).
3. El analizador corre la herramienta por SSH (`exec_command`) sobre esa ruta y
   se cierra la conexión.

**El módulo SFTP es compartido**: vive una sola vez en `compartido/sftp/` y lo
usan las dos familias — `estatico/` (motor→sandbox) y `dinamico/`
(host→VM, en `dinamico/scripts/analizador_dinamico.py`). Hay un puntero en
`dinamico/sftp/readme.md`.

Config del motor (host/puerto/usuario/llave) por variables de entorno en
`docker-compose.yml` (`SANDBOX_HOST`, `SANDBOX_PORT`, `SANDBOX_USER`,
`KEY_PATH`, `SAMPLES_DIR`).

### El catálogo de comandos es la única fuente de verdad

Los analizadores estáticos se declaran en **`estatico/catalogo/` → `CATALOGO`**
(dict de `Analizador`, en `registro.py`). De ahí salen `/tools`, los checkboxes
de la web y la ejecución genérica en `GET /samples/{sha256}/run/{tool}`. El
paquete está dividido por responsabilidad: `analizadores.py` (una función
`fn(client, ruta, **opts)` por herramienta), `comando_guiado.py` (el comando
suelto del usuario + `comandos.json`), `registro.py` (el `CATALOGO`) y
`analizador_estatico.py` (**fachada**: el motor importa siempre desde aquí).
**Añadir un análisis = una función en `analizadores.py` + una línea en
`CATALOGO`**. Flags: `cacheable` (los paramétricos como `strings`/`xxd` no se
cachean) y `oculto` (no aparece en `/tools`, p. ej. `custom`). La lista por
defecto (`POR_DEFECTO`) se expone en `/tools` con el flag `por_defecto`; la web
la lee de ahí (no la duplica).

El catálogo es **estático**: el motor lo copia dentro de su imagen e importa como
`catalogo.analizador_estatico`; no es parte del paquete `compartido`.

### compartido — paquete Python

`compartido/` es un namespace package (PEP 420, **sin `__init__.py`**; no los
añadas). Lo define `pyproject.toml` con `namespaces = true` y solo contiene lo
realmente común: `compartido/sftp/conexion.py` (SSH/SFTP) y
`compartido/configuracion.py` (lee `config.json`). Lo instalan el host (editable,
vía `setup.sh`, para el dinámico) y la imagen del motor (`pip install /pkg`).

### YARA

Reglas en `estatico/sandbox/reglas_yara/*.yar`, copiadas a la imagen del sandbox
al construir (`/rules/`). Para añadir/editar reglas: **reconstruir el sandbox**
(`docker compose up -d --build sandbox`).

## Estructura por carpeta

```
estatico/
  motor/        principal.py · rutas.py · servicios.py · repositorio.py (la API)
  catalogo/     analizadores.py · comando_guiado.py · registro.py · analizador_estatico.py (fachada) · comandos.json
  sandbox/      reglas_yara/ (*.yar)
  user_data/    motor/Dockerfile · sandbox/{Dockerfile,entrypoint.sh}
  scripts/
dinamico/
  maquina_virtual/  Vagrantfile (definición de la VM Kali)
  user_data/        provision_kali.sh (provisioning de la VM)
  reglas_firewall/  aislar_host.sh (aísla el host de la VM)
  scripts/          analizador_dinamico.py · control_maquina_virtual.sh · ssh_maquina_virtual.sh
  sftp/             puntero a compartido/sftp
compartido/   sftp/conexion.py · configuracion.py
web/          manage.py · sitio/ (proyecto Django) · analizador/ (app: servicios.py, rutas.py, templates, static)
base_de_datos/  init.sql
dataset/      catálogo de muestras + scripts/
```

## Notas

- El sandbox y la VM son deliberadamente cajas sin host. Cualquier cambio que les
  dé salida a internet o acceso al host rompe el aislamiento; no lo hagas sin que
  el usuario lo pida.
- Renombrar el paquete `compartido`, las rutas del motor o la app Django implica
  tocar imports + `docker-compose.yml` + Dockerfiles + `setup.sh` + `Vagrantfile`.
- `web/sitio/__init__.py` (casi vacío) es **obligatorio** para Django; no lo
  borres. El resto del código usa namespace packages, sin `__init__.py`.
- Generados/locales (gitignored): `lab_keys/`, `.env`, `config.json`,
  `*.egg-info/`, `build/`, `__pycache__/`.
