"""Conexión SSH y transferencia de archivos por SFTP.

Este es el ÚNICO punto donde el lab abre conexiones SSH y mueve archivos entre
máquinas. Lo usan las dos familias de análisis:

- Estático: `estatico/motor/servicios.py` → `conectar()` + `asegurar_remoto()`
  para enviar la muestra del motor al contenedor `sandbox`.
- Dinámico: `dinamico/scripts/analizador_dinamico.py` → `conectar()` + `subir()`
  para enviar la muestra del host a la VM Kali.

Todas las funciones reciben un `client` de paramiko ya conectado (salvo
`conectar`, que es quien lo crea).
"""
import os

import paramiko


def conectar(host: str, port: int, user: str, key_path: str, label: str = "host") -> paramiko.SSHClient:
    """Abre una conexión SSH autenticada por llave y devuelve el cliente.

    `key_path` es la llave privada del lab (`lab_keys/id_rsa`). La parte pública
    está instalada como `authorized_keys` en el destino (sandbox o VM).
    """
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
    """Sube un archivo por SFTP (`local` → `remoto`), siempre."""
    sftp = client.open_sftp()
    try:
        sftp.put(local, remoto)
    finally:
        sftp.close()
    print(f"[+] Subido: {local} → {remoto}")


def asegurar_remoto(client: paramiko.SSHClient, local: str, remoto: str) -> None:
    """Garantiza que `local` esté en `remoto` (vía SFTP), subiéndolo solo si falta  """
    sftp = client.open_sftp()
    try:
        try:
            remoto_stat = sftp.stat(remoto)
            local_size  = os.path.getsize(local)
            if remoto_stat.st_size == local_size:
                return  # ya está
        except FileNotFoundError:
            pass  # no existe → hay que subirlo
        sftp.put(local, remoto)
        print(f"[+] Muestra enviada al sandbox: {remoto}")
    finally:
        sftp.close()
