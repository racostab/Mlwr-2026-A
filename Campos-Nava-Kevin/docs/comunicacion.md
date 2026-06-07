
| Servicio   | Tecnología   | Puerto        | Red(es) Docker            |
|------------|--------------|---------------|---------------------------|
| `web`      | Django       | 8000 (al host)| `lab-frontend`            |
| `engine`   | FastAPI      | 8001 (al host)| `lab-frontend`, `lab-sandbox` |
| `db`       | PostgreSQL   | interno       | `lab-frontend`            |
| `sandbox`  | Debian + SSH | interno (22)  | `lab-sandbox` (`internal`)|
| VM Kali    | VirtualBox   | 192.168.56.10:22 | host-only `vboxnet0`, **sin NAT** (fuera de Docker) |

Dos redes Docker (ver `docker-compose.yml`):
- **`lab-frontend`** — bridge normal. Conecta `web`, `engine` y `db`.
- **`lab-sandbox`** — `internal: true`: **sin salida a internet ni al host**.
  Solo `engine` y `sandbox` están en ella. Por eso el `engine` pertenece a las
  dos redes: es el puente entre el frontend y la caja aislada.

## 2. Quién se comunica con quién

```
  navegador
     │ HTTP :8000
     ▼
 ┌───────┐   HTTP :8001    ┌────────┐   SQL :5432    ┌──────┐
 │  web  │ ──────────────▶ │ engine │ ─────────────▶ │  db  │
 └───────┘   (requests)    └────────┘   (psycopg)    └──────┘
                                │
                                │ SSH + SFTP :22   (red lab-sandbox, internal)
                                ▼
                            ┌─────────┐
                            │ sandbox │
                            └─────────┘
```

| Origen   | Destino  | Protocolo     | Red            | Para qué                                   | Código |
|----------|----------|---------------|----------------|--------------------------------------------|--------|
| `web`    | `engine` | HTTP (`requests`) | `lab-frontend` | Subir muestras y pedir análisis. `ENGINE_URL=http://engine:8001` | `web/analizador/servicios.py` |
| `engine` | `db`     | SQL (`psycopg`)   | `lab-frontend` | Guardar muestras y cachear reportes. `DATABASE_URL` | `estatico/motor/repositorio.py` |
| `engine` | `sandbox`| SSH + SFTP (`paramiko`) | `lab-sandbox` | Enviar la muestra y ejecutar las herramientas | `estatico/motor/servicios.py` + `compartido/sftp/conexion.py` |
| host     | VM Kali  | SSH + SFTP (`paramiko`) | host-only | Análisis dinámico: enviar la muestra y volcar memoria | `dinamico/scripts/analizador_dinamico.py` |

Observaciones clave:
- **`web` NO habla con `db` ni con `sandbox`.** Es un cliente delgado: todo pasa
  por el `engine`.
- **`sandbox` no inicia ninguna conexión.** Solo recibe SSH del `engine`. Como
  su red es `internal`, aunque una muestra intente "llamar a casa", no tiene ruta.
- La VM Kali no es Docker: vive en una red **host-only sin NAT** (`192.168.56.10`,
  host `192.168.56.1`), así que no tiene internet. Vagrant la provisiona por NAT
  y luego `dinamico/scripts/red_aislada.py` le quita ese NAT. El firewall
  (`dinamico/reglas_firewall/aislar_host.sh`) corta además lo que la VM inicie
  hacia el host; solo deja pasar las respuestas a las sesiones SSH/SFTP que abre
  el host.

## 3. Cómo se transfiere la muestra (SFTP, sin volumen compartido)

**Decisión de diseño:** el `engine` y el `sandbox` **no comparten ningún volumen**.
La muestra viaja por **SFTP sobre el mismo canal SSH** que se usa para ejecutar las
herramientas. Así el `sandbox` es una caja pura: solo se le habla por SSH.

### Lado estático: engine → sandbox

Paso a paso (todo en `estatico/motor/servicios.py::ejecutar`):

1. El `engine` ya guardó la muestra en su volumen `samples:/samples/<sha256>` al
   recibirla (`POST /samples`, en `rutas.py`).
2. `conectar(SANDBOX_HOST, ...)` abre SSH al sandbox con la llave `/keys/id_rsa`
   → `compartido/sftp/conexion.py::conectar`.
3. `asegurar_remoto(client, local, "/samples/<sha256>")` abre un canal SFTP
   (`client.open_sftp()`) y **sube la muestra solo si falta** (compara tamaño;
   como el nombre es el sha256, igual tamaño ⇒ mismo contenido)
   → `compartido/sftp/conexion.py::asegurar_remoto`.
4. El analizador del catálogo corre la herramienta por SSH sobre esa ruta remota
   (`client.exec_command`, en `estatico/catalogo/analizadores.py`).
5. Se cierra la conexión. El resultado se cachea en `db` (si aplica).

```
engine: /samples/<sha256>  ──SFTP put──▶  sandbox: /samples/<sha256>  ──exec_command──▶  hash/yara/...
```

### Lado dinámico: host → VM Kali

En `dinamico/scripts/analizador_dinamico.py::analizar`:

1. `conectar(host, port, user, key)` abre SSH a la VM (mismo módulo compartido).
2. `subir(client, local, remoto)` sube la muestra por SFTP al `$HOME` de la VM
   → `compartido/sftp/conexion.py::subir`.
3. Se ejecuta la muestra acotada por tiempo y se vuelca su memoria.
4. Se **recuperan** los volcados al host con `client.open_sftp().get(...)`.

## 4. Dónde se usan las funciones de transmisión

Todo el SSH/SFTP está centralizado en **`compartido/sftp/conexion.py`** (un solo
sitio, sin duplicación):

| Función           | Qué hace                        | Quién la llama |
|-------------------|---------------------------------|----------------|
| `conectar(...)`   | Abre el cliente SSH (paramiko)  | `estatico/motor/servicios.py::ssh` · `dinamico/scripts/analizador_dinamico.py::esperar_ssh` |
| `asegurar_remoto` | Sube por SFTP **solo si falta** | `estatico/motor/servicios.py::ejecutar` |
| `subir`           | Sube por SFTP siempre           | `dinamico/scripts/analizador_dinamico.py::analizar` |

La **ejecución** de comandos no usa una función envoltorio: cada analizador llama
`client.exec_command(...)` directamente (`estatico/catalogo/analizadores.py`), y el
runner dinámico tiene su propio helper local `_ejecutar`.

> Si necesitas tocar la transferencia de archivos, el único archivo a editar es
> `compartido/sftp/conexion.py`; su uso está en los dos `::ejecutar`/`::analizar`.
