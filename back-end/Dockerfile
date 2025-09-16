# back-end/web/Dockerfile
FROM python:3.11-slim

# Metadatos
LABEL maintainer="acceso.informaticauaint.com"
LABEL description="Web API Flask para sistema de acceso"

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear directorio para certificados SSL
RUN mkdir -p /app/certs

# Cambiar propietario de archivos
RUN chown -R appuser:appuser /app

# Cambiar a usuario no-root
USER appuser

# Exponer puerto
EXPOSE 5000

# Comando de salud
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('https://localhost:5000/health', verify=False)" || exit 1

# Comando por defecto
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--certfile=certificate.pem", "--keyfile=privatekey.pem", "app:app"]
