import paramiko
import os

def setup_y_conectar(host, port, usuario):
    # La llave privada viene con el ISO, siempre en la misma ruta
    key_path = os.path.expanduser("~/.ssh/id_rsa")

    if not os.path.exists(key_path):
        raise FileNotFoundError("La llave privada no está, verificá el ISO")

    key = paramiko.RSAKey.from_private_key_file(key_path)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=usuario, pkey=key, timeout=10)
    print("[+] Conectado")
    return client


def ejecutar(client, comando):
    _, stdout, stderr = client.exec_command(comando)
    stdout.channel.recv_exit_status()
    salida = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    if salida:
        print(f"[OUT] {salida}")
    if error:
        print(f"[ERR] {error}")
    return salida


# Sin contraseña, sin setup — la llave ya está en el ISO
client = setup_y_conectar("127.0.0.1", 2222, "kali")

ejecutar(client, "whoami")
ejecutar(client, "uname -a")

client.close()