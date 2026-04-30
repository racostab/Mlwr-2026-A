# Malware Lab — Campos Nava Kevin Eduardo

Laboratorio de análisis de malware con dos entornos aislados:

| Entorno | Tecnología | Uso |
|---|---|---|
| **Debian** | Docker | Análisis estático (hashes, strings, info) |
| **Kali Linux** | VirtualBox / Vagrant | Análisis dinámico (strace, tcpdump, gdb) |

La comunicación con ambos entornos es por SSH usando llave pública.

---

## Instalación

### 1. Requisitos previos

| Herramienta | Instalación |
|---|---|
| Python 3 | — |
| Docker | https://docs.docker.com/engine/install/ |
| jq | `sudo apt install jq` |
| Vagrant *(opcional)* | https://www.vagrantup.com/downloads |
| VirtualBox | https://www.virtualbox.org/ |

### 2. Setup automático

```bash
git clone <repo>
cd Campos-Nava-Kevin
bash setup.sh
```

El script:
- Crea `config.json` desde la plantilla
- Genera llaves SSH si no existen
- Instala dependencias Python
- Construye y configura el contenedor Debian
- Te guía para configurar Kali (3 opciones)

---

## Configuración

Copia la plantilla y edita los valores:

```bash
cp config.example.json config.json
```

```json
{
  "docker": {
    "container": "malware-debian",
    "host": "127.0.0.1",
    "port": 2223,
    "user": "kevin",
    "key_path": "~/.ssh/id_rsa"
  },
  "kali": {
    "host": "127.0.0.1",
    "port": 2222,
    "user": "kali",
    "key_path": "~/.ssh/id_rsa",
    "vm_name": "kali-malware-lab"
  }
}
```

> `config.json` está en `.gitignore` — nunca se sube al repo.

---

## Uso

### CLI principal

```bash
python3 lab.py docker status
python3 lab.py docker start
python3 lab.py kali start

python3 lab.py static hash    /tmp/muestra.exe
python3 lab.py static strings /tmp/muestra.exe
python3 lab.py static info    /tmp/muestra.exe
```

### Conectar shell interactiva

```bash
bash docker/debian.sh   # shell en Debian
bash kali/kali.sh       # shell en Kali
```

---

## Kali Linux — Opciones de configuración

### Opción 1: Vagrant (recomendado)

Levanta automáticamente una VM Kali con herramientas preinstaladas:

```bash
vagrant up          # primera vez (descarga el box ~3 GB)
vagrant halt        # apagar
vagrant up          # encender de nuevo
vagrant destroy     # eliminar la VM
```

### Opción 2: VirtualBox manual con .ova

1. `VirtualBox → Archivo → Importar servicio virtualizado`
2. Configurar reenvío de puertos: **host 2222 → guest 22**
3. Iniciar la VM
4. Copiar llave SSH:
   ```bash
   sshpass -p kali ssh-copy-id -i ~/.ssh/id_rsa.pub -p 2222 -o StrictHostKeyChecking=no kali@127.0.0.1
   ```

### Opción 3: VM ya existente

Solo necesitas configurar el reenvío de puertos y copiar la llave:

```bash
ssh-copy-id -i ~/.ssh/id_rsa.pub -p 2222 kali@127.0.0.1
```

---

## Estructura del proyecto

```
Campos-Nava-Kevin/
├── config.json          # configuración local (gitignored)
├── config.example.json  # plantilla de configuración
├── requirements.txt
├── setup.sh             # instalación automatizada
├── lab.py               # CLI principal
├── Vagrantfile          # VM Kali vía Vagrant
├── vagrant/
│   └── provision_kali.sh
├── core/
│   ├── config.py        # lector de config.json
│   └── ssh.py           # helper SSH compartido
├── docker/
│   ├── Dockerfile
│   ├── debian.py        # análisis estático vía SSH
│   ├── docker.py        # gestión del contenedor
│   └── debian.sh        # shell interactiva
└── kali/
    ├── kali.py          # conexión SSH a Kali
    ├── api.py           # control VM vía vboxapi
    ├── kali.sh          # shell interactiva
    └── cli.sh           # control VM vía VBoxManage
```
