# HorariosLabInf

This repository contains the code for a small access control system used in the computer labs. It is split into multiple subprojects:

- **back-end** – Python/Flask services.
- **front-end** – The Expo application (React Native/TypeScript).
- **cliente** – Optional local client built with Kivy.
- **static** – Static files such as user photos.

## Architecture Overview

The main architecture is based on Flask REST APIs that expose the data used by the clients. The Expo application communicates with these APIs. A simple Kivy client is also provided for local usage when running on a computer with a webcam.

```
[front-end (Expo)]        <--->  [back-end/web]
                           ^
                           |
[cliente (Kivy desktop)] ---->  [back-end/lector]
                                [back-end/api_estudiantes]
```

- `back-end/web` – Main API with authentication, schedules and other routes.
- `back-end/api_estudiantes` – Dedicated API that provides student information and QR validation.
- `back-end/lector` – Lightweight service for reading temporary QR codes.
- `front-end` – Expo project containing the React Native mobile/web app. See its own `README.md` for development instructions.
- `cliente` – Stand‑alone Kivy application that can read QR codes locally.
- `static` – Repository of static assets such as images.

## Prerequisites

- **Python 3.11** or newer for the back‑end services and optional Kivy client.
- **Node.js 18** (or the version used by Expo) for the front‑end.
- A MySQL database (or compatible) configured via environment variables.

Each service expects an `.env` file with its configuration. The variables follow the standard names seen in the source (`MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`, `JWT_SECRET`, etc.).

## Running the Back‑end Services

1. **Main Web API**

   ```bash
   cd back-end/web
   python -m venv venv && source venv/bin/activate  # optional
   pip install -r requirements.txt
   python app.py
   ```

   By default it listens on `https://localhost:5000` using the SSL certificates found in the directory. In production `gunicorn` can be used as shown in the `Dockerfile`.

2. **Student API**

   ```bash
   cd back-end/api_estudiantes
   python -m venv venv && source venv/bin/activate  # optional
   pip install -r requirements.txt
   python run.py
   ```

3. **QR Reader API**

   ```bash
   cd back-end/lector
   python -m venv venv && source venv/bin/activate  # optional
   pip install Flask flask-cors PyMySQL gunicorn python-dotenv
   python api_qr_temporal.py
   ```

   The commands above start each Flask service in development mode. Adjust the environment variables as needed for MySQL connectivity.

## Running the Expo Front‑end

```bash
cd front-end
npm install
npx expo start
```

Open the QR code displayed in the terminal with the Expo Go mobile application or use a simulator/emulator.
See `front-end/README.md` for additional details.

## Optional Local Client

A desktop client using Kivy is provided in the `cliente` directory. To run it:

```bash
cd cliente
python ver.py
```

It will open a simple GUI that uses the webcam to scan QR codes and communicates with the back‑end.

---

More detailed documentation will live in each subproject's future `README` files. This top‑level guide only gives a quick overview of how the repository is organised and how to start the main components.
