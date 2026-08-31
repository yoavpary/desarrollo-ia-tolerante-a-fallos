import sentry_sdk
from loguru import logger
import sys

# 1. Configurar Loguru para registrar errores en un archivo local
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/errores_ia.log", rotation="500 KB", level="ERROR", backtrace=True, diagnose=True)

# 2. Inicializar Sentry SDK (con DSN de prueba/simulado)
sentry_sdk.init(
    dsn="https://1234567890abcdef1234567890abcdef@o123456.ingest.sentry.io/123456",
    traces_sample_rate=1.0,
)

def procesar_entrada_modelo(valor_a: str, valor_b: str) -> float:
    """Intenta procesar y calcular la inferencia a partir de strings de entrada."""
    try:
        num_a = float(valor_a)
        num_b = float(valor_b)
        
        # Simulación de cálculo de inferencia
        resultado = num_a / num_b
        logger.info(f"Cálculo completado exitosamente: {resultado}")
        return resultado

    except ValueError as val_err:
        # Registro local estructurado con Loguru
        logger.error(f"Error de conversión en las entradas '{valor_a}', '{valor_b}': {val_err}")
        # Notificación a Sentry
        sentry_sdk.capture_exception(val_err)
        return None

    except ZeroDivisionError as zero_err:
        # Captura de error de división por cero
        logger.critical(f"Error matemático crítico: {zero_err}")
        sentry_sdk.capture_exception(zero_err)
        return 0.0  # Fallback de recuperación


# --- Pruebas del sistema ---
if __name__ == "__main__":
    print("=== CASO 1: Datos correctos ===")
    res1 = procesar_entrada_modelo("50.0", "3.0")
    print(f"Resultado: {res1}\n")

    print("=== CASO 2: Entrada no numérica (capturada por Loguru y Sentry) ===")
    res2 = procesar_entrada_modelo("texto_invalido", "10")
    print(f"Resultado: {res2}\n")

    print("=== CASO 3: División por cero (capturada y recuperada con Fallback) ===")
    res3 = procesar_entrada_modelo("100", "0")
    print(f"Resultado: {res3}\n")