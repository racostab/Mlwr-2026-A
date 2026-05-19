# engine/ — API REST (FastAPI)

El cerebro del lab. Recibe muestras, orquesta su análisis en el `sandbox` y
guarda los resultados. Tanto la CLI (`lab.py`) como la web hablan con él por HTTP.

Es el servicio `engine` de `docker-compose.yml`, expuesto en el puerto **8001**.

## Cómo funciona

1. **Subida** — recibe el archivo, calcula su `sha256`, lo guarda en el volumen
   compartido `samples` y registra la muestra en la base de datos.
2. **Análisis** — al pedir un reporte, primero busca en la tabla `reports` de la
   BD. Si no está cacheado, se conecta por SSH al `sandbox`, ejecuta la
   herramienta sobre el archivo y guarda el resultado.
3. **Caché** — los reportes se guardan por `(sha256, kind)`; analizar dos veces
   la misma muestra no repite el trabajo (`strings` es la excepción: depende de
   `min_len`, siempre se recalcula).

El volumen `samples` está montado en `/samples` tanto en el `engine` como en el
`sandbox`, así que ambos ven el mismo archivo.

## Endpoints

| Método | Ruta                          | Descripción                          |
|--------|-------------------------------|--------------------------------------|
| `GET`  | `/health`                     | Estado del servicio                  |
| `POST` | `/samples`                    | Sube una muestra → `sha256`          |
| `GET`  | `/samples`                    | Lista el historial                   |
| `GET`  | `/samples/{sha256}`           | Metadatos de una muestra             |
| `GET`  | `/samples/{sha256}/hash`      | MD5 / SHA1 / SHA256                  |
| `GET`  | `/samples/{sha256}/file`      | Tipo de archivo (`file`)             |
| `GET`  | `/samples/{sha256}/strings`   | Cadenas (`?min_len=N`)               |
| `GET`  | `/samples/{sha256}/entropy`   | Entropía de Shannon                  |
| `GET`  | `/samples/{sha256}/ssdeep`    | Fuzzy hash                           |
| `GET`  | `/samples/{sha256}/exiftool`  | Metadatos                            |
| `GET`  | `/samples/{sha256}/readelf`   | Cabeceras ELF                        |

FastAPI sirve además documentación interactiva en http://localhost:8001/docs.

## Archivos

- `main.py` — la aplicación FastAPI: rutas y orquestación.
- `db.py` — acceso a PostgreSQL con `psycopg` (`save_sample`, `list_samples`,
  `get_report`, `save_report`...).
- `Dockerfile` — imagen del servicio; copia también `core/ssh.py` y
  `docker/debian.py`, que el engine reutiliza.
- `requirements.txt` — `fastapi`, `uvicorn`, `paramiko`, `psycopg`...

## Variables de entorno

Las define `docker-compose.yml`:

| Variable        | Por defecto                | Para qué                          |
|-----------------|----------------------------|-----------------------------------|
| `SAMPLES_DIR`   | `/samples`                 | Dónde se guardan las muestras     |
| `SANDBOX_HOST`  | `sandbox`                  | Host SSH del sandbox              |
| `SANDBOX_PORT`  | `22`                       | Puerto SSH del sandbox            |
| `SANDBOX_USER`  | `root`                     | Usuario SSH del sandbox           |
| `KEY_PATH`      | `/keys/id_rsa`             | Llave privada del lab (montada)   |
| `DATABASE_URL`  | `postgresql://lab:lab@db…` | Conexión a PostgreSQL             |
