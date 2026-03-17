## Como Correr el FastApy
Para iniciar el apy fast, se necesita generar primero el ambiente. Iniciamos Uvicorn
```
pip install uvicorn fastapi paramiko
```
Unavez instalado uvicorn, usamos el comando para encender el fast apy
```
uvicorn apy:app --host 127.0.0.1 --port 8000
```