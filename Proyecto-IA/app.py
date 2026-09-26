import threading
import time
from datetime import datetime
import requests
import customtkinter as ctk

# Importar los módulos separados
from monitor import init_db, log_event, obtener_logs_db
from asesor_ia import FinanzasCheckpointManager, evaluar_compra_ia

# Configuración inicial de CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MonitorWindow(ctk.CTkToplevel):
    """Ventana flotante emergente para consultar los estados y logs del monitor (demonio)"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("650x450")
        self.title("🛠️ Consola de Diagnóstico del Sistema")
        self.resizable(False, False)
        
        # Asegurar que la ventana aparezca al frente
        self.attributes("-topmost", True)

        # Título y Estado actual dentro de la ventana flotante
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=10)

        lbl_title = ctk.CTkLabel(header_frame, text="Estado de la Red y Enlaces de Ayuda", font=("Arial", 14, "bold"))
        lbl_title.pack(side="left")

        self.lbl_status_indicator = ctk.CTkLabel(
            header_frame, 
            text="● VERIFICANDO", 
            font=("Arial", 13, "bold"), 
            text_color="orange"
        )
        self.lbl_status_indicator.pack(side="right")

        # Caja de texto para los logs de SQLite
        self.textbox_logs = ctk.CTkTextbox(self, width=610, height=320, font=("Consolas", 10))
        self.textbox_logs.pack(padx=15, pady=5)
        self.textbox_logs.configure(state="disabled")

        # Botón de actualización manual
        btn_reload = ctk.CTkButton(self, text="Actualizar Registros de Base de Datos", width=250, command=self.load_logs_to_ui)
        btn_reload.pack(pady=10)

        self.load_logs_to_ui()

    def update_status_label(self, text, color):
        try:
            self.lbl_status_indicator.configure(text=f"● {text}", text_color=color)
        except Exception:
            pass

    def load_logs_to_ui(self):
        self.textbox_logs.configure(state="normal")
        self.textbox_logs.delete("1.0", "end")
        rows = obtener_logs_db(40)
        for row in rows:
            self.textbox_logs.insert("end", f"[{row[0]}] [{row[1]}] {row[2]}\n")
        self.textbox_logs.configure(state="disabled")


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sistema Integral - Asesor Financiero Tóxico")
        self.geometry("750x550")
        self.resizable(False, False)

        # Inicializar base de datos del monitor y control de hilo
        init_db()
        self.is_monitoring = True
        self.monitor_window_ref = None

        # --- BOTÓN DE CONFIGURACIÓN (ENGRANAJE) EN LA ESQUINA SUPERIOR DERECHA ---
        btn_config = ctk.CTkButton(
            self, 
            text="⚙️", 
            width=40, 
            height=40, 
            font=("Arial", 18),
            fg_color="#334155", 
            hover_color="#475569",
            command=self.abrir_monitor_flotante
        )
        # Posicionado de forma absoluta en la esquina superior derecha
        btn_config.place(x=685, y=15)

        # --- CONTENIDO PRINCIPAL: EL ASESOR FINANCIERO TÓXICO ---
        self.setup_finance_ui()

        # Iniciar el hilo del demonio en segundo plano (sigue corriendo su auditoría silenciosa)
        self.monitor_thread = threading.Thread(target=self.background_monitor, daemon=True)
        self.monitor_thread.start()

    def setup_finance_ui(self):
        estado_inicial = FinanzasCheckpointManager.load()
        total_inicial = estado_inicial["total_desperdiciado"]

        # Título principal centrado
        gr_title = ctk.CTkLabel(self, text="💸 El Hater Financiero (Anti-Gastos)", font=("Arial", 20, "bold"))
        gr_title.pack(pady=(25, 5))

        self.marcador_deuda = ctk.CTkLabel(self, text=f"Deuda Moral Acumulada: ${total_inicial:,.2f}", font=("Arial", 16, "bold"), text_color="#ff5555")
        self.marcador_deuda.pack(pady=5)

        # Contenedor de inputs
        frame_inputs = ctk.CTkFrame(self)
        frame_inputs.pack(pady=10, padx=20, fill="x")

        self.in_producto = ctk.CTkEntry(frame_inputs, placeholder_text="¿Qué quieres comprar? (Ej: Teclado)", width=450, height=35)
        self.in_producto.pack(pady=10)

        self.in_precio = ctk.CTkEntry(frame_inputs, placeholder_text="¿Cuánto cuesta? ($)", width=450, height=35)
        self.in_precio.pack(pady=10)

        self.in_excusa = ctk.CTkEntry(frame_inputs, placeholder_text="Tu justificación (Ej: Lo necesito para trabajar)", width=450, height=35)
        self.in_excusa.pack(pady=10)

        btn_juzgar = ctk.CTkButton(frame_inputs, text="Evaluar mi pésima decisión", fg_color="#d97706", hover_color="#b45309", height=40, command=self.ejecutar_juicio_financiero)
        btn_juzgar.pack(pady=15)

        # Caja de texto para la respuesta de la IA
        self.out_veredicto = ctk.CTkTextbox(self, width=680, height=130, font=("Arial", 12))
        self.out_veredicto.pack(pady=5)
        self.out_veredicto.insert("1.0", "Esperando tu decisión de compra...")
        self.out_veredicto.configure(state="disabled")

        btn_reset = ctk.CTkButton(self, text="Declararse en Bancarrota (Resetear Checkpoint)", fg_color="#dc2626", hover_color="#b91c1c", width=300, command=self.reset_financiero)
        btn_reset.pack(pady=10)

    def abrir_monitor_flotante(self):
        """Abre la ventana flotante de diagnóstico sin duplicarla"""
        if self.monitor_window_ref is None or not self.monitor_window_ref.winfo_exists():
            self.monitor_window_ref = MonitorWindow(self)
        else:
            self.monitor_window_ref.focus()

    def background_monitor(self):
        """Hilo Demonio autónomo que evalúa enlaces de ayuda en segundo plano"""
        target_url = "https://httpbin.org/status/200"
        
        while self.is_monitoring:
            timestamp = datetime.now().strftime("%H:%M:%S")
            status_text = "OPERATIVO"
            color_ui = "green"
            
            try:
                response = requests.get(target_url, timeout=5)
                if response.status_code == 200:
                    msg = f"[{timestamp}] Conexión OK con enlaces de ayuda/app."
                else:
                    status_text = "ADVERTENCIA"
                    color_ui = "orange"
                    msg = f"[{timestamp}] Respuesta con código: {response.status_code}"
            except requests.RequestException as e:
                status_text = "CAÍDO"
                color_ui = "red"
                msg = f"[{timestamp}] Fallo crítico de red: {e}"

            log_event(status_text, msg)
            
            # Si la ventana flotante del monitor está abierta, actualizar su indicador en tiempo real
            if self.monitor_window_ref and self.monitor_window_ref.winfo_exists():
                self.after(0, lambda s=status_text, c=color_ui: self.monitor_window_ref.update_status_label(s, c))
                # Opcional: si quieres que se refresquen los logs solos al abrir, puedes dejarlo manual o agregar auto-refresh
            
            time.sleep(15)

    def ejecutar_juicio_financiero(self):
        prod = self.in_producto.get()
        try:
            precio = float(self.in_precio.get())
        except ValueError:
            precio = 0.0
        excusa = self.in_excusa.get()

        if not prod or precio <= 0:
            self.actualizar_texto_veredicto("Por favor ingresa un producto válido y un precio mayor a 0.")
            return

        self.actualizar_texto_veredicto("Evaluando compra con IA en segundo plano...")
        threading.Thread(target=self._proceso_ia_hilo, args=(prod, precio, excusa), daemon=True).start()

    def _proceso_ia_hilo(self, prod, precio, excusa):
        veredicto, total_acumulado = evaluar_compra_ia(prod, precio, excusa)
        self.after(0, lambda: self.marcador_deuda.configure(text=f"Deuda Moral Acumulada: ${total_acumulado:,.2f}"))
        self.after(0, lambda: self.actualizar_texto_veredicto(veredicto))

    def actualizar_texto_veredicto(self, texto):
        self.out_veredicto.configure(state="normal")
        self.out_veredicto.delete("1.0", "end")
        self.out_veredicto.insert("1.0", texto)
        self.out_veredicto.configure(state="disabled")

    def reset_financiero(self):
        FinanzasCheckpointManager.reset()
        self.marcador_deuda.configure(text="Deuda Moral Acumulada: $0.00")
        self.actualizar_texto_veredicto("Historial de gastos reiniciado. Billetera en ceros.")

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()