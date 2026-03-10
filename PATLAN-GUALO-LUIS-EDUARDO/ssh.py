import sys
import signal
import paramiko

SSH_HOST = "127.0.0.1"
SSH_PORT = 2222
SSH_USER = "eduardo"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def disconnect(sig=None, frame=None):
    print("\n[SSH] Cerrando sesión...")
    client.close()
    sys.exit(0)

signal.signal(signal.SIGINT, disconnect)
signal.signal(signal.SIGTERM, disconnect)

print(f"[SSH] Conectando → {SSH_USER}@{SSH_HOST}:{SSH_PORT}")
client.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USER, timeout=10)
print("[SSH] ✓ Conectado.\n")

channel = client.invoke_shell()
channel.settimeout(0.0)

import threading, socket

def reader():
    while True:
        try:
            data = channel.recv(1024)
            if not data:
                break
            sys.stdout.write(data.decode(errors="replace"))
            sys.stdout.flush()
        except socket.timeout:
            pass
        except Exception:
            break

threading.Thread(target=reader, daemon=True).start()

try:
    while True:
        cmd = input()
        channel.send(cmd + "\n")
        if cmd.strip() == "exit":
            break
except (EOFError, KeyboardInterrupt):
    pass

disconnect()