from flask import Blueprint, jsonify, request
from datetime import datetime, time, timedelta, date
from database import get_connection
from utils.datetime_utils import get_current_datetime, convert_to_time, format_hora, get_week_dates
from config import Config

cumplimiento_bp = Blueprint('cumplimiento', __name__)

@cumplimiento_bp.route('/cumplimiento', methods=['GET'])
def get_cumplimiento():
    """Obtener estado de cumplimiento de todos los usuarios"""
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # Fecha y hora actual
            now = get_current_datetime()
            dia_actual = now.strftime('%A').lower()
            dia_actual_esp = Config.DIAS_TRADUCCION.get(dia_actual, dia_actual)
            hora_actual = now.strftime('%H:%M:%S')
            fecha_actual = now.strftime('%Y-%m-%d')

            print(f"[DEBUG] Iniciando cálculo de cumplimiento. Fecha: {fecha_actual}, Día: {dia_actual_esp}")

            # Traer usuarios activos
            cursor.execute("SELECT * FROM usuarios_permitidos WHERE activo = 1")
            usuarios = cursor.fetchall()

            resultado = []

            # Fecha de inicio de semana (lunes)
            start_of_week = now - timedelta(days=now.weekday())
            start_of_week_str = start_of_week.strftime('%Y-%m-%d')

            for user in usuarios:
                print(f"[DEBUG] Procesando usuario: {user['nombre']} {user['apellido']} ({user['email']})")
                
                # Traer sus horarios asignados
                cursor.execute(
                    "SELECT * FROM horarios_asignados WHERE usuario_id = %s",
                    (user['id'],)
                )
                horarios = cursor.fetchall()

                # Si no tiene horarios, "No Aplica"
                if not horarios:
                    resultado.append({
                        "nombre": user['nombre'],
                        "apellido": user['apellido'],
                        "email": user['email'],
                        "estado": "No Aplica",
                        "bloques": [],
                        "bloques_info": []
                    })
                    continue

                bloques = []
                bloques_info = []
                cumplidos = 0
                incompletos = 0
                ausentes = 0
                pendientes = 0

                # Un bloque por cada horario
                for h in horarios:
                    print(f"[DEBUG] Procesando bloque: {h['dia']} {h['hora_entrada']}-{h['hora_salida']}")
                    
                    bloque_label = f"{h['dia']} {h['hora_entrada']}-{h['hora_salida']}"
                    bloques.append(bloque_label)

                    # Default
                    bloque_estado = "Ausente"

                    # Convertir horas a datetime.time
                    hora_entrada_dt = convert_to_time(h['hora_entrada'])
                    hora_salida_dt = convert_to_time(h['hora_salida'])

                    # Obtener registros de ese día o semana
                    dia_horario = h['dia'].lower()
                    dia_en_espanol = Config.DIAS_TRADUCCION.get(dia_horario, dia_horario)
                    
                    print(f"[DEBUG] Día actual: {dia_actual_esp}, Día del bloque: {dia_horario} / {dia_en_espanol}")

                    if dia_en_espanol == dia_actual_esp:
                        cursor.execute("""
                            SELECT * FROM registros
                            WHERE email = %s AND fecha = %s
                            ORDER BY hora
                        """, (user['email'], fecha_actual))
                    else:
                        cursor.execute("""
                            SELECT * FROM registros
                            WHERE email = %s
                              AND (LOWER(dia) = %s OR LOWER(dia) = %s)
                              AND fecha BETWEEN %s AND %s
                            ORDER BY fecha DESC, hora
                        """, (user['email'], dia_en_espanol, dia_horario, start_of_week_str, fecha_actual))

                    registros_del_dia = cursor.fetchall()
                    print(f"[DEBUG] Registros encontrados para el día: {len(registros_del_dia)}")

                    # Revisar registros de entrada y salida para determinar estado del bloque
                    cumplio_bloque = False
                    incompleto_bloque = False
                    
                    # Separar registros por tipo
                    entradas = [r for r in registros_del_dia if r['tipo'] == 'Entrada']
                    salidas = [r for r in registros_del_dia if r['tipo'] == 'Salida']
                    
                    print(f"[DEBUG] Entradas: {len(entradas)}, Salidas: {len(salidas)}")
                    
                    # Verificar si hay al menos una entrada y una salida
                    if entradas and salidas:
                        for entrada in entradas:
                            t_entrada = convert_to_time(entrada['hora'])
                            
                            print(f"[DEBUG] Procesando entrada id:{entrada['id']} hora:{t_entrada}")
                            
                            for salida in salidas:
                                # Solo considerar salidas posteriores a esta entrada
                                if salida['id'] > entrada['id']:
                                    t_salida = convert_to_time(salida['hora'])
                                    
                                    print(f"[DEBUG] Comparando con salida id:{salida['id']} hora:{t_salida}")
                                    
                                    # Verificar si cumplió el bloque completo
                                    if (t_entrada <= hora_entrada_dt and t_salida >= hora_salida_dt):
                                        cumplio_bloque = True
                                        print(f"[DEBUG] CUMPLIDO! Entrada a tiempo/antes y salida a tiempo/después")
                                        break
                                    elif (t_entrada > hora_entrada_dt and t_entrada < hora_salida_dt and t_salida >= hora_salida_dt):
                                        incompleto_bloque = True
                                        print(f"[DEBUG] INCOMPLETO - Entrada tarde, salida a tiempo/después")
                                    elif (t_entrada <= hora_entrada_dt and t_salida < hora_salida_dt):
                                        incompleto_bloque = True
                                        print(f"[DEBUG] INCOMPLETO - Entrada a tiempo/antes, salida temprana")
                                    elif (t_entrada < hora_salida_dt and t_salida > hora_entrada_dt):
                                        incompleto_bloque = True
                                        print(f"[DEBUG] INCOMPLETO - Presencia parcial en el bloque")
                            
                            if cumplio_bloque:
                                break

                    # Determinar estado según día actual o no
                    if dia_en_espanol == dia_actual_esp:
                        now_t = datetime.strptime(hora_actual, "%H:%M:%S").time()
                        
                        if cumplio_bloque:
                            bloque_estado = "Cumplido"
                            cumplidos += 1
                        elif incompleto_bloque:
                            bloque_estado = "Incompleto"
                            incompletos += 1
                        elif now_t < hora_entrada_dt:
                            bloque_estado = "Pendiente"
                            pendientes += 1
                        elif now_t >= hora_entrada_dt and now_t < hora_salida_dt:
                            bloque_estado = "Atrasado"
                            incompletos += 1
                        else:
                            bloque_estado = "Ausente"
                            ausentes += 1
                    else:
                        # Para días anteriores de la semana
                        if cumplio_bloque:
                            bloque_estado = "Cumplido"
                            cumplidos += 1
                        elif incompleto_bloque:
                            bloque_estado = "Incompleto"
                            incompletos += 1
                        else:
                            bloque_estado = "Ausente"
                            ausentes += 1

                    print(f"[DEBUG] Estado bloque: {bloque_estado} (Cumplido: {cumplio_bloque}, Incompleto: {incompleto_bloque})")
                    
                    bloques_info.append({
                        "bloque": bloque_label,
                        "estado": bloque_estado
                    })

                # Estado general del usuario para la semana
                print(f"[DEBUG] Usuario {user['email']} - Cumplidos: {cumplidos}, Incompletos: {incompletos}, Ausentes: {ausentes}, Pendientes: {pendientes}")
                
                if len(horarios) == 0:
                    estado_usuario = "No Aplica"
                elif pendientes > 0 and ausentes == 0 and incompletos == 0:
                    estado_usuario = "Pendiente"
                elif cumplidos == len(horarios):
                    estado_usuario = "Cumple"
                elif ausentes == len(horarios):
                    estado_usuario = "Ausente"
                elif incompletos > 0 or (cumplidos > 0 and ausentes > 0):
                    estado_usuario = "Incompleto"
                else:
                    estado_usuario = "No Cumple"
                
                print(f"[DEBUG] Estado final usuario: {estado_usuario}")

                resultado.append({
                    "nombre": user['nombre'],
                    "apellido": user['apellido'],
                    "email": user['email'],
                    "estado": estado_usuario,
                    "bloques": bloques,
                    "bloques_info": bloques_info
                })

        conn.close()
        return jsonify(resultado)

    except Exception as e:
        print(f"Error en cumplimiento: {e}")
        return jsonify({"error": str(e)}), 500

@cumplimiento_bp.route('/diagnostico_cumplimiento/<email>', methods=['GET'])
def diagnostico_cumplimiento(email):
    """Obtener diagnóstico detallado de cumplimiento para un usuario específico"""
    try:
        conn = get_connection()
        resultado = {}
        
        with conn.cursor() as cursor:
            # Obtener información del usuario
            cursor.execute("SELECT * FROM usuarios_permitidos WHERE email = %s", (email,))
            usuario = cursor.fetchone()
            
            if not usuario:
                return jsonify({"error": "Usuario no encontrado"}), 404
            
            resultado["usuario"] = {
                "id": usuario["id"],
                "nombre": usuario["nombre"],
                "apellido": usuario["apellido"],
                "email": usuario["email"]
            }
            
            # Obtener horarios asignados
            cursor.execute("SELECT * FROM horarios_asignados WHERE usuario_id = %s", (usuario["id"],))
            horarios = cursor.fetchall()
            
            # Formato para los horarios
            resultado["horarios"] = []
            for h in horarios:
                hora_entrada = format_hora(h["hora_entrada"])
                hora_salida = format_hora(h["hora_salida"])
                
                # Incluir traducción del día si está en inglés
                dia_original = h["dia"]
                dia_lower = dia_original.lower()
                dia_traducido = Config.DIAS_TRADUCCION.get(dia_lower, dia_lower)
                
                resultado["horarios"].append({
                    "dia": dia_original,
                    "dia_traducido": dia_traducido,
                    "hora_entrada": hora_entrada,
                    "hora_salida": hora_salida
                })
            
            # Fecha y hora actual
            now = get_current_datetime()
            dia_actual = now.strftime('%A').lower()
            dia_actual_esp = Config.DIAS_TRADUCCION.get(dia_actual, dia_actual)
            fecha_actual = now.strftime('%Y-%m-%d')
            hora_actual = now.strftime('%H:%M:%S')
            
            resultado["fecha_actual"] = fecha_actual
            resultado["hora_actual"] = hora_actual
            resultado["dia_actual"] = dia_actual
            resultado["dia_actual_esp"] = dia_actual_esp
            
            # Fecha de inicio de semana
            start_of_week = now - timedelta(days=now.weekday())
            start_of_week_str = start_of_week.strftime('%Y-%m-%d')
            resultado["inicio_semana"] = start_of_week_str
            
            # Registros de la semana
            cursor.execute("""
                SELECT * FROM registros
                WHERE email = %s AND fecha BETWEEN %s AND %s
                ORDER BY fecha, hora
            """, (email, start_of_week_str, fecha_actual))
            
            registros = cursor.fetchall()
            
            # Formato para registros
            resultado["registros"] = []
            for r in registros:
                resultado["registros"].append({
                    "id": r["id"],
                    "fecha": str(r["fecha"]),
                    "dia": r["dia"],
                    "hora": format_hora(r["hora"]),
                    "tipo": r["tipo"]
                })
            
            # Análisis de cumplimiento de cada bloque
            resultado["analisis_bloques"] = []
            
            for h in horarios:
                bloque_info = {
                    "dia": h["dia"],
                    "hora_entrada": format_hora(h["hora_entrada"]),
                    "hora_salida": format_hora(h["hora_salida"]),
                }
                
                # Convertir horas a datetime.time para comparación
                hora_entrada_dt = convert_to_time(h["hora_entrada"])
                hora_salida_dt = convert_to_time(h["hora_salida"])
                
                # Filtrar registros para este día
                dia_horario = h["dia"].lower()
                dia_en_espanol = Config.DIAS_TRADUCCION.get(dia_horario, dia_horario)
                
                # Registros que coinciden con este día
                registros_del_dia = [
                    r for r in registros 
                    if r["dia"].lower() == dia_horario or r["dia"].lower() == dia_en_espanol
                ]
                
                bloque_info["registros_encontrados"] = len(registros_del_dia)
                
                # Separar por tipo
                entradas = [r for r in registros_del_dia if r['tipo'] == 'Entrada']
                salidas = [r for r in registros_del_dia if r['tipo'] == 'Salida']
                
                bloque_info["entradas"] = len(entradas)
                bloque_info["salidas"] = len(salidas)
                
                # Analizar cumplimiento
                cumplio_bloque = False
                incompleto_bloque = False
                razon = "Sin registros suficientes"
                
                if entradas and salidas:
                    for entrada in entradas:
                        t_entrada = convert_to_time(entrada["hora"])
                        
                        for salida in salidas:
                            if salida["id"] > entrada["id"]:
                                t_salida = convert_to_time(salida["hora"])
                                
                                # Verificar cumplimiento según criterios
                                if t_entrada <= hora_entrada_dt and t_salida >= hora_salida_dt:
                                    cumplio_bloque = True
                                    razon = "Entrada a tiempo/antes y salida a tiempo/después"
                                    break
                                elif t_entrada > hora_entrada_dt and t_entrada < hora_salida_dt and t_salida >= hora_salida_dt:
                                    incompleto_bloque = True
                                    razon = "Entrada tarde y salida a tiempo/después"
                                elif t_entrada <= hora_entrada_dt and t_salida < hora_salida_dt:
                                    incompleto_bloque = True
                                    razon = "Entrada a tiempo/antes y salida temprana"
                                elif t_entrada < hora_salida_dt and t_salida > hora_entrada_dt:
                                    incompleto_bloque = True
                                    razon = "Presencia parcial en el bloque"
                        
                        if cumplio_bloque:
                            break
                
                # Determinar estado
                now_t = convert_to_time(hora_actual)
                
                if dia_en_espanol == dia_actual_esp:
                    if cumplio_bloque:
                        estado = "Cumplido"
                    elif incompleto_bloque:
                        estado = "Incompleto"
                    elif now_t < hora_entrada_dt:
                        estado = "Pendiente"
                        razon = "El bloque aún no ha comenzado"
                    elif now_t >= hora_entrada_dt and now_t < hora_salida_dt:
                        estado = "Atrasado"
                        razon = "El bloque está en curso pero no hay registro de entrada"
                    else:
                        estado = "Ausente"
                        razon = "El bloque ya pasó y no hubo asistencia completa"
                else:
                    if cumplio_bloque:
                        estado = "Cumplido"
                    elif incompleto_bloque:
                        estado = "Incompleto"
                    else:
                        estado = "Ausente"
                        razon = "No hay registros válidos para este bloque"
                
                bloque_info["estado"] = estado
                bloque_info["razon"] = razon
                bloque_info["cumplio"] = cumplio_bloque
                bloque_info["incompleto"] = incompleto_bloque
                
                resultado["analisis_bloques"].append(bloque_info)
        
        conn.close()
        return jsonify(resultado)
    
    except Exception as e:
        print(f"Error en diagnóstico cumplimiento: {e}")
        return jsonify({"error": str(e)}), 500

@cumplimiento_bp.route('/reiniciar_cumplimiento', methods=['POST'])
def reiniciar_cumplimiento():
    """Reiniciar cumplimiento semanal y guardar historial"""
    try:
        conn = get_connection()
        
        # Fecha actual
        now = get_current_datetime()
        fecha_actual = now.strftime('%Y-%m-%d')
        
        # 1. Crear tabla de historial si no existe
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historial_cumplimiento (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    usuario_id INT,
                    email VARCHAR(255),
                    nombre VARCHAR(100),
                    apellido VARCHAR(100),
                    semana_inicio DATE,
                    semana_fin DATE,
                    estado VARCHAR(50),
                    cumplidos INT,
                    incompletos INT,
                    ausentes INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        
        # 2. Obtener cumplimiento actual para guardar en historial
        with conn.cursor() as cursor:
            # Fecha de inicio de semana (lunes) y fin (domingo)
            start_of_week, end_of_week = get_week_dates()
            inicio_semana_str = start_of_week.strftime('%Y-%m-%d')
            fin_semana_str = end_of_week.strftime('%Y-%m-%d')
            
            # Obtener usuarios activos y sus horarios
            cursor.execute("SELECT * FROM usuarios_permitidos WHERE activo = 1")
            usuarios = cursor.fetchall()
            
            historial_insertado = 0
            
            for user in usuarios:
                # Calcular cumplimiento actual para este usuario
                cursor.execute(
                    "SELECT * FROM horarios_asignados WHERE usuario_id = %s",
                    (user['id'],)
                )
                horarios = cursor.fetchall()
                
                if not horarios:
                    continue
                
                # Obtener los registros de esta semana
                cursor.execute("""
                    SELECT * FROM registros 
                    WHERE email = %s AND fecha BETWEEN %s AND %s
                    ORDER BY fecha, hora
                """, (user['email'], inicio_semana_str, fecha_actual))
                
                registros_semana = cursor.fetchall()
                
                # Contar estados
                cumplidos = 0
                incompletos = 0
                ausentes = 0
                
                # Procesamiento simplificado para conteo
                for h in horarios:
                    dia_semana = h['dia'].lower()
                    
                    # Verificar si hay registros para este día y horario
                    cumplio_bloque = False
                    incompleto_bloque = False
                    
                    # Filtrar registros por día de la semana
                    registros_dia = [r for r in registros_semana if r['dia'].lower() == dia_semana]
                    
                    # Obtener horas de entrada y salida para este bloque
                    hora_entrada_dt = convert_to_time(h['hora_entrada'])
                    hora_salida_dt = convert_to_time(h['hora_salida'])
                    
                    # Verificar cumplimiento simplificado para historial
                    entradas = [r for r in registros_dia if r['tipo'] == 'Entrada']
                    salidas = [r for r in registros_dia if r['tipo'] == 'Salida']
                    
                    if entradas and salidas:
                        for entrada in entradas:
                            t_entrada = convert_to_time(entrada['hora'])
                            
                            for salida in salidas:
                                if salida['id'] > entrada['id']:
                                    t_salida = convert_to_time(salida['hora'])
                                    
                                    # Verificar cumplimiento
                                    if t_entrada <= hora_entrada_dt and t_salida >= hora_salida_dt:
                                        cumplio_bloque = True
                                        break
                                    elif ((t_entrada > hora_entrada_dt and t_entrada < hora_salida_dt and t_salida >= hora_salida_dt) or
                                          (t_entrada <= hora_entrada_dt and t_salida < hora_salida_dt) or
                                          (t_entrada < hora_salida_dt and t_salida > hora_entrada_dt)):
                                        incompleto_bloque = True
                            
                            if cumplio_bloque:
                                break
                    
                    # Incrementar contadores
                    if cumplio_bloque:
                        cumplidos += 1
                    elif incompleto_bloque:
                        incompletos += 1
                    else:
                        ausentes += 1
                
                # Determinar estado general para el historial
                if len(horarios) == 0:
                    estado = "No Aplica"
                elif cumplidos == len(horarios):
                    estado = "Cumple"
                elif ausentes == len(horarios):
                    estado = "Ausente"
                elif incompletos > 0 or (cumplidos > 0 and ausentes > 0):
                    estado = "Incompleto"
                else:
                    estado = "No Cumple"
                
                # Guardar en historial
                cursor.execute("""
                    INSERT INTO historial_cumplimiento
                    (usuario_id, email, nombre, apellido, semana_inicio, semana_fin, 
                     estado, cumplidos, incompletos, ausentes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user['id'],
                    user['email'],
                    user['nombre'],
                    user['apellido'],
                    inicio_semana_str,
                    fin_semana_str,
                    estado,
                    cumplidos,
                    incompletos,
                    ausentes
                ))
                
                historial_insertado += 1
            
            conn.commit()
        
        # 3. Establecer marca para indicar nuevo inicio de semana
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sistema_config (
                    clave VARCHAR(50) PRIMARY KEY,
                    valor TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # Actualizar la fecha de último reinicio
            cursor.execute("""
                INSERT INTO sistema_config (clave, valor) 
                VALUES ('ultimo_reinicio_cumplimiento', %s)
                ON DUPLICATE KEY UPDATE valor = %s
            """, (fecha_actual, fecha_actual))
            
            conn.commit()
        
        conn.close()
        
        return jsonify({
            "mensaje": "Reinicio de cumplimiento semanal completado",
            "fecha_reinicio": fecha_actual,
            "registros_historial": historial_insertado
        })
        
    except Exception as e:
        print(f"Error en reinicio de cumplimiento: {e}")
        return jsonify({"error": str(e)}), 500

@cumplimiento_bp.route('/historial_cumplimiento/<email>', methods=['GET'])
def get_historial_cumplimiento(email):
    """Obtener historial de cumplimiento de un usuario específico"""
    try:
        conn = get_connection()
        
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM historial_cumplimiento
                WHERE email = %s
                ORDER BY semana_inicio DESC
            """, (email,))
            
            historial = cursor.fetchall()
            
            # Formatear fechas
            for item in historial:
                for key, value in item.items():
                    if isinstance(value, (datetime, date)):
                        item[key] = value.isoformat()
        
        conn.close()
        return jsonify(historial)
        
    except Exception as e:
        print(f"Error al obtener historial de cumplimiento: {e}")
        return jsonify({"error": str(e)}), 500