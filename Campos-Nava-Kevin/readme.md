# Malware Lab — Campos Nava Kevin Eduardo

Laboratorio de análisis de malware. Subes una o varias muestras y eliges qué
comandos correr sobre ellas (**análisis estático**: hashes, strings, entropía,
metadatos, cabeceras ELF, YARA, radare2…) ejecutados dentro de un sandbox
aislado. Para **análisis dinámico** hay una VM Kali aparte.

## Arquitectura

El análisis estático corre en Docker Compose (4 servicios). La VM Kali queda
fuera de Docker porque necesita su propio kernel.

```
                    ┌──────────┐
   navegador ─────▶ │   web    │  Django UI            :8000
                    └────┬─────┘
                         │ HTTP
                         ▼
                    ┌──────────┐        ┌──────────┐
                    │  engine  │ ◀────▶ │    db    │  PostgreSQL
                    │ REST API │        └──────────┘
                    │   :8001  │
                    └────┬─────┘
                         │ SSH + SFTP  (red interna: sin internet, sin host)
                         ▼
                    ┌──────────┐
                    │ sandbox  │  Debian + binutils, file, ssdeep,
                    │          │  yara, exiftool, readelf, radare2...
                    └──────────┘

   ── aparte, fuera de Docker ──
                    ┌──────────┐
                    │   Kali   │  VM VirtualBox — análisis dinámico
                    └──────────┘
```

| Servicio | Tecnología     | Puerto         | Rol                                            |
|----------|----------------|----------------|------------------------------------------------|
| `web`    | Django         | 8000           | Interfaz para subir muestras y elegir comandos |
| `engine` | FastAPI        | 8001           | API REST: orquesta el análisis y cachea reportes |
| `db`     | PostgreSQL 16  | interno        | Historial de muestras y reportes               |
| `sandbox`| Debian slim    | interno        | Ejecuta las herramientas de análisis estático  |
| Kali     | VirtualBox     | 192.168.56.10 (host-only) | Análisis dinámico aislado (strace, gdb, tcpdump...) |

> El `sandbox` está en una red Docker `internal`: no tiene salida a internet ni
> acceso al host. Solo el `engine` puede hablar con él.

### Cómo llega la muestra al sandbox (SFTP, sin volumen compartido)

El engine guarda cada muestra en **su propio** volumen. Cuando se pide un
análisis, abre la conexión SSH al sandbox y **envía el archivo por SFTP** a
`/samples/<sha256>` (solo si no está ya), corre la herramienta y cierra. Así el
sandbox no comparte filesystem con nadie: es una caja pura a la que solo se le
habla por SSH, usando las llaves de `lab_keys/`.

> **Detalle completo** de qué docker habla con cuál, por qué red y cómo viaja la
> muestra paso a paso: **[`docs/comunicacion.md`](docs/comunicacion.md)**.

### Catálogo de comandos (única fuente de verdad)

Todos los analizadores se declaran en un único registro,
`estatico/catalogo/analizador_estatico.py` → `CATALOGO`. De ahí salen automáticamente la lista
de comandos (`GET /tools` y los checkboxes de la web) y la ejecución genérica
(`GET /samples/<sha>/run/<tool>`). **Añadir un análisis nuevo
es una sola línea** en `CATALOGO`.

Comandos incluidos: `hash`, `file`, `entropy`, `ssdeep`, `exiftool`, `readelf`,
`yara`, `radare`, `strings`, `xxd`.

---

## Requisitos

`setup.sh` instala automáticamente lo que falte (Docker, compose, llaves, etc.).

| Herramienta            | Para qué                            | Instalación                                 |
|------------------------|-------------------------------------|----------------------------------------------|
| Docker + Compose v2    | Levantar el lab                     | lo instala `setup.sh` (`docker.io`)          |
| `ssh-keygen`           | Generar las llaves del lab          | lo instala `setup.sh` (`openssh-client`)     |
| VirtualBox + Vagrant   | Análisis dinámico *(opcional)*      | lo instala `setup.sh` si eliges Kali         |

---

## Instalación

```bash
git clone <repo>
cd Campos-Nava-Kevin
bash setup.sh
```

`setup.sh` hace todo el arranque:

- Instala dependencias faltantes (Docker, compose, `ssh-keygen`, `requests`).
- Genera las llaves SSH **del lab** en `lab_keys/`.
- Crea `.env` y `config.json` desde sus plantillas.
- Instala el paquete `compartido` (editable, para las herramientas del host).
- Construye y levanta los contenedores (`docker compose up -d --build`).
- Pregunta si quieres configurar Kali con Vagrant (instala VirtualBox/Vagrant y
  levanta la VM si aceptas).
- Se queda en primer plano: **Ctrl+C apaga y destruye los contenedores** (los
  datos en volúmenes se conservan).

Al terminar: Web → http://localhost:8000 · API → http://localhost:8001

---

## Uso

### Interfaz web

Abre http://localhost:8000, arrastra una o varias muestras y, en modo
*personalizado*, marca qué comandos correr (incluido YARA). La pestaña *History*
lista todo lo analizado.

> El `engine` expone una API REST (FastAPI) en `http://localhost:8001`; puedes
> llamarla directo (`curl`, scripts) además de usar la web. Ver `estatico/motor/readme.md`.

### Shell / SSH a los entornos

```bash
ssh -i lab_keys/id_rsa -p <puerto> root@127.0.0.1   # sandbox (vía docker compose exec es más fácil)
docker compose exec sandbox bash                    # shell directa en el sandbox
bash dinamico/scripts/ssh_maquina_virtual.sh        # SSH a la VM Kali
```

---

## Análisis dinámico — Kali

VM independiente (necesita su propio kernel, no va en Docker). Detalle en
`dinamico/readme.md`.

---

## Estructura

El árbol está clasificado por familia: **`estatico/`** y **`dinamico/`** son las
carpetas principales; `base_de_datos/` y lo compartido quedan a nivel de raíz.

```
Campos-Nava-Kevin/
├── docker-compose.yml      orquesta los 4 servicios
├── pyproject.toml          define el paquete `compartido`
├── setup.sh                instalación y arranque del lab
├── .env.example            plantilla de variables de entorno
├── config.example.json     plantilla de config (solo Kali)
├── lab_keys/               llaves SSH del lab (gitignored)
│
├── estatico/   →  ANÁLISIS ESTÁTICO
│   ├── motor/        API REST (FastAPI): principal · rutas · servicios · repositorio
│   ├── catalogo/     analizador_estatico.py + comandos.json (única fuente de verdad)
│   ├── sandbox/      reglas_yara/ (*.yar)
│   ├── user_data/    provisioning de contenedores: motor/ y sandbox/ (Dockerfiles, entrypoint)
│   └── scripts/      operaciones estáticas
│
├── dinamico/   →  ANÁLISIS DINÁMICO (VM Kali, fuera de Docker)
│   ├── maquina_virtual/  Vagrantfile (definición de la VM)
│   ├── user_data/        provision_kali.sh (provisioning de la VM)
│   ├── reglas_firewall/  aislar_host.sh (firewall del host: aísla el host de la VM)
│   ├── analizador/       motor (Python): red · firewall · verificacion · ejecucion · aislamiento (fachada) · analizador_dinamico
│   ├── scripts/          configurar_dinamico.sh · control/ssh de la VM
│   └── sftp/             puntero a compartido/sftp
│
├── base_de_datos/  →  esquema PostgreSQL (init.sql)
│
├── compartido/  →  paquete Python común: sftp/ (SSH/SFTP) + configuracion.py
├── web/         →  interfaz web (Django): sitio/ (proyecto) + analizador/ (app)
└── dataset/     →  catálogo de muestras botnet ELF (scripts/)
```

Cada carpeta tiene su propio `readme.md`. Dentro de `estatico/` y `dinamico/`,
`user_data/` reúne lo que construye/configura el contenedor o la VM al crearse, y
`scripts/` las operaciones que se corren durante el uso.
