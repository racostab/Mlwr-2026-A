import paramiko
import os

def setup_y_conectar(host, port, usuario, password):
    key_path = os.path.expanduser("~/.ssh/id_rsa")

    # Generar llave si no existe
    if not os.path.exists(key_path):
        print("Generando llave SSH...")
        key = paramiko.RSAKey.generate(4096)
        key.write_private_key_file(key_path)
        os.chmod(key_path, 0o600)
        with open(key_path + ".pub", "w") as f:
            f.write(f"ssh-rsa {key.get_base64()}")
    else:
        key = paramiko.RSAKey.from_private_key_file(key_path)
        print("Llave existente cargada")

    # Copiar llave si no está en la VM (usa contraseña solo esta vez)
    try:
        print("Intentando conectar sin contraseña...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port=port, username=usuario, pkey=key)
        print("Llave ya estaba configurada")

    except paramiko.AuthenticationException:
        print("Primera vez, copiando llave con contraseña...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port=port, username=usuario, password=password)

        pub_key = open(key_path + ".pub").read()
        _, stdout, _ = client.exec_command(
            f'mkdir -p ~/.ssh && echo "{pub_key}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'
        )
        stdout.read()
        client.close()

        # Reconectar sin contraseña
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port=port, username=usuario, pkey=key)
        print("Llave copiada y conectado sin credenciales")

    return client

def ejecutar(client, comando):
    _, stdout, stderr = client.exec_command(comando)
    salida = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    if salida:
        print(f"[OUT] {salida}")
    if error:
        print(f"[ERR] {error}")
    return salida

# Uso la contraseña solo se usa si es la primera vez
client = setup_y_conectar("127.0.0.1", 2222, "kali", "kali")

# Comandos de análisis
ejecutar(client, "whoami")
ejecutar(client, "ls")

client.close()