# db/ — Base de datos (PostgreSQL)

Persistencia del lab: historial de muestras y caché de reportes de análisis.

Es el servicio `db` de `docker-compose.yml` (imagen `postgres:16-alpine`). Solo
el `engine` se conecta a él, por la red interna `lab-frontend`.

## `init.sql`

Postgres ejecuta este script **una sola vez**, al crear el contenedor por primera
vez (lo monta en `/docker-entrypoint-initdb.d/`). Define dos tablas:

### `samples` — muestras subidas

| Columna       | Tipo          | Notas                        |
|---------------|---------------|------------------------------|
| `sha256`      | `TEXT`        | clave primaria               |
| `filename`    | `TEXT`        | nombre original del archivo  |
| `size`        | `BIGINT`      | tamaño en bytes              |
| `uploaded_at` | `TIMESTAMPTZ` | fecha de subida (`now()`)    |

### `reports` — reportes de análisis (caché)

| Columna      | Tipo          | Notas                                       |
|--------------|---------------|---------------------------------------------|
| `sha256`     | `TEXT`        | FK → `samples` (`ON DELETE CASCADE`)        |
| `kind`       | `TEXT`        | tipo de análisis: `hash`, `file`, `entropy`, `ssdeep`, `exiftool`, `readelf` |
| `payload`    | `JSONB`       | resultado del análisis                      |
| `created_at` | `TIMESTAMPTZ` | fecha de generación                         |

Clave primaria compuesta `(sha256, kind)`: cada muestra guarda un reporte por
tipo. El `engine` consulta esta tabla antes de analizar; si ya existe, no vuelve
a ejecutar la herramienta en el sandbox.

> `strings` no se cachea (depende del parámetro `min_len`), siempre se recalcula.

## Persistencia

Los datos viven en el volumen Docker `db-data`. `lab.py down` / `docker compose
down` **no** borra ese volumen. Para empezar de cero:
`docker compose down -v`.

## Credenciales

Usuario, contraseña y nombre de base se toman de `.env`
(`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`).
