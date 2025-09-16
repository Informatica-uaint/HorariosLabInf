# HorariosLabInf

This repository contains the code for a small access control system used in the computer labs. It is split into multiple subprojects:

- **back-end** – Python/Flask services.
- **front-end** – The Expo application (React Native/TypeScript).
- **cliente** – Optional local client built with Kivy.
- **static** – Static files such as user photos.

## Architecture Overview

The main architecture is based on Flask REST APIs that expose the data used by the clients. The Expo application communicates with these APIs. A simple Kivy client is also provided for local usage when running on a computer with a webcam.

```
[front-end (Expo)]        <--->  [back-end]
                           ^      (Unified API)
                           |
[cliente (Kivy desktop)] ------>
```

- `back-end` – Unified API with authentication, schedules, student management, QR validation, and all routes.
- `front-end` – Expo project containing the React Native mobile/web app. See its own `README.md` for development instructions.
- `cliente` – Stand‑alone Kivy application that can read QR codes locally.
- `static` – Repository of static assets such as images.

## Prerequisites

- **Python 3.11** or newer for the back‑end services and optional Kivy client.
- **Node.js 18** (or the version used by Expo) for the front‑end.
- A MySQL database (or compatible) configured via environment variables.

Each service expects an `.env` file with its configuration. The variables follow the standard names seen in the source (`MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`, `JWT_SECRET`, etc.).

## Running the Back‑end API

**Unified API (All Services)**

   ```bash
   cd back-end
   python -m venv venv && source venv/bin/activate  # optional
   pip install -r requirements.txt
   python app.py
   ```

   By default it listens on `https://localhost:5001` using the SSL certificates found in the directory. In production `gunicorn` can be used as shown in the `Dockerfile`.

   The unified API provides all endpoints:
   - `/api/auth/*` - Authentication and user management
   - `/api/estudiantes/*` - Student management
   - `/api/qr/*` - QR code validation and generation
   - `/api/registros/*` - Access record management
   - `/api/horarios/*` - Schedule management
   - `/api/cumplimiento/*` - Compliance tracking
   - `/api/horas/*` - Hour tracking
   - `/api/estado/*` - Status management
   - `/api/health` - Health check

## Running the Expo Front‑end

```bash
cd front-end/web
npm install
npx expo start
```

Open the QR code displayed in the terminal with the Expo Go mobile application or use a simulator/emulator.
See `front-end/web/README.md` for additional details.

## Optional Local Client

A desktop client using Kivy is provided in the `cliente` directory. To run it:

```bash
cd cliente
python ver.py
```

It will open a simple GUI that uses the webcam to scan QR codes and communicates with the unified back‑end API.

---

More detailed documentation will live in each subproject's future `README` files. This top‑level guide only gives a quick overview of how the repository is organised and how to start the main components.
