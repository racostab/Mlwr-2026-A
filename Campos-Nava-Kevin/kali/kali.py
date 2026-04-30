import paramiko
import configparser
import os

# Leer config_kali.ini
config = configparser.ConfigParser()
config.read("config_kali.ini")

HOST = config["kali"]["host"]
PORT = int(config["kali"]["port"])
USER = config["kali"]["user"]

KEY_PATH = os.path.expanduser("~/.ssh/id_rsa")

def conectar():
    if not os.path.exists(KEY_PATH):
        raise FileNotFoundError(f"No se encontró la llave en {KEY_PATH}")

    os.chmod(KEY_PATH, 0o600)

    key    = paramiko.RSAKey.from_private_key_file(KEY_PATH)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, pkey=key, timeout=10)
    print("[+] Conectado a Kali")
    return client

def ejecutar(client, comando):
    _, stdout, stderr = client.exec_command(comando)
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
ejecutar(client, "cat  /etc/os-release")
client.close()