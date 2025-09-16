from apscheduler.schedulers.background import BackgroundScheduler
import requests
from config import Config

def ejecutar_cierre_diario():
    """Ejecuta el cierre diario de registros sin salida"""
    try:
        # URL del servidor de producción
        server_url = Config.SERVER_URL
        
        # Llamar al endpoint de procesar salidas pendientes
        response = requests.post(
            f'{server_url}/api/procesar_salidas_pendientes',
            json={},
            verify=True  # En producción, verificar los certificados
        )
        
        if response.status_code == 200:
            print(f"Cierre diario ejecutado con éxito: {response.json()}")
        else:
            print(f"Error en cierre diario: {response.text}")
    
    except Exception as e:
        print(f"Error al ejecutar cierre diario: {str(e)}")

def ejecutar_reinicio_semanal():
    """Ejecuta el reinicio semanal de cumplimiento"""
    try:
        # URL del servidor de producción
        server_url = Config.SERVER_URL
        
        # Llamar al endpoint de reinicio
        response = requests.post(
            f'{server_url}/reiniciar_cumplimiento',
            json={},
            verify=True
        )
        
        if response.status_code == 200:
            print(f"Reinicio semanal de cumplimiento ejecutado: {response.json()}")
        else:
            print(f"Error en reinicio semanal: {response.text}")
    
    except Exception as e:
        print(f"Error al ejecutar reinicio semanal: {str(e)}")

def configurar_tarea_cierre_diario():
    """
    Configura una tarea programada que se ejecutará diariamente a las 23:59
    para cerrar los registros sin salida del día.
    """
    # Crear el scheduler
    scheduler = BackgroundScheduler()
    
    # Programar la tarea para ejecutarse TODOS los días a las 23:59 (11:59 PM)
    scheduler.add_job(ejecutar_cierre_diario, 'cron', hour=23, minute=59)
    
    # Iniciar el scheduler
    scheduler.start()
    
    print("Tarea de cierre diario programada para ejecutarse a las 23:59 (11:59 PM)")

def configurar_reinicio_semanal():
    """
    Configura una tarea programada para reiniciar los estados de cumplimiento
    cada semana (domingos a las 23:55).
    """
    # Crear el scheduler
    scheduler = BackgroundScheduler()
    
    # Programar la tarea para ejecutarse los domingos a las 23:55
    scheduler.add_job(ejecutar_reinicio_semanal, 'cron', day_of_week='sun', hour=23, minute=55)
    
    # Iniciar el scheduler
    scheduler.start()
    
    print("Tarea de reinicio semanal programada para los domingos a las 23:55")