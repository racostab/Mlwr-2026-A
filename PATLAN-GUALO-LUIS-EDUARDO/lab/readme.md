# Malware Lab — Campos Nava Kevin Eduardo

Laboratorio de análisis de malware con dos entornos aislados:

| Entorno | Tecnología | Uso |
|---|---|---|
| **Debian** | Docker | Análisis estático (hashes, strings, info) |
| **Debian VM** | VirtualBox | Análisis dinámico (strace, tcpdump, gdb) |

La comunicación con ambos entornos es por SSH usando llave pública.

---

## Instalación

### 1. Requisitos previos

| Herramienta | Instalación |
|---|---|
| Python 3 | — |
| Docker | https://docs.docker.com/engine/install/ |
| jq | `sudo apt install jq` |
| VirtualBox *(para análisis dinámico)* | https://www.virtualbox.org/ |

### 2. Setup automático

```bash
cd PATLAN-GUALO-LUIS-EDUARDO/lab
bash setup.sh
```

El script:
- Genera las llaves SSH del lab en `lab_keys/`
- Crea el `.env` desde `.env.example`
- Construye y levanta los contenedores (sandbox, db, engine, web)
- Te ofrece (opcional) encender tu VM Debian para el análisis dinámico

---

## Configuración

Copia la plantilla y edita los valores:

```bash
cp config.example.json config.json
```

```json
{
  "docker": {
    "container": "debian",
    "host": "127.0.0.1",
    "port": 2223,
    "user": "root",
    "key_path": "~/.ssh/id_rsa"
  },
  "vbox": {
    "host": "127.0.0.1",
    "port": 2222,
    "user": "tu_usuario",
    "key_path": "~/.ssh/id_rsa",
    "vm_name": "debian"
  }
}
```

> `config.json` está en `.gitignore` — nunca se sube al repo.
> La sección `vbox` apunta a tu VM Debian de VirtualBox (análisis dinámico).

---

## Uso

### CLI principal

```bash
python3 lab.py up                        # levanta los contenedores del lab
python3 lab.py analyze /ruta/muestra      # sube la muestra + análisis completo
python3 lab.py list                       # historial de muestras
python3 lab.py strings <sha256>
python3 lab.py readelf <sha256>
```

### Conectar shell interactiva

```bash
bash docker/debian.sh   # shell en el contenedor sandbox
bash vbox/vbox.sh       # shell SSH en la VM Debian (análisis dinámico)
```

---

## VM Debian — Análisis dinámico

El análisis dinámico (strace, tcpdump, gdb) corre en una VM Debian de
VirtualBox, fuera de Docker. Configúrala una vez:

1. Ten tu VM Debian en VirtualBox; su nombre debe coincidir con `vbox.vm_name`
   de `config.json` (por defecto `debian`).
2. Reenvío de puertos en la VM: **host 2222 → guest 22**.
3. Autoriza tu llave SSH en la VM:
   ```bash
   ssh-copy-id -i ~/.ssh/id_rsa.pub -p 2222 eduardo@127.0.0.1
   ```
4. Revisa que la sección `vbox` de `config.json` tenga tus datos.

Más detalle en `vbox/readme.md`.

---

## Estructura del proyecto

```
lab/
├── config.json          # configuración local (gitignored)
├── config.example.json  # plantilla de configuración
├── requirements.txt
├── setup.sh             # instalación automatizada
├── lab.py               # CLI principal
├── docker-compose.yml   # orquesta sandbox + db + engine + web
├── core/
│   ├── config.py        # lector de config.json
│   └── ssh.py           # helper SSH compartido
├── db/
│   └── init.sql         # esquema de la base de datos
├── engine/              # API REST de análisis estático (FastAPI)
├── web/                 # interfaz web (Django)
├── docker/
│   ├── Dockerfile
│   ├── debian.py        # análisis estático vía SSH
│   ├── docker.py        # gestión del contenedor
│   └── debian.sh        # shell interactiva
└── vbox/
    ├── api.py           # control de la VM Debian vía vboxapi
    ├── cli.sh           # control de la VM Debian vía VBoxManage
    └── vbox.sh          # shell interactiva SSH
```
