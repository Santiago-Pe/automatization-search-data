# config/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# --- Claves de API ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CX_ID = os.getenv("CX_ID")

# --- Configuración de Google Sheets ---
SHEET_NAME = "TEST_SCRAPING"

# --- Listas de Control ---
# Define qué datos son esenciales para considerar una fila "completa"
CRITICAL_DATA = ["WEB", "TELEFONO", "EMAIL", "LATITUD", "LONGITUD", "URL_Gmaps"]

# URLs formateables para scraping de directorios gratuitos
WHITELIST_DIRECTORIES = []

# Dominios a ignorar en los resultados de búsqueda
BLACKLISTED_DOMAINS = [
    "facebook.com",
    "twitter.com",
    "youtube.com",
    "wikipedia.org",
    "datos.gob.ar",
    "boletinoficial.gob.ar",
]

# User agents para rotar en las peticiones de scraping
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
]

# --- Validación de Secretos ---
if not GOOGLE_API_KEY or not CX_ID:
    raise ValueError(
        "Error: GOOGLE_API_KEY y/o CX_ID no están definidas en el archivo .env"
    )
