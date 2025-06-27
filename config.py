# config.py
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CX_ID = os.getenv("CX_ID")
SHEET_NAME = "TEST_SCRAPING"

if not GOOGLE_API_KEY or not CX_ID:
    raise ValueError("Error: GOOGLE_API_KEY y/o CX_ID no están definidas en el archivo .env")