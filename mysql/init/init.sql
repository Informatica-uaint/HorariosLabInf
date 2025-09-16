-- init.sql - Script de inicialización de la base de datos
-- Se ejecuta automáticamente cuando se crea el contenedor MySQL

-- Crear base de datos si no existe
CREATE DATABASE IF NOT EXISTS registro_qr CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Usar la base de datos
USE registro_qr;

-- Crear usuario de aplicación si no existe
CREATE USER IF NOT EXISTS 'app_user'@'%' IDENTIFIED BY 'app_password';
GRANT ALL PRIVILEGES ON registro_qr.* TO 'app_user'@'%';
FLUSH PRIVILEGES;

-- Ejemplo de tablas básicas (ajustar según sea necesario)
-- Tabla de usuarios estudiantes
CREATE TABLE IF NOT EXISTS usuarios_estudiantes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    TP VARCHAR(50) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabla de registros de estudiantes
CREATE TABLE IF NOT EXISTS EST_registros (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    dia VARCHAR(20),
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    tipo ENUM('Entrada', 'Salida') NOT NULL,
    auto_generado BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email_fecha (email, fecha),
    INDEX idx_fecha_hora (fecha, hora),
    INDEX idx_tipo (tipo)
);

-- Tabla de usuarios ayudantes (ejemplo)
CREATE TABLE IF NOT EXISTS usuarios_ayudantes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE,
    rol VARCHAR(50) DEFAULT 'ayudante',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabla de registros de ayudantes
CREATE TABLE IF NOT EXISTS registros (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    dia VARCHAR(20),
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    tipo ENUM('Entrada', 'Salida') NOT NULL,
    auto_generado BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email_fecha (email, fecha),
    INDEX idx_fecha_hora (fecha, hora),
    INDEX idx_tipo (tipo)
);

-- Insertar datos de ejemplo para desarrollo
INSERT IGNORE INTO usuarios_estudiantes (nombre, apellido, email, TP) VALUES
('Juan', 'Pérez', 'juan.perez@ejemplo.com', 'Ingeniería Informática'),
('María', 'González', 'maria.gonzalez@ejemplo.com', 'Ingeniería Civil'),
('Carlos', 'López', 'carlos.lopez@ejemplo.com', 'Ingeniería Informática');

-- Insertar ayudantes de ejemplo
INSERT IGNORE INTO usuarios_ayudantes (nombre, apellido, email) VALUES
('Ana', 'Martínez', 'ana.martinez@ayudante.com'),
('Pedro', 'Silva', 'pedro.silva@ayudante.com'),
('Laura', 'Torres', 'laura.torres@ayudante.com');

-- Insertar registros de ejemplo
INSERT IGNORE INTO EST_registros (fecha, hora, dia, nombre, apellido, email, tipo) VALUES
(CURDATE(), '09:00:00', 'Monday', 'Juan', 'Pérez', 'juan.perez@ejemplo.com', 'Entrada'),
(CURDATE(), '12:00:00', 'Monday', 'María', 'González', 'maria.gonzalez@ejemplo.com', 'Entrada'),
(CURDATE(), '15:00:00', 'Monday', 'Juan', 'Pérez', 'juan.perez@ejemplo.com', 'Salida');

-- Insertar registros de ayudantes de ejemplo
INSERT IGNORE INTO registros (fecha, hora, dia, nombre, apellido, email, tipo) VALUES
(CURDATE(), '08:00:00', 'Monday', 'Ana', 'Martínez', 'ana.martinez@ayudante.com', 'Entrada'),
(CURDATE(), '10:00:00', 'Monday', 'Pedro', 'Silva', 'pedro.silva@ayudante.com', 'Entrada'),
(CURDATE(), '13:00:00', 'Monday', 'Pedro', 'Silva', 'pedro.silva@ayudante.com', 'Salida');

-- Confirmar configuración
SELECT 'Base de datos inicializada correctamente' as mensaje;