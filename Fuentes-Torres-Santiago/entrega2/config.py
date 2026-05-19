# ============================================================
#  config.py  —  Configuración Global del Laboratorio
# ============================================================

import os

# ── Rutas ────────────────────────────────────────────────────
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTOS_DIR = os.path.join(BASE_DIR, "experimentos")
RESULTADOS_DIR   = os.path.join(BASE_DIR, "resultados")

# ── Servidor ─────────────────────────────────────────────────
SRV_HOST = "localhost"
SRV_PORT = 9999
BUFFER   = 65536  
TIMEOUT  = 30

# ── Docker ───────────────────────────────────────────────────
DOCKER_IMAGEN     = "lab-malware"
DOCKER_CONTENEDOR = "ciber-lab"
DOCKER_DIR_LAB    = "/laboratorio"
DOCKER_DIR_MUESTRAS = "/muestras"

# ── Modos de análisis ─────────────────────────────────────────
MODO_LOCAL  = "docker"
MODO_DOCKER = "docker"
MODO_DEFAULT = MODO_DOCKER

# ── VirtualBox ───────────────────────────────────────────────
VM_NOMBRE = "ciber"
VM_SSH_PORT = 2222

# ── SSH ──────────────────────────────────────────────────────
SSH_ALIAS   = "ciber-vm"
SSH_USUARIO = "debian"
SSH_PUERTO  = 2222

# ── Crear directorios si no existen ──────────────────────────
os.makedirs(EXPERIMENTOS_DIR, exist_ok=True)
os.makedirs(RESULTADOS_DIR,   exist_ok=True)