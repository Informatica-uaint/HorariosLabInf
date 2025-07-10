def format_registros(registros):
    """Formatea la lista de registros para la respuesta"""
    formatted = []
    
    for reg in registros:
        try:
            # Manejar fecha
            if isinstance(reg['fecha'], str):
                fecha_str = reg['fecha']
            else:
                fecha_str = reg['fecha'].strftime('%Y-%m-%d')
            
            # Manejar hora - SOLUCIÓN CORREGIDA
            hora_registro = reg['horaRegistro']
            
            if isinstance(hora_registro, str):
                hora_str = hora_registro
            elif isinstance(hora_registro, timedelta):
                # Convertir timedelta a string de hora
                total_seconds = int(hora_registro.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                hora_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            elif hasattr(hora_registro, 'hour'):
                # Si es time object
                hora_str = hora_registro.strftime('%H:%M:%S')
            else:
                # Default para casos inesperados
                hora_str = "00:00:00"
            
            # Crear timestamp simplemente concatenando strings
            timestamp_str = f"{fecha_str} {hora_str}"
            
            # Convertir a datetime para generar ISO format
            try:
                fecha_hora = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                iso_timestamp = fecha_hora.isoformat()
            except ValueError:
                # Si falla el parsing, usar la fecha actual como fallback
                iso_timestamp = datetime.now().isoformat()
            
            formatted.append({
                'id': str(reg['id']),
                'estudianteId': str(reg['estudianteId']) if reg['estudianteId'] else '',
                'nombreEstudiante': reg['nombreEstudiante'] or '',
                'apellidoEstudiante': reg['apellidoEstudiante'] or '',
                'rutEstudiante': reg['rutEstudiante'] or '',
                'tipoRegistro': reg['tipoRegistro'] or '',
                'horaRegistro': iso_timestamp,
                'fecha': fecha_str
            })
            
        except Exception as e:
            # Log del error y continuar con el siguiente registro
            logging.error(f"Error formatting registro {reg.get('id', 'unknown')}: {e}")
            
            # Crear entrada con datos básicos si falla el formateo
            now = datetime.now()
            formatted.append({
                'id': str(reg.get('id', '')),
                'estudianteId': str(reg.get('estudianteId', '')),
                'nombreEstudiante': reg.get('nombreEstudiante', '') or '',
                'apellidoEstudiante': reg.get('apellidoEstudiante', '') or '',
                'rutEstudiante': reg.get('rutEstudiante', '') or '',
                'tipoRegistro': reg.get('tipoRegistro', '') or '',
                'horaRegistro': now.isoformat(),
                'fecha': now.date().isoformat()
            })
    
    return formatted
