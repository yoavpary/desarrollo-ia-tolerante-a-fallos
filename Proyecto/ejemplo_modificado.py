import requests
from prefect import task, flow, get_run_logger

@task(retries=3, retry_delay_seconds=2, name="Extraer Todas las Tareas")
def obtener_todos():
    """Descarga la lista completa de tareas desde la API."""
    logger = get_run_logger()
    url = "https://jsonplaceholder.cypress.io/todos"
    
    logger.info("Solicitando la lista de tareas a JSONPlaceholder...")
    respuesta = requests.get(url, timeout=10)
    respuesta.raise_for_status()
    return respuesta.json()

@task(name="Filtrar Pendientes")
def filtrar_tareas_pendientes(lista_tareas):
    """Filtra la lista y conserva únicamente las tareas no completadas (completed == False)."""
    logger = get_run_logger()
    
    # Filtramos las tareas donde 'completed' es False
    pendientes = [t for t in lista_tareas if not t.get("completed")]
    
    logger.info(f"Total de tareas recibidas: {len(lista_tareas)}")
    logger.info(f"Tareas pendientes encontradas: {len(pendientes)}")
    return pendientes

@task(name="Mostrar Reporte de Pendientes")
def generar_reporte_pendientes(pendientes):
    """Muestra en pantalla un resumen formateado de las tareas pendientes."""
    print("\n" + "="*60)
    print("         REPORTE DE TAREAS PENDIENTES (INCOMPLETAS)         ")
    print("="*60)
    
    # Tomamos una muestra de las primeras 15 para no saturar la consola
    muestra = pendientes[:15]
    
    for tarea in muestra:
        print(f"📌 [ID: {tarea['id']:>3}] Usuario #{tarea['userId']} -> {tarea['title']}")
    
    print("-" * 60)
    print(f"Total de pendientes mostrados: {len(muestra)} de {len(pendientes)} totales.")
    print("="*60 + "\n")

@flow(name="Pipeline Filtro Tareas Pendientes")
def flujo_control_pendientes():
    # 1. Obtener todos los elementos
    todas_las_tareas = obtener_todos()
    # 2. Filtrar solo los inconclusos (completed == False)
    solo_pendientes = filtrar_tareas_pendientes(todas_las_tareas)
    # 3. Presentar reporte
    generar_reporte_pendientes(solo_pendientes)

if __name__ == "__main__":
    flujo_control_pendientes()