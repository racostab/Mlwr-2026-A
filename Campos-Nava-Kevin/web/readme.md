# web/ — Interfaz web (Django)

Front-end del lab: una página para subir muestras y ver el reporte, más un
historial. No analiza nada por su cuenta — todo lo pide al `engine` por HTTP.

Es el servicio `web` de `docker-compose.yml`, expuesto en el puerto **8000**.

## Estructura

```
web/
├── manage.py            utilidad de gestión de Django
├── Dockerfile           imagen del servicio
├── requirements.txt     django, requests
├── sitio/               proyecto Django (configuracion.py, rutas.py, wsgi.py)
└── analizador/          app principal
    ├── servicios.py     lógica de las páginas (las "views")
    ├── rutas.py         rutas de la app
    └── templates/       index.html · results.html · history.html
```

## Páginas

| Ruta        | Vista     | Qué hace                                                  |
|-------------|-----------|-----------------------------------------------------------|
| `/`         | `index`   | Sube N muestras y elige qué comandos correr (checkboxes del catálogo) + un comando guiado opcional. Muestra el reporte (`results.html`). |
| `/history/` | `history` | Lista todas las muestras analizadas.                      |
| `/rules/`   | `rules`   | Reglas YARA cargadas en el sandbox (`/yara/rules`).       |
| `/stats/`   | `stats`   | Métricas del lab (`/stats`).                              |
| `/status/`  | `status`  | Estado de engine / db / sandbox (`/status`).              |
| `/docs/`    | `docs`    | Guía de uso, catálogo de comandos y lista blanca.         |

## Comunicación con el engine

La vista usa la variable de entorno `ENGINE_URL` (en Compose: `http://engine:8001`).
Pide el catálogo a `GET /tools` para pintar los checkboxes, sube cada archivo a
`POST /samples` y ejecuta los comandos elegidos vía `GET /samples/{sha}/run/{tool}`.
`results.html` renderiza cada resultado de forma genérica según su tipo
(pares clave/valor, coincidencias YARA o bloque de texto).

## Nota

Es una app de laboratorio: corre con `DEBUG=True`, `SECRET_KEY` de desarrollo y
`ALLOWED_HOSTS = ['*']`. Suficiente para uso local; **no apta para producción**.
