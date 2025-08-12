# config.py
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CX_ID = os.getenv("CX_ID")
SHEET_NAME = "TEST_SCRAPING"
COLUMNS = [
    "ID_EMPRESA",
    "CUIT",
    "NOMBRE_ESTABLECIMIENTO",
    "NOMBRE_COMERCIAL",
    "TELEFONO",
    "TELEFONO_2",
    "TELEFONO_3",
    "EMAIL",
    "DIRECCION",
    "LOCALIDAD",
    "PROVINCIA",
    "LATITUD",
    "LONGITUD",
    "URL_Gmaps",
    "ESTADO",
    "FECHA_ACTUALIZACION",
]

if not GOOGLE_API_KEY or not CX_ID:
    raise ValueError(
        "Error: GOOGLE_API_KEY y/o CX_ID no están definidas en el archivo .env"
    )
