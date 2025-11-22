# ============================================
# Stage 1: Builder - Instalación de dependencias
# ============================================
FROM python:3.11-slim AS builder

# Variables de entorno para el builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema necesarias para compilar
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    pkg-config \
    cargo \
    rustc \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar solo requirements.txt para aprovechar cache de Docker
COPY requirements.txt .

# Instalar dependencias globalmente
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# Stage 2: Runtime - Imagen final optimizada
# ============================================
FROM python:3.11-slim AS production

# Metadatos
LABEL maintainer="acceso.informaticauaint.com"
LABEL description="Web API Flask para sistema de acceso"
LABEL stage="production"

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production

# Instalar solo dependencias de runtime necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

# Crear directorio de trabajo
WORKDIR /app

# Copiar dependencias de Python desde el builder
COPY --from=builder /usr/local /usr/local

# Copiar código fuente
COPY --chown=appuser:appuser . .

# Crear directorio para certificados SSL
RUN mkdir -p /app/certs && chown appuser:appuser /app/certs

# Cambiar a usuario no-root
USER appuser

# Exponer puerto
EXPOSE 5000

# Comando de salud
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f -k https://localhost:5000/api/health || curl -f http://localhost:5000/api/health || exit 1

# Comando por defecto
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--certfile=certificate.pem", "--keyfile=privatekey.pem", "app:app"]
