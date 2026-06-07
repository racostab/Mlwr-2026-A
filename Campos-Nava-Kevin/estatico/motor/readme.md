# estatico/motor/ — API REST (FastAPI)

El cerebro del análisis estático. Recibe muestras, orquesta su análisis en el
`sandbox` y guarda los resultados. La web (y cualquier cliente HTTP) hablan con
él por HTTP.

Es el servicio `engine` de `docker-compose.yml`, expuesto en el puerto **8001**.

## Cómo funciona

1. **Subida** — recibe el archivo, calcula su `sha256`, lo guarda en **su propio**
   volumen `samples` y registra la muestra en la base de datos.
2. **Análisis** — al pedir un comando, busca primero en la tabla `reports`. Si no
   está cacheado, se conecta por SSH al `sandbox`, **envía la muestra por SFTP**
   (`asegurar_remoto`, solo si falta), ejecuta la herramienta del catálogo y
   guarda el resultado.
3. **Caché** — los reportes se guardan por `(sha256, tool)`. Los análisis
   paramétricos (`strings`, `xxd`) no se cachean: dependen de `min_len`/`length`.

> Ya no hay volumen compartido con el `sandbox`: la muestra viaja por SFTP sobre
> el mismo canal SSH. El sandbox es una caja a la que solo se le habla por SSH.

## Endpoints

| Método | Ruta                              | Descripción                              |
|--------|-----------------------------------|------------------------------------------|
| `GET`  | `/health`                         | Estado del servicio                      |
| `GET`  | `/tools`                          | Catálogo de comandos disponibles         |
| `GET`  | `/commands`                       | Binarios permitidos en el comando guiado |
| `GET`  | `/yara/rules`                     | Reglas YARA cargadas en el sandbox       |
| `GET`  | `/stats`                          | Métricas (muestras, reportes, desglose)  |
| `GET`  | `/status`                         | Estado de engine / db / sandbox          |
| `POST` | `/samples`                        | Sube una muestra → `sha256`              |
| `GET`  | `/samples`                        | Lista el historial                       |
| `GET`  | `/samples/{sha256}`               | Metadatos de una muestra                 |
| `GET`  | `/samples/{sha256}/run/{tool}`    | Ejecuta cualquier comando del catálogo   |

El endpoint genérico acepta `?min_len=N` (strings), `?length=N` (xxd) y `?cmd=...`
(comando guiado, `tool=custom`). La lista de `tool` válidos es la de `/tools`
(`hash`, `file`, `entropy`, `ssdeep`, `exiftool`, `readelf`, `yara`, `radare`,
`strings`, `xxd`), más `custom` (oculto): valida el binario contra `/commands`,
prohíbe metacaracteres de shell y anexa la ruta de la muestra al final.

FastAPI sirve además documentación interactiva en http://localhost:8001/docs.

## Archivos

- `principal.py` — la app FastAPI (monta el router y el lifespan).
- `rutas.py` — los endpoints; importa el catálogo de `catalogo.analizador_estatico`.
- `servicios.py` — orquestación: SSH/SFTP al sandbox (`compartido.sftp.conexion`),
  caché y ejecución de analizadores.
- `repositorio.py` — acceso a PostgreSQL con `psycopg`.
- El catálogo estático vive en `estatico/catalogo/` (no aquí): el motor lo copia
  a su imagen e importa como `catalogo.analizador_estatico`.
- El Dockerfile y `requirements.txt` están en `estatico/user_data/motor/`: instala
  el paquete `compartido` con `pip` y copia el código del motor + el catálogo.

## Variables de entorno

Las define `docker-compose.yml`:

| Variable        | Por defecto                | Para qué                          |
|-----------------|----------------------------|-----------------------------------|
| `SAMPLES_DIR`   | `/samples`                 | Dónde guarda el engine las muestras |
| `SANDBOX_HOST`  | `sandbox`                  | Host SSH del sandbox              |
| `SANDBOX_PORT`  | `22`                       | Puerto SSH del sandbox            |
| `SANDBOX_USER`  | `root`                     | Usuario SSH del sandbox           |
| `KEY_PATH`      | `/keys/id_rsa`             | Llave privada del lab (montada)   |
| `DATABASE_URL`  | `postgresql://lab:lab@db…` | Conexión a PostgreSQL             |
