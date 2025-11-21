from flask import Blueprint, jsonify
from datetime import datetime, date, timedelta
from database import get_connection
from utils.datetime_utils import convert_to_time

horas_bp = Blueprint('horas', __name__)

@horas_bp.route('/horas_acumuladas', methods=['GET'])
def get_horas_acumuladas():
    """Obtener horas acumuladas de todos los usuarios"""
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # 1) Traer usuarios activos
            cursor.execute("""
                SELECT id, nombre, apellido, email 
                FROM usuarios_permitidos 
                WHERE activo = 1
            """)
            usuarios = cursor.fetchall()

            resultado = []

            for usuario in usuarios:
                # 2) Traer todos los registros ordenados por fecha y hora
                cursor.execute("""
                    SELECT id, fecha, hora, tipo 
                    FROM registros 
                    WHERE email = %s 
                    ORDER BY fecha, hora
                """, (usuario['email'],))
                registros = cursor.fetchall()
                
                # Inicializar variables para el cálculo
                horas_totales = 0
                dias_calendario = set()  # Para contar días únicos con asistencia
                entradas_sin_salida = []
                
                # 3) Procesar los registros para hacer pares entrada-salida
                for registro in registros:
                    # Añadir a días con asistencia
                    if isinstance(registro['fecha'], date):
                        fecha_str = registro['fecha'].isoformat()
                    else:
                        fecha_str = str(registro['fecha'])
                    
                    dias_calendario.add(fecha_str)
                    
                    # Procesar según el tipo de registro
                    if registro['tipo'] == 'Entrada':
                        # Guardar esta entrada para emparejarla después
                        entradas_sin_salida.append(registro)
                    
                    elif registro['tipo'] == 'Salida' and entradas_sin_salida:
                        # Tomar la entrada más reciente que no tenga salida
                        entrada = entradas_sin_salida.pop(0)
                        
                        # Convertir ambos registros a datetime.time para poder calcular la diferencia
                        entrada_time = convert_to_time(entrada['hora'])
                        salida_time = convert_to_time(registro['hora'])
                        
                        # Verificar que la entrada y salida sean del mismo día
                        entrada_fecha = entrada['fecha'].isoformat() if isinstance(entrada['fecha'], date) else str(entrada['fecha'])
                        salida_fecha = registro['fecha'].isoformat() if isinstance(registro['fecha'], date) else str(registro['fecha'])
                        
                        if entrada_fecha == salida_fecha:
                            # Calcular la diferencia de tiempo en horas
                            if salida_time > entrada_time:  # Mismo día
                                dt_entrada = datetime.combine(date.min, entrada_time)
                                dt_salida = datetime.combine(date.min, salida_time)
                                diff = dt_salida - dt_entrada
                                horas_totales += diff.total_seconds() / 3600
                
                # 4) Calcular estadísticas finales
                dias_asistidos = horas_totales / 8.0  # 8 horas = 1 día completo
                
                resultado.append({
                    "nombre": usuario['nombre'],
                    "apellido": usuario['apellido'],
                    "email": usuario['email'],
                    "dias_asistidos": round(dias_asistidos, 1),
                    "horas_totales": round(horas_totales, 1),
                    "dias_calendario": len(dias_calendario)
                })

        conn.close()
        return jsonify(resultado)

    except Exception as e:
        print(f"Error al obtener horas acumuladas: {e}")
        return jsonify({"error": str(e)}), 500

@horas_bp.route('/horas_detalle/<email>', methods=['GET'])
def get_horas_detalle(email):
    """Obtener detalle de horas por usuario (para debugging)"""
    try:
        conn = get_connection()
        
        with conn.cursor() as cursor:
            # Verificar que el usuario existe
            cursor.execute("SELECT nombre, apellido FROM usuarios_permitidos WHERE email = %s AND activo = 1", (email,))
            usuario = cursor.fetchone()
            
            if not usuario:
                return jsonify({"error": "Usuario no encontrado o inactivo"}), 404
            
            # Obtener todos los registros ordenados por fecha y hora
            cursor.execute("""
                SELECT fecha, hora, id
                FROM registros
                WHERE email = %s
                ORDER BY fecha, hora
            """, (email,))
            
            todos_registros = cursor.fetchall()
            
            # Procesar los registros para mostrar el detalle
            detalle_por_dia = {}
            
            for reg in todos_registros:
                fecha_str = str(reg['fecha'])
                
                # Convertir hora a formato estandarizado
                if isinstance(reg['hora'], str):
                    hora_str = reg['hora']
                elif isinstance(reg['hora'], timedelta):
                    # Convertir timedelta a string en formato HH:MM:SS
                    seconds = reg['hora'].total_seconds()
                    hours = int(seconds // 3600)
                    minutes = int((seconds % 3600) // 60)
                    secs = int(seconds % 60)
                    hora_str = f"{hours:02d}:{minutes:02d}:{secs:02d}"
                else:
                    try:
                        hora_str = reg['hora'].strftime('%H:%M:%S')
                    except:
                        hora_str = str(reg['hora'])
                
                # Agregar al diccionario de días
                if fecha_str not in detalle_por_dia:
                    detalle_por_dia[fecha_str] = []
                
                detalle_por_dia[fecha_str].append({
                    "id": reg['id'],
                    "hora": hora_str
                })
            
            # Calcular horas por día
            resumen_dias = []
            horas_totales = 0
            
            for fecha, registros in detalle_por_dia.items():
                # Ordenar registros por hora
                registros.sort(key=lambda x: x['hora'])
                
                # Manejar registros impares agregando uno ficticio al final
                reg_procesados = registros.copy()
                if len(reg_procesados) % 2 != 0 and len(reg_procesados) > 0:
                    ultimo_registro = reg_procesados[-1].copy()
                    ultimo_registro["hora"] = "23:59:59"
                    ultimo_registro["ficticio"] = True
                    reg_procesados.append(ultimo_registro)
                
                # Calcular pares entrada-salida
                pares = []
                horas_dia = 0
                
                for i in range(0, len(reg_procesados), 2):
                    if i + 1 < len(reg_procesados):  # Hay un par completo
                        entrada = reg_procesados[i]['hora']
                        salida = reg_procesados[i + 1]['hora']
                        es_ficticio = reg_procesados[i + 1].get('ficticio', False)
                        
                        try:
                            # Convertir a horas decimales
                            # Aseguramos que entrada y salida sean strings
                            if not isinstance(entrada, str):
                                # Convertir a string si no lo es
                                if isinstance(entrada, timedelta):
                                    seconds = entrada.total_seconds()
                                    hours = int(seconds // 3600)
                                    minutes = int((seconds % 3600) // 60)
                                    secs = int(seconds % 60)
                                    entrada = f"{hours:02d}:{minutes:02d}:{secs:02d}"
                                else:
                                    entrada = str(entrada)
                                    
                            if not isinstance(salida, str):
                                # Convertir a string si no lo es
                                if isinstance(salida, timedelta):
                                    seconds = salida.total_seconds()
                                    hours = int(seconds // 3600)
                                    minutes = int((seconds % 3600) // 60)
                                    secs = int(seconds % 60)
                                    salida = f"{hours:02d}:{minutes:02d}:{secs:02d}"
                                else:
                                    salida = str(salida)
                            
                            # Ahora que tenemos strings, convertir a datetime
                            entrada_dt = datetime.strptime(entrada, '%H:%M:%S')
                            salida_dt = datetime.strptime(salida, '%H:%M:%S')
                            
                            entrada_decimal = entrada_dt.hour + entrada_dt.minute/60 + entrada_dt.second/3600
                            salida_decimal = salida_dt.hour + salida_dt.minute/60 + salida_dt.second/3600
                            
                            if salida_decimal > entrada_decimal:
                                horas = salida_decimal - entrada_decimal
                                horas_dia += horas
                                
                                pares.append({
                                    "entrada": entrada,
                                    "salida": salida,
                                    "horas": round(horas, 2),
                                    "es_ficticio": es_ficticio
                                })
                        except Exception as e:
                            print(f"Error calculando horas para par: {str(e)}")
                
                # Agregar resumen del día
                resumen_dias.append({
                    "fecha": fecha,
                    "registros_totales": len(registros),
                    "pares_completos": len(pares),
                    "registros": registros,
                    "pares": pares,
                    "horas_dia": round(horas_dia, 2)
                })
                
                horas_totales += horas_dia
            
            # Definir horas por día completo
            HORAS_POR_DIA = 8
            dias_completos = horas_totales / HORAS_POR_DIA
            
            # Preparar resultado final
            resultado = {
                "nombre": usuario['nombre'],
                "apellido": usuario['apellido'],
                "email": email,
                "dias_calendario": len(detalle_por_dia),  # Días naturales con registros
                "dias_completos": round(dias_completos, 2),  # Días equivalentes basados en horas
                "horas_totales": round(horas_totales, 2),
                "detalle_dias": resumen_dias
            }
            
        conn.close()
        return jsonify(resultado)
    except Exception as e:
        print(f"Error al obtener detalle de horas: {str(e)}")
        return jsonify({"error": str(e)}), 500