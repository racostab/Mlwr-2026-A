
import os
import paramiko


def conectar(host: str, port: int, user: str, key_path: str, label: str = "host") -> paramiko.SSHClient:
    key_path = os.path.expanduser(key_path)
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"Llave SSH no encontrada: {key_path}")
    try:
        os.chmod(key_path, 0o600)
    except OSError:
        pass  # llave montada read-only desde un volumen Docker
    key    = paramiko.RSAKey.from_private_key_file(key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, pkey=key, timeout=10)
    print(f"[+] Conectado a {label}")
    return client


def subir(client: paramiko.SSHClient, local: str, remoto: str) -> None:
    sftp = client.open_sftp()
    sftp.put(local, remoto)
    sftp.close()
    print(f"[+] Subido: {local} → {remoto}")


def ejecutar(client: paramiko.SSHClient, comando: str) -> str:
    _, stdout, stderr = client.exec_command(comando)
    stdout.channel.recv_exit_status()
    salida = stdout.read().decode().strip()
    error  = stderr.read().decode().strip()
    if salida:
        print(f"[OUT] {salida}")
    if error:
        print(f"[ERR] {error}")
    return salida
