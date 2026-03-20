import paramiko
import configparser
import os


# Leer config_debian.ini (espera que el archivo exista en el directorio
# desde donde se ejecuta el script)
config = configparser.ConfigParser()
config.read("config_debian.ini")

# Parámetros de conexión leídos desde la sección [debian]
HOST = config["debian"]["host"]
PORT = int(config["debian"]["port"])
USER = config["debian"]["user"]

# Ruta de la llave privada en el equipo local (expandir ~)
KEY_PATH = os.path.expanduser("~/.ssh/id_rsa")


def conectar():
    # Verificar que la llave privada existe antes de intentar conectar
    if not os.path.exists(KEY_PATH):
        raise FileNotFoundError(f"No se encontró la llave en {KEY_PATH}")

    # Ajustar permisos de la llave privada para que sólo el propietario la lea
    os.chmod(KEY_PATH, 0o600)

    # Cargar la llave privada y conectar con Paramiko
    key = paramiko.RSAKey.from_private_key_file(KEY_PATH)
    client = paramiko.SSHClient() # Crear cliente SSH de Paramiko
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # Aceptar host keys automáticamente 
    client.connect(HOST, port=PORT, username=USER, pkey=key, timeout=10)
    print("[+] Conectado a Debian")
    return client

def ejecutar(client, comando):
    _, stdout, stderr = client.exec_command(comando)
    # Esperar a que termine el comando (sin límite de timeout aquí)
    stdout.channel.recv_exit_status()
    salida = stdout.read().decode().strip()
    error  = stderr.read().decode().strip()
    if salida:
        print(f"[OUT] {salida}")
    if error:
        print(f"[ERR] {error}")
    return salida


client = conectar()
ejecutar(client, "whoami")
ejecutar(client, "uname -a")
client.close()