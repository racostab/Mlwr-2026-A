import paramiko
import os

def conectar(host, port, usuario):
    # Ruta de la llave privada SSH en tu máquina
    key_path = os.path.expanduser("~/.ssh/id_rsa")
    
    # Cargar la llave privada desde el archivo
    key = paramiko.RSAKey.from_private_key_file(key_path)

    # Crear el cliente SSH
    client = paramiko.SSHClient()
    
    # Aceptar automáticamente hosts desconocidos (sin pedir confirmación)
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Conectar a la VM usando la llave (sin contraseña)
    client.connect(host, port=port, username=usuario, pkey=key)
    
    return client

def ejecutar(client, comando):
    # Ejecutar el comando en la VM
    _, stdout, stderr = client.exec_command(comando)
    
    # Leer la salida del comando
    salida = stdout.read().decode().strip()
    
    # Leer errores si los hay
    error = stderr.read().decode().strip()
    
    # Imprimir salida y errores
    if salida:
        print(f"[OUT] {salida}")
    if error:
        print(f"[ERR] {error}")
    
    return salida

# Conectar a la VM (port forwarding 2222 -> 22 de la VM)
client = conectar("127.0.0.1", 2222, "kali")

# Ejecutar comandos en la VM
ejecutar(client, "whoami")
ejecutar(client, "uname -a")

# Cerrar la conexión al terminar
client.close()