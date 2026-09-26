import sqlite3
import threading
import time
from datetime import datetime
import requests

DB_NAME = "system_status.db"

def init_db():
    """Inicializa la base de datos SQLite para el registro persistente."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            status TEXT,
            message TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_event(status, message):
    """Guarda eventos de forma persistente en SQLite"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO logs (timestamp, status, message) VALUES (?, ?, ?)", (timestamp, status, message))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error al escribir log en BD: {e}")

def obtener_logs_db(limite=40):
    """Recupera los registros de la base de datos"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, status, message FROM logs ORDER BY id DESC LIMIT ?", (limite,))
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        return [("Error", "DB", str(e))]