# Análisis dinámico — VM Debian (VirtualBox)

VM de análisis dinámico del lab. Los datos de conexión salen de `../config.json`,
sección `vbox`.

## Requisitos
- VirtualBox instalado
- Python 3
- `vboxapi` *(opcional, solo para `api.py`)*
- `jq`: `sudo apt install jq` *(para `vbox.sh`)*
- OpenSSH: `sudo apt install openssh-client`

## Configuración (solo una vez)

### 1. La VM
Usa tu VM Debian ya importada en VirtualBox. Debe llamarse igual que
`vbox.vm_name` en `config.json` (por defecto `debian`).

### 2. Reenvío de puertos
Con la VM apagada: VirtualBox → la VM → Configuración → Red → Adaptador 1 →
Avanzado → Reenvío de puertos. Agrega:

| Nombre | Protocolo | Puerto anfitrión | Puerto invitado |
|--------|-----------|------------------|-----------------|
| SSH    | TCP       | 2222             | 22              |

### 3. Copiar la llave SSH a la VM (si aún no está autorizada)
```bash
ssh-copy-id -i ~/.ssh/id_rsa.pub -p 2222 eduardo@127.0.0.1
```

## Uso

```bash
# Controlar la VM (encender/apagar) vía VBoxManage
bash cli.sh start  debian
bash cli.sh stop   debian

# Controlar la VM vía vboxapi (lee vm_name de config.json)
python3 api.py start

# Shell interactiva por SSH (lee host/puerto/usuario/llave de config.json)
bash vbox.sh
```

## Notas
- Los datos de conexión viven en `config.json` (`.gitignore` — no se sube al repo).
- La VM debe estar encendida antes de abrir la shell con `vbox.sh`.
