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
├── lab_web/             proyecto Django (settings, urls, wsgi)
└── analyzer/            app principal
    ├── views.py         lógica de las páginas
    ├── urls.py          rutas
    └── templates/       index.html · results.html · history.html
```

## Páginas

| Ruta        | Vista     | Qué hace                                                  |
|-------------|-----------|-----------------------------------------------------------|
| `/`         | `index`   | Formulario de subida. Al enviar, sube la muestra al engine y muestra el reporte completo (`results.html`). |
| `/history/` | `history` | Lista todas las muestras analizadas.                      |

## Comunicación con el engine

La vista usa la variable de entorno `ENGINE_URL` para saber dónde está la API
(en Compose: `http://engine:8001`). Sube el archivo a `POST /samples` y luego
pide cada reporte (`/hash`, `/file`, `/strings`, ...).

## Nota

Es una app de laboratorio: corre con `DEBUG=True`, `SECRET_KEY` de desarrollo y
`ALLOWED_HOSTS = ['*']`. Suficiente para uso local; **no apta para producción**.
