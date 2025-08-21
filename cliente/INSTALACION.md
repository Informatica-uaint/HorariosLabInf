# 🔧 INSTALACIÓN LECTOR QR - LABORATORIO INFORMÁTICA

## 📋 Requisitos del Sistema
- Windows 10/11
- Python 3.9 o superior
- Cámara web conectada
- Conexión a internet (para acceso a MySQL remoto)

## 🚀 Instalación Paso a Paso

### 1. Copiar Archivos
Copia toda la carpeta `cliente` al nuevo PC en cualquier ubicación.

### 2. Instalar Python (si no está instalado)
Descarga Python desde: https://python.org/downloads/
- ✅ Marca "Add Python to PATH"
- Instala Python 3.9 o superior

### 3. Instalar Dependencias
Abre **Command Prompt** o **PowerShell** como administrador:

```bash
cd "ruta\donde\copiaste\cliente"
pip install -r requirements_pc.txt
```

### 4. Configurar Base de Datos
**IMPORTANTE:** Crea el archivo `.env` con las credenciales:

```bash
# En la carpeta cliente, copia .env.example como .env
copy .env.example .env
```

**O manualmente:**
Crea un archivo llamado `.env` (sin extensión) con este contenido:

```
MYSQL_HOST=10.0.3.54
MYSQL_USER=root
MYSQL_PASSWORD=CxJEv99!fnm1WUS6GyubBvPlqYjUP@
MYSQL_DB=registro_qr
MYSQL_PORT=3306

CLIENT_NAME=Lector QR Laboratorio
DEBUG=true
```

### 5. Ejecutar Lector QR
```bash
python ver.py
```

## 🔍 Verificación de Instalación

### ✅ Checks de Estado
Al iniciar, verifica que veas:
- `Cámara inicializada correctamente en índice X`
- `Base de datos: CONECTADA` (no ERROR)
- Interfaz con estado "Lector QR Activo"

### ❌ Problemas Comunes

**Error de MySQL:**
```
Error conectando a MySQL: (2003, "Can't connect to...")
```
**Solución:**
1. Verifica que el archivo `.env` existe en la carpeta `cliente`
2. Verifica que las credenciales en `.env` son correctas
3. Verifica conectividad de red al servidor `10.0.3.54`

**Error de Cámara:**
```
No se pudo encontrar una cámara funcional
```
**Solución:**
1. Conecta una cámara web USB
2. Cierra otras aplicaciones que usen la cámara
3. Presiona "REINTENTAR CÁMARA" en la interfaz

**Error de Dependencias:**
```
ModuleNotFoundError: No module named 'kivy'
```
**Solución:**
```bash
pip install -r requirements_pc.txt
```

## 🎯 Uso del Sistema

### Funcionamiento Normal
1. Abre el lector: `python ver.py`
2. Verifica estados: CÁMARA: OK, MySQL: CONECTADA
3. Apunta códigos QR hacia la cámara
4. El sistema detecta y procesa automáticamente
5. Ve confirmación en pantalla (verde=éxito, rojo=error)

### Estados del Sistema
- **Lector QR Activo**: Todo funcionando correctamente
- **Cámara No Disponible**: Problema con cámara web
- **Base de Datos Error**: Sin conexión a MySQL

### Controles
- **PAUSAR/REANUDAR**: Pausa detección temporal
- **REINTENTAR CÁMARA**: Reconecta cámara web
- **RECONECTAR MySQL**: Reintenta conexión BD
- **SALIR**: Cierra aplicación

## 📞 Soporte
Si persisten problemas, contacta al administrador del sistema con:
- Mensaje de error completo
- Versión de Python (`python --version`)
- Sistema operativo y versión