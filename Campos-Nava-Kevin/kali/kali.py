import paramiko
import configparser
import os

# Leer config_kali.ini
config = configparser.ConfigParser()
config.read("config_kali.ini")

HOST = config["kali"]["host"]
PORT = int(config["kali"]["port"])
USER = config["kali"]["user"]
PASS = config["kali"]["password"]

KEY_PATH = os.path.expanduser("~/.ssh/id_rsa")

def copiar_llave():
    pub_key_path = KEY_PATH + ".pub"

    if not os.path.exists(pub_key_path):
        raise FileNotFoundError(f"No se encontró {pub_key_path}")

    with open(pub_key_path, "r") as f:
        pub_key = f.read().strip()

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=10)

    comandos = [
        "mkdir -p ~/.ssh",
        "chmod 700 ~/.ssh",
        f'grep -qxF "{pub_key}" ~/.ssh/authorized_keys 2>/dev/null || echo "{pub_key}" >> ~/.ssh/authorized_keys',
        "chmod 600 ~/.ssh/authorized_keys"
    ]
    for cmd in comandos:
        _, stdout, _ = client.exec_command(cmd)
        stdout.channel.recv_exit_status()

    client.close()
    print("[+] Llave pública copiada")

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

copiar_llave()
client = conectar()
ejecutar(client, "whoami")
ejecutar(client, "uname -a")
client.close()