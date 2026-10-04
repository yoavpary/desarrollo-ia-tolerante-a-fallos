import requests
from prefect import task, flow

@task(retries=3, retry_delay_seconds=2)
def obtener_tarea_simulada():
    """Pide un elemento de prueba a la API."""
    url = "https://jsonplaceholder.cypress.io/todos/1"
    respuesta = requests.get(url)
    return respuesta.json()

@task
def mostrar_resultado(datos):
    """Muestra en pantalla la información recuperada."""
    print("\n" + "="*40)
    print(f" ID de la tarea: {datos['id']}")
    print(f" Título: {datos['title']}")
    print(f" ¿Completada?: {datos['completed']}")
    print("="*40 + "\n")

@flow(name="Tutorial Base Prefect")
def flujo_principal():
    """Coordina la ejecución ordenada de las tareas."""
    datos = obtener_tarea_simulada()
    mostrar_resultado(datos)

if __name__ == "__main__":
    flujo_principal()