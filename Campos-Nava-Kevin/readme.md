# Malware Lab — Campos Nava Kevin Eduardo

Laboratorio de análisis de malware. Subes una muestra y obtienes su **análisis
estático** (hashes, strings, entropía, info de archivo, etc.) ejecutado dentro de
un sandbox aislado. Para **análisis dinámico** hay una VM Kali aparte.

## Arquitectura

Todo el análisis estático corre en Docker Compose (4 servicios). La VM Kali queda
fuera de Docker porque necesita su propio kernel.

```
                    ┌──────────┐
   navegador ─────▶ │   web    │  Django UI            :8000
                    └────┬─────┘
                         │ HTTP
   CLI (lab.py) ────────▶│
                         ▼
                    ┌──────────┐        ┌──────────┐
                    │  engine  │ ◀────▶ │    db    │  PostgreSQL
                    │ REST API │        └──────────┘
                    │   :8001  │
                    └────┬─────┘
                         │ SSH  (red interna: sin internet, sin host)
                         ▼
                    ┌──────────┐
                    │ sandbox  │  Debian + binutils, file, ssdeep,
                    │          │  yara, exiftool, readelf...
                    └──────────┘

   ── aparte, fuera de Docker ──
                    ┌──────────┐
                    │   Kali   │  VM VirtualBox — análisis dinámico
                    └──────────┘
```

| Servicio | Tecnología     | Puerto         | Rol                                            |
|----------|----------------|----------------|------------------------------------------------|
| `web`    | Django         | 8000           | Interfaz para subir muestras y ver resultados  |
| `engine` | FastAPI        | 8001           | API REST: orquesta el análisis y cachea reportes |
| `db`     | PostgreSQL 16  | interno        | Historial de muestras y reportes               |
| `sandbox`| Debian slim    | interno        | Ejecuta las herramientas de análisis estático  |
| Kali     | VirtualBox     | 2222 (SSH)     | Análisis dinámico (strace, gdb, tcpdump...)     |

> El `sandbox` está en una red Docker `internal`: no tiene salida a internet ni
> acceso al host. Solo el `engine` puede hablar con él.

---

## Requisitos

| Herramienta            | Para qué                            | Instalación                                 |
|------------------------|-------------------------------------|----------------------------------------------|
| Docker + Compose v2    | Levantar el lab                     | https://docs.docker.com/engine/install/      |
| `ssh-keygen`           | Generar las llaves del lab          | paquete `openssh-client`                     |
| Python 3 + `requests`  | Usar la CLI `lab.py`                | `pip install -r requirements.txt`            |
| VirtualBox + Vagrant   | Análisis dinámico *(opcional)*      | https://www.vagrantup.com/downloads          |
| `jq`                   | `kali/kali.sh` *(opcional)*         | `sudo apt install jq`                        |

---

## Instalación

```bash
git clone <repo>
cd Campos-Nava-Kevin
bash setup.sh
```

`setup.sh` hace todo el arranque:

- Genera el par de llaves SSH **del lab** en `lab_keys/` (propias del lab, no las tuyas).
- Crea `.env` a partir de `.env.example`.
- Construye y levanta los contenedores (`docker compose up -d --build`).
- Pregunta si quieres configurar Kali con Vagrant.
- Se queda en primer plano: **Ctrl+C apaga y destruye los contenedores** (los
  datos en volúmenes se conservan).

Al terminar:

- Web → http://localhost:8000
- API → http://localhost:8001

---

## Configuración — `.env`

`.env` lo crea `setup.sh` y está en `.gitignore`. Controla puertos y credenciales
de la base de datos:

```
WEB_PORT=8000
ENGINE_PORT=8001
POSTGRES_USER=lab
POSTGRES_PASSWORD=lab
POSTGRES_DB=lab
```

> `config.example.json` / `config.json` es una configuración aparte que **solo**
> usa la parte de Kali (ver `kali/readme.md`). El análisis estático no lo necesita.

---

## Uso

### Interfaz web

Abre http://localhost:8000, sube una muestra y mira el reporte. La pestaña
*History* lista todo lo analizado.

### CLI — `lab.py`

La CLI es un cliente HTTP del `engine`.

```bash
python3 lab.py up                      # levanta los contenedores
python3 lab.py analyze /ruta/muestra   # sube + análisis completo
python3 lab.py list                    # historial de muestras
python3 lab.py down                    # apaga los contenedores
```

Análisis individual sobre una muestra ya subida (identificada por su `sha256`):

```bash
python3 lab.py upload   /ruta/muestra   # devuelve el sha256
python3 lab.py hash     <sha256>
python3 lab.py file     <sha256>
python3 lab.py strings  <sha256> [min_len]
python3 lab.py entropy  <sha256>
python3 lab.py ssdeep   <sha256>
python3 lab.py exiftool <sha256>
python3 lab.py readelf  <sha256>
```

Con `ENGINE_URL=http://otro-host:8001 python3 lab.py ...` apuntas a otra instancia.

### Shell dentro de los entornos

```bash
bash docker/debian.sh   # shell interactiva en el sandbox
bash kali/kali.sh       # SSH a la VM Kali
```

---

## Análisis dinámico — Kali

Es una VM independiente (necesita su propio kernel, no va en Docker). El detalle
está en `kali/readme.md` y `vagrant/readme.md`.

---

## Estructura

```
Campos-Nava-Kevin/
├── docker-compose.yml      orquesta los 4 servicios
├── setup.sh                instalación y arranque del lab
├── lab.py                  CLI cliente del engine
├── .env.example            plantilla de variables de entorno
├── config.example.json     plantilla de config (solo Kali)
├── requirements.txt        dependencias de la CLI
├── Vagrantfile             definición de la VM Kali
├── lab_keys/               llaves SSH del lab (gitignored)
├── core/      →  módulos compartidos (SSH, config)      · core/readme.md
├── dataset/   →  catálogo de muestras botnet ELF        · dataset/readme.md
├── db/        →  esquema PostgreSQL                     · db/readme.md
├── docker/    →  imagen del sandbox de análisis         · docker/readme.md
├── engine/    →  API REST (FastAPI)                     · engine/readme.md
├── kali/      →  control de la VM Kali                  · kali/readme.md
├── vagrant/   →  provisioning de Kali                   · vagrant/readme.md
└── web/       →  interfaz web (Django)                  · web/readme.md
```

Cada carpeta tiene su propio `readme.md` con el detalle de qué hace y cómo.
