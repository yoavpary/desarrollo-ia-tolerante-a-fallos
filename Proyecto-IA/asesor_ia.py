import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from google import genai

GOOGLE_API_KEY = "TU-API-KEY" # Reemplaza con tu API Key real
try:
    client = genai.Client(api_key=GOOGLE_API_KEY)
except Exception:
    client = None

CHECKPOINT_FILE = "historial_asesor.json"
executor_disco = ThreadPoolExecutor(max_workers=2)

class FinanzasCheckpointManager:

    @staticmethod
    def load():
        if os.path.exists(CHECKPOINT_FILE):
            try:
                with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Error Checkpoint] No se pudo leer el archivo: {e}")
        return {"total_desperdiciado": 0.0, "compras_previas": []}

    @staticmethod
    def _save_sync(total: float, compras: list):
        temp_file = f"{CHECKPOINT_FILE}.tmp"
        data = {"total_desperdiciado": total, "compras_previas": compras}
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, CHECKPOINT_FILE)

    @classmethod
    def save_async_thread(cls, total: float, compras: list):
        executor_disco.submit(cls._save_sync, total, compras)

    @staticmethod
    def reset():
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)
        return 0.0, "Historial reiniciado. Billetera en ceros."

def evaluar_compra_ia(prod, precio, excusa):
    """Prepara el prompt y consulta a Gemini en segundo plano"""
    estado = FinanzasCheckpointManager.load()
    total_acumulado = estado["total_desperdiciado"] + precio
    historial = estado["compras_previas"]

    previas_texto = ", ".join([f"{c['producto']} (${c['precio']})" for c in historial[-3:]])
    contexto_previo = f"Compras previas: [{previas_texto}]" if previas_texto else "Primera compra de la sesión."

    prompt = f"""
    Eres un asesor financiero con humor ácido y sarcástico. Odias las compras impulsivas.
    Detalles de la compra:
    - Producto: {prod}
    - Precio: ${precio:.2f}
    - Justificación: "{excusa}"
    - Gasto total acumulado: ${total_acumulado:.2f}
    - Contexto: {contexto_previo}
    
    Instrucciones:
    1. Desacredita su justificación en 2 o 3 oraciones usando sarcasmo.
    2. Da una equivalencia cómica de cosas útiles que podría comprar.
    """

    veredicto = "Error de conexión con la IA."
    if client:
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash", 
                contents=prompt
            )
            veredicto = response.text.strip()
        except Exception as e:
            veredicto = f"No se pudo conectar a la IA: {e}"
    else:
        veredicto = "Simulación: ¡Estás gastando dinero innecesariamente en caprichos!"

    historial.append({"producto": prod, "precio": precio, "justificacion": excusa})
    FinanzasCheckpointManager.save_async_thread(total=total_acumulado, compras=historial)

    return veredicto, total_acumulado