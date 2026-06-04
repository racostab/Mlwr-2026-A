# api_controller.py
from flask import Flask, request, jsonify
import subprocess
import paramiko
import json
import os

app = Flask(__name__)

# Cargar configuración
with open('config.json', 'r') as f:
    config = json.load(f)

VM_NAME = config['vm_name']
SSH_HOST = config['ssh_host']
SSH_PORT = config['ssh_port']
SSH_USER = config['ssh_user']
SSH_KEY_PATH = os.path.expanduser(config['ssh_key_path'])

def ejecutar_vboxmanage(comando):
    """Ejecuta comandos VBoxManage"""
    try:
        resultado = subprocess.run(
            f'VBoxManage {comando}',
            shell=True,
            capture_output=True,
            text=True
        )
        return {"success": True, "output": resultado.stdout, "error": resultado.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}

def ejecutar_ssh(comando):
    """Ejecuta comandos vía SSH en Kali"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=SSH_HOST,
            port=SSH_PORT,
            username=SSH_USER,
            key_filename=SSH_KEY_PATH
        )
        stdin, stdout, stderr = ssh.exec_command(comando)
        output = stdout.read().decode()
        error = stderr.read().decode()
        ssh.close()
        return {"success": True, "output": output, "error": error}
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Endpoints VM ---
@app.route('/vm/status', methods=['GET'])
def vm_status():
    return jsonify(ejecutar_vboxmanage(f'showvminfo "{VM_NAME}" --machinereadable | grep VMState'))

@app.route('/vm/start', methods=['POST'])
def vm_start():
    return jsonify(ejecutar_vboxmanage(f'startvm "{VM_NAME}" --type headless'))

@app.route('/vm/stop', methods=['POST'])
def vm_stop():
    return jsonify(ejecutar_vboxmanage(f'controlvm "{VM_NAME}" acpipowerbutton'))

@app.route('/vm/snapshot', methods=['POST'])
def vm_snapshot():
    nombre = request.json.get('nombre', 'auto_snapshot')
    return jsonify(ejecutar_vboxmanage(f'snapshot "{VM_NAME}" take "{nombre}"'))

@app.route('/vm/restore/<snapshot>', methods=['POST'])
def vm_restore(snapshot):
    return jsonify(ejecutar_vboxmanage(f'snapshot "{VM_NAME}" restore "{snapshot}"'))

# --- Endpoints Docker en Kali ---
@app.route('/docker/ps', methods=['GET'])
def docker_ps():
    return jsonify(ejecutar_ssh('docker ps -a'))

@app.route('/docker/up', methods=['POST'])
def docker_up():
    return jsonify(ejecutar_ssh('cd ~/lab_malware && docker-compose up -d'))

@app.route('/docker/down', methods=['POST'])
def docker_down():
    return jsonify(ejecutar_ssh('cd ~/lab_malware && docker-compose down'))

@app.route('/docker/exec', methods=['POST'])
def docker_exec():
    contenedor = request.json.get('contenedor')
    comando = request.json.get('comando')
    return jsonify(ejecutar_ssh(f'docker exec {contenedor} {comando}'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)