from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import paramiko
import os

app = FastAPI()

VM_HOST = "192.168.106.128"
VM_USER = "fak3me"
KEY_PATH = os.path.expanduser("~/.ssh/id_rsa")
API_TOKEN = "529d232021e4de877a81fcef9100b690f075836411419898e5905a0758db21e8"

class CMD(BaseModel):
    token: str
    command: str

@app.post("/run")
def run(cmd: CMD):
    if cmd.token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API token")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        VM_HOST,
        username=VM_USER,
        key_filename=KEY_PATH,
        allow_agent=True,
        look_for_keys=False,
        timeout=10,
    )

    stdin, stdout, stderr = ssh.exec_command(cmd.command, timeout=60)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    code = stdout.channel.recv_exit_status()
    ssh.close()


    return {"stdout": out, "stderr": err, "returncode": code}