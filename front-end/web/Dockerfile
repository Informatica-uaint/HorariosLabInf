# ============================================
# Stage 1: Builder - Build de la aplicación
# ============================================
FROM node:20-alpine AS builder

# Metadatos
LABEL maintainer="acceso.informaticauaint.com"
LABEL description="Frontend Web para sistema de acceso QR"

# Build-time argument for API URL
ARG EXPO_PUBLIC_API_URL=http://localhost:5000/api

# Variables de entorno para el build
ENV NODE_ENV=production \
    NPM_CONFIG_LOGLEVEL=warn \
    EXPO_PUBLIC_API_URL=${EXPO_PUBLIC_API_URL}

# Instalar dependencias del sistema y Expo CLI
RUN apk add --no-cache \
    git \
    python3 \
    make \
    g++ && \
    npm install -g @expo/cli@latest

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias para aprovechar cache de Docker
COPY package.json package-lock.json* ./

# Instalar TODAS las dependencias (prod + dev) necesarias para el build
RUN npm ci --prefer-offline --no-audit

# Copiar el resto del código fuente
COPY . .

# Exportar la aplicación para web (genera archivos estáticos optimizados)
# La variable EXPO_PUBLIC_API_URL será embebida en el build
RUN npx expo export -p web --output-dir dist

# ============================================
# Stage 2: Production - Servidor Nginx optimizado
# ============================================
FROM nginx:alpine AS production

# Metadatos para la imagen final
LABEL maintainer="acceso.informaticauaint.com"
LABEL description="Frontend Web estático para sistema de acceso QR"
LABEL stage="production"

# Instalar curl para healthcheck
RUN apk add --no-cache curl

# Copiar configuración personalizada de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar archivos estáticos desde la etapa de build
COPY --from=builder /app/dist /usr/share/nginx/html

# Crear usuario nginx si no existe y ajustar permisos
RUN addgroup -g 101 -S nginx 2>/dev/null || true && \
    adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx 2>/dev/null || true && \
    chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# Cambiar a usuario no-root
USER nginx

# Exponer puerto 8080 (no privilegiado)
EXPOSE 8080

# Health check para verificar que Nginx está funcionando
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Comando para ejecutar Nginx
CMD ["nginx", "-g", "daemon off;"]