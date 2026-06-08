# dinamico/sftp/ — Transferencia SFTP (puntero)

El análisis dinámico sube la muestra a la VM Kali por **SFTP**, usando el mismo
módulo compartido que el lado estático: **`compartido/sftp/conexion.py`**.

No hay código duplicado aquí: el runner (`dinamico/analizador/`, en `ejecucion.py`)
importa `from compartido.sftp.conexion import conectar_con_reintentos, subir` y,
tras ejecutar la muestra, recupera el volcado con `client.open_sftp().get(...)`.

Esta carpeta existe solo para dejar explícito que el dinámico también transfiere
por SFTP (igual que `estatico/`, que lo usa para enviar la muestra al sandbox).
