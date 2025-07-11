# Estudiantes API

This module implements the REST API for student access using Flask. It exposes endpoints to register student presence, manage student data and validate QR codes.

## Dependencies

```
Flask==3.0.0
Flask-CORS==4.0.0
mysql-connector-python==8.2.0
python-dotenv==1.0.0
gunicorn==21.2.0
python-dateutil==2.8.2
pytest==7.4.3
pytest-flask==1.3.0
black==23.11.0
flake8==6.1.0
pytz
```

## Environment variables

- `SECRET_KEY` – Flask secret.
- `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB` – MySQL settings.
- `HOST`, `PORT` – bind address for the server.
- `FLASK_ENV` – set to `development` for debug mode.

Variables are loaded via `python-dotenv`.

## Running

The service can be started directly with:

```bash
python run.py
```

In production you may run `gunicorn`:

```bash
gunicorn --bind 0.0.0.0:5000 app:app
```

## API endpoints

`routes/` defines several groups:

- `/estudiantes_presentes/estudiantes` – list all students and mark presence.
- `/estudiantes` – CRUD operations for students.
- `/registros` and related endpoints – retrieve register logs.
- `/qr/*` – validate QR codes and check status/history.
- `/api/health` – basic health check.

See the route files for further details.
