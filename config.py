# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# --- Claves de API ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("CX_ID")

# --- Configuración de Google Sheets ---
SHEET_NAME = "TEST_SCRAPING"
SHEET_INDEX = 1
PROCESSING_LIMIT = 200

# ### CAMBIO: Se añaden las columnas WEB y PAIS a la lista oficial ###
COLUMNS = [
    "ID_EMPRESA",
    "CUIT",
    "NOMBRE_ESTABLECIMIENTO",
    "NOMBRE_COMERCIAL",
    "WEB",
    "TELEFONO",
    "TELEFONO_2",
    "TELEFONO_3",
    "EMAIL",
    "DIRECCION",
    "LOCALIDAD",
    "PROVINCIA",
    "PAIS",
    "LATITUD",
    "LONGITUD",
    "URL_Gmaps",
    "ESTADO",
    "FECHA_ACTUALIZACION",
]

# --- Configuración de Búsqueda y Scraping (sin cambios) ---
BLACKLISTED_DOMAINS = [
    "linkedin.com",
    "facebook.com",
    "twitter.com",
    "instagram.com",
    "youtube.com",
    "google.com",
    "maps.google.com",
    "paginasamarillas.com.ar",
    "cuitonline.com",
    "wikipedia.org",
    "datos.gob.ar",
    "boletinoficial.gob.ar",
]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
]

# --- Validación de Secretos ---
if not GOOGLE_API_KEY or not SEARCH_ENGINE_ID:
    raise ValueError(
        "Error: GOOGLE_API_KEY y/o CX_ID no están definidas en el archivo .env"
    )
