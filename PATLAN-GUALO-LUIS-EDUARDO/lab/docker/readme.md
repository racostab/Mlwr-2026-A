# Docker SSH - Debian

## Requisitos
- Docker instalado
- Python 3 con paramiko: `pip install paramiko`
- sshpass: `sudo apt install sshpass`

## Configuración inicial (solo una vez)

### 1. Iniciar Docker
```bash
sudo systemctl start docker
```

### 2. Construir la imagen
```bash
docker build -t mi-debian .
```

### 3. Crear el contenedor
```bash
docker run -d --name debian -p 2223:22 --restart always mi-debian
```

### 4. Crear usuario dentro del contenedor
```bash
docker exec -it debian bash
useradd -m -s /bin/bash tu_usuario
passwd tu_usuario
exit
```

### 5. Crear config_debian.ini en la misma ruta
```ini
[debian]
host     = 127.0.0.1
port     = 2223
user     = tu_usuario
password = tu_contraseña
```

### 6. Generar llaves SSH (si no tienes)
```bash
ssh-keygen -t rsa -b 4096
```

### 7. Copiar llave pública al contenedor (solo una vez)
```bash
sshpass -p tu_contraseña ssh-copy-id -i ~/.ssh/id_rsa.pub -p 2223 -o StrictHostKeyChecking=no tu_usuario@127.0.0.1
```

## Uso diario
```bash
bash debian.sh
# o
python3 debian.py
```
