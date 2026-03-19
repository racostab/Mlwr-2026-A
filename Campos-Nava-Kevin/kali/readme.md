# SSH Automation - Kali Linux (VirtualBox)

## Requisitos
- VirtualBox instalado
- Python 3
- paramiko: `pip install paramiko`
- sshpass: `sudo apt install sshpass`
- OpenSSH: `sudo apt install openssh-client`

## Configuración inicial (solo una vez)

### 1. Importar la VM
Abre VirtualBox → Archivo → Importar servicio virtualizado → selecciona el `.ova`

### 2. Configurar reenvío de puertos
En VirtualBox con la VM apagada:
1. Selecciona la VM → Configuración → Red → Adaptador 1 → Avanzado → Reenvío de puertos
2. Agrega esta regla:

| Nombre | Protocolo | Puerto anfitrión | Puerto invitado |
|--------|-----------|------------------|-----------------|
| SSH    | TCP       | 2222             | 22              |

### 3. Iniciar la VM
Arranca Kali desde VirtualBox.

### 4. Generar llaves SSH (si no tienes)
```bash
ssh-keygen -t rsa -b 4096
```

### 5. Copiar llave pública a Kali
```bash
sshpass -p kali ssh-copy-id -i ~/.ssh/id_rsa.pub -p 2222 -o StrictHostKeyChecking=no kali@127.0.0.1
```

### 6. Crear config_kali.ini
```ini
[kali]
host = 127.0.0.1
port = 2222
user = kali
```

## Uso
```bash
python3 kali.py
```

## Notas
- `config_kali.ini` está en `.gitignore`, no se sube al repo
- La contraseña por defecto de Kali es `kali`
- La VM debe estar corriendo antes de ejecutar el script