import paramiko
import configparser

config = configparser.ConfigParser()
config.read("config.init")

SSH_HOST = config.get("vbox", "SSH_HOST")
SSH_PORT = int(config.get("vbox", "SSH_PORT"))
SSH_USER = config.get("vbox", "SSH_USER")

def conectar():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, timeout=10)
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

client = conectar()
ejecutar(client, "whoami")
ejecutar(client, "ls /home/eduardo/Desktop")
ejecutar(client, "pwd")
client.close()

