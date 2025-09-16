# Web API

This service exposes the main Flask application used by the system to manage helpers and records.

## Dependencies

Contents of `requirements.txt`:

```
Flask==2.3.3
flask-cors==4.0.0
PyMySQL==1.1.0
PyJWT==2.8.0
cryptography==41.0.3
pytz==2023.3
APScheduler==3.10.4
requests==2.31.0
python-dotenv==1.0.0
gunicorn==21.2.0
Werkzeug==2.3.7
```

## Environment variables

- `JWT_SECRET` – secret key for JWT tokens.
- `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`, `MYSQL_PORT` – MySQL connection settings.
- `DB_CHARSET` – charset for the database (default `utf8mb4`).

Variables are normally loaded from a `.env` file or the environment.

## Running

For development the application can be started with:

```bash
python app.py
```

For production the included Dockerfile runs gunicorn:

```bash
docker build -t horarios-web .
docker run -p 5000:5000 horarios-web
```

## Scheduled tasks

`tasks/scheduled_tasks.py` defines two APScheduler jobs:

- **Daily closing** – POSTs to `/api/procesar_salidas_pendientes` every day at `23:59`.
- **Weekly reset** – POSTs to `/reiniciar_cumplimiento` every Sunday at `23:55`.

## API endpoints

Endpoints are grouped in blueprints. Some notable routes are:

- `POST /api/ayudantes/register` – register an administrator.
- `GET /registros`, `GET /registros_hoy` – obtain records.
- `GET /usuarios` – list allowed users.
- `GET /cumplimiento` – fetch compliance status.
- `GET /horas_acumuladas` – total hours worked.
- `GET /estado_usuarios` – status of all users.

Refer to the code inside `routes/` for the full list.
