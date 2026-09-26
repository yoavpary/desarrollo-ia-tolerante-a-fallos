import asyncio
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
import gradio as gr
from google import genai

# --- 1. CONFIGURACIÓN DEL MODELO ---
GOOGLE_API_KEY = "TU-API-KEY-AQUI"
client = genai.Client(api_key=GOOGLE_API_KEY)
CHECKPOINT_FILE = "historial_asesor.json"

# Pool de hilos dedicado exclusivamente a operaciones I/O de disco
executor_disco = ThreadPoolExecutor(max_workers=2)


# --- 2. GESTOR DE CHECKPOINTING (Con Hilos en Segundo Plano) ---
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
        """Guardado atómico ejecutado dentro de un HILO secundario."""
        print(
            f"[Thread {threading.current_thread().name}] Guardando checkpoint en disco..."
        )
        temp_file = f"{CHECKPOINT_FILE}.tmp"
        data = {"total_desperdiciado": total, "compras_previas": compras}
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, CHECKPOINT_FILE)
        print(f"[Thread {threading.current_thread().name}] Checkpoint guardado.")

    @classmethod
    def save_async_thread(cls, total: float, compras: list):
        """Delega la escritura en disco al Pool de Hilos para no bloquear la respuesta."""
        executor_disco.submit(cls._save_sync, total, compras)

    @staticmethod
    def reset():
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)
        return 0.0, "Historial reiniciado. Billetera en ceros."


# --- 3. LÓGICA DE INFERENCIA ASÍNCRONA (asyncio) ---
async def juzgar_compra(producto: str, precio: float, justificacion: str):
    if not producto or precio <= 0:
        return (
            "Ingresa un producto válido y un precio mayor a 0.",
            "$0.00",
            "Entrada inválida.",
        )

    estado = FinanzasCheckpointManager.load()
    total_acumulado = estado["total_desperdiciado"] + precio
    historial = estado["compras_previas"]

    previas_texto = ", ".join(
        [f"{c['producto']} (${c['precio']})" for c in historial[-3:]]
    )
    contexto_previo = (
        f"Compras innecesarias previas en la sesión: [{previas_texto}]"
        if previas_texto
        else "Primera compra registrada."
    )

    prompt = f"""
    Eres un asesor financiero con humor ácido y sarcástico. Odias las compras impulsivas.
    
    Detalles de la compra que el usuario planea:
    - Producto: {producto}
    - Precio: ${precio:.2f}
    - Justificación dada: "{justificacion}"
    - Gasto total acumulado que lleva: ${total_acumulado:.2f}
    - Contexto de sesiones previas: {contexto_previo}
    
    Instrucciones:
    1. Desacredita su justificación en 2 o 3 oraciones usando sarcasmo e ingenio.
    2. Da una equivalencia cómica de cosas más útiles que podría comprar con ese monto.
    3. Si ya tiene gastos acumulados en el historial, échale en cara su falta of control financiero.
    """

    try:
        # LLAMADA ASÍNCRONA A LA API DE GEMINI (No bloquea el bucle de eventos)
        response = await client.aio.models.generate_content(
            model="gemini-3.6-flash", contents=prompt
        )
        veredicto = response.text.strip()

        # Actualizar lista
        historial.append(
            {
                "producto": producto,
                "precio": precio,
                "justificacion": justificacion,
            }
        )

        # GUARDADO ASÍNCRONO EN HILO SECUNDARIO (No congela el retorno)
        FinanzasCheckpointManager.save_async_thread(
            total=total_acumulado, compras=historial
        )

        marcador = f"Deuda Moral Acumulada: ${total_acumulado:,.2f}"
        status = f"Checkpoint en proceso (Hilo): {len(historial)} decisiones registradas."
        return veredicto, marcador, status

    except Exception as e:
        return (
            f"Error al conectar con la API: {e}",
            f"${estado['total_desperdiciado']:,.2f}",
            "Fallo de conexión.",
        )


# --- 4. INTERFAZ GRÁFICA (Gradio) ---
estado_inicial = FinanzasCheckpointManager.load()
total_inicial = estado_inicial["total_desperdiciado"]

with gr.Blocks(title="Asesor Financiero Tóxico") as demo:
    gr.Markdown("# 💸 El Hater Financiero (Asesor Anti-Gastos - Asíncrono)")
    gr.Markdown(
        "Registra lo que pretendes comprar. Evaluado concurrentemente con `asyncio` y `threading`."
    )

    marcador_deuda = gr.Label(
        value=f"Deuda Moral Acumulada: ${total_inicial:,.2f}"
    )

    with gr.Row():
        with gr.Column():
            in_producto = gr.Textbox(
                label="¿Qué quieres comprar?", placeholder="Ej: Teclado mecánico"
            )
            in_precio = gr.Number(label="¿Cuánto cuesta? ($)", value=0.0)
            in_excusa = gr.Textbox(
                label="Tu justificación",
                placeholder="Ej: Es para programar más rápido",
            )
            btn_juzgar = gr.Button(
                "Evaluar mi pésima decisión", variant="primary"
            )

        with gr.Column():
            out_veredicto = gr.Textbox(label="Veredicto del Asesor", lines=6)
            out_status = gr.Textbox(
                label="Estado del Checkpoint", interactive=False
            )
            btn_reset = gr.Button(
                "Declararse en Bancarrota (Resetear)", variant="stop"
            )

    btn_juzgar.click(
        fn=juzgar_compra,
        inputs=[in_producto, in_precio, in_excusa],
        outputs=[out_veredicto, marcador_deuda, out_status],
    )

    btn_reset.click(
        fn=lambda: (
            FinanzasCheckpointManager.reset()[1],
            "Deuda Moral Acumulada: $0.00",
            "Checkpoint borrado.",
        ),
        inputs=None,
        outputs=[out_veredicto, marcador_deuda, out_status],
    )

if __name__ == "__main__":
    demo.launch()