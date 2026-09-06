import json
import os
import gradio as gr
from google import genai

# --- 1. CONFIGURACIÓN DEL MODELO ---
# Clave obtenida desde Google AI Studio
GOOGLE_API_KEY = "TU API_KEY_AQUI"  # Reemplaza con tu clave real

# Inicialización del cliente moderno de la API de Gemini
client = genai.Client(api_key=GOOGLE_API_KEY)

# Archivo persistente en disco para almacenar los checkpoints
CHECKPOINT_FILE = "historial_asesor.json"


# --- 2. GESTOR DE CHECKPOINTING (Tolerancia a fallos) ---
class FinanzasCheckpointManager:
    """Administra el guardado y la recuperación de estado de la aplicación."""

    @staticmethod
    def load():
        """
        Lee el archivo de checkpoint en disco.
        Si la app se reinicia o se corta la energía, restaura el estado previo.
        """
        if os.path.exists(CHECKPOINT_FILE):
            try:
                with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Error Checkpoint] No se pudo leer el archivo: {e}")
        # Estado inicial por defecto si no existe archivo previo
        return {"total_desperdiciado": 0.0, "compras_previas": []}

    @staticmethod
    def save(total: float, compras: list):
        """
        Escritura atómica:
        Primero escribe en un archivo temporal (.tmp) y luego lo reemplaza.
        Esto previene la corrupción de datos si el sistema se apaga durante la escritura.
        """
        temp_file = f"{CHECKPOINT_FILE}.tmp"
        data = {
            "total_desperdiciado": total,
            "compras_previas": compras
        }
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, CHECKPOINT_FILE)

    @staticmethod
    def reset():
        """Borra el checkpoint para iniciar un historial limpio."""
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)
        return 0.0, "Historial reiniciado. Billetera en ceros."


# --- 3. LÓGICA DE INFERENCIA DE LA IA ---
def juzgar_compra(producto: str, precio: float, justificacion: str):
    # Validación básica de entradas
    if not producto or precio <= 0:
        return (
            "Ingresa un producto válido y un precio mayor a 0.",
            "$0.00",
            "Entrada inválida."
        )

    # Cargar el último punto de control guardado
    estado = FinanzasCheckpointManager.load()
    total_acumulado = estado["total_desperdiciado"] + precio
    historial = estado["compras_previas"]

    # Contexto de las últimas compras para que el modelo tenga memoria conversacional
    previas_texto = ", ".join([f"{c['producto']} (${c['precio']})" for c in historial[-3:]])
    contexto_previo = (
        f"Compras innecesarias previas en la sesión: [{previas_texto}]"
        if previas_texto else "Primera compra registrada."
    )

    # Instrucción estructurada para el modelo
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
    3. Si ya tiene gastos acumulados en el historial, échale en cara su falta de control financiero.
    """

    try:
        # Llamada al modelo usando la biblioteca google-genai
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        veredicto = response.text.strip()

        # Actualizar lista y persistir el checkpoint inmediatamente tras la respuesta exitosa
        historial.append({"producto": producto, "precio": precio, "justificacion": justificacion})
        FinanzasCheckpointManager.save(total=total_acumulado, compras=historial)

        marcador = f"Deuda Moral Acumulada: ${total_acumulado:,.2f}"
        status = f"Checkpoint actualizado: {len(historial)} decisiones registradas."
        return veredicto, marcador, status

    except Exception as e:
        return (
            f"Error al conectar con la API: {e}",
            f"${estado['total_desperdiciado']:,.2f}",
            "Fallo de conexión."
        )


# --- 4. INTERFAZ GRÁFICA (Gradio) ---
# Se precarga el estado actual al iniciar el servidor web
estado_inicial = FinanzasCheckpointManager.load()
total_inicial = estado_inicial["total_desperdiciado"]

with gr.Blocks(title="Asesor Financiero Tóxico") as demo:
    gr.Markdown("# 💸 El Hater Financiero (Asesor Anti-Gastos)")
    gr.Markdown("Registra lo que pretendes comprar. La IA evaluará si tu lógica tiene sentido.")

    marcador_deuda = gr.Label(value=f"Deuda Moral Acumulada: ${total_inicial:,.2f}")

    with gr.Row():
        with gr.Column():
            in_producto = gr.Textbox(label="¿Qué quieres comprar?", placeholder="Ej: Teclado mecánico")
            in_precio = gr.Number(label="¿Cuánto cuesta? ($)", value=0.0)
            in_excusa = gr.Textbox(label="Tu justificación", placeholder="Ej: Es para programar más rápido")
            btn_juzgar = gr.Button("Evaluar mi pésima decisión", variant="primary")

        with gr.Column():
            out_veredicto = gr.Textbox(label="Veredicto del Asesor", lines=6)
            out_status = gr.Textbox(label="Estado del Checkpoint", interactive=False)
            btn_reset = gr.Button("Declararse en Bancarrota (Resetear)", variant="stop")

    # Vinculación de eventos con botones
    btn_juzgar.click(
        fn=juzgar_compra,
        inputs=[in_producto, in_precio, in_excusa],
        outputs=[out_veredicto, marcador_deuda, out_status]
    )

    btn_reset.click(
        fn=lambda: (FinanzasCheckpointManager.reset()[1], "Deuda Moral Acumulada: $0.00", "Checkpoint borrado."),
        inputs=None,
        outputs=[out_veredicto, marcador_deuda, out_status]
    )

# --- 5. ARRANQUE DEL SERVIDOR ---
if __name__ == "__main__":
    demo.launch()