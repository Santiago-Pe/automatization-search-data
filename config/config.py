# config/config.py - CONFIGURACIÓN MEJORADA
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
WHITELIST_DIRECTORIES = [
    "paginasamarillas.com.ar",
    "guiaoleo.com.ar",
    "tucomercio.com.ar",
    "comercios.com.ar",
    "locales.com.ar",
    "cuitonline.com",
    "dateas.com",
    "argentina.gob.ar",
    "buenosaires.gob.ar",
]

# Dominios a ignorar en los resultados de búsqueda - AMPLIADO
BLACKLISTED_DOMAINS = [
    # Redes sociales
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "linkedin.com",
    "youtube.com",
    "tiktok.com",
    "snapchat.com",
    # Sitios de información general
    "wikipedia.org",
    "wikimedia.org",
    # Sitios gubernamentales genéricos
    "datos.gob.ar",
    "boletinoficial.gob.ar",
    # Marketplaces y clasificados
    "mercadolibre.com",
    "olx.com",
    "alamaula.com",
    # Directorios genéricos internacionales
    "yellowpages.com",
    "whitepages.com",
    "yelp.com",
    # Sitios de noticias generales (pueden tener menciones pero no ser la empresa)
    "clarin.com",
    "lanacion.com.ar",
    "infobae.com",
    # Otros sitios problemáticos
    "pinterest.com",
    "tumblr.com",
    "reddit.com",
]

# User agents para rotar en las peticiones de scraping - AMPLIADO
USER_AGENTS = [
    # Chrome en Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    # Chrome en Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Firefox en Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
    # Firefox en Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Safari en Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    # Edge en Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    # Chrome en Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Móviles (para mayor variedad)
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
]

# --- Configuraciones de Rate Limiting ---
RATE_LIMIT_CONFIG = {
    "min_delay": 1,  # Mínimo delay entre requests (segundos)
    "max_delay": 3,  # Máximo delay entre requests (segundos)
    "retry_attempts": 3,  # Número de reintentos por request
    "backoff_factor": 2,  # Factor de backoff exponencial
}

# --- Configuraciones de Timeout ---
TIMEOUT_CONFIG = {
    "connect_timeout": 10,  # Timeout de conexión
    "read_timeout": 15,  # Timeout de lectura
    "total_timeout": 25,  # Timeout total
}

# --- Configuración de Cache ---
CACHE_CONFIG = {
    "ttl_seconds": 86400,  # 24 horas
    "cleanup_interval": 604800,  # 7 días para limpieza
    "max_entries": 10000,  # Máximo número de entradas en cache
}

# --- Patrones de Validación ---
VALIDATION_PATTERNS = {
    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "phone_argentina": [
        r"\+?54\s?9?\s?\d{2,4}\s?\d{3,4}[-\s]?\d{4}",  # Formato completo
        r"\(\+?54\)\s?\d{2,4}\s?\d{3,4}[-\s]?\d{4}",  # Con paréntesis
        r"\b\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4}\b",  # Local
        r"\(\d{3,4}\)\s?\d{3,4}[-\s]?\d{4}",  # Con código área
    ],
    "cuit": r"^\d{2}-?\d{8}-?\d{1}$",
}

# --- Coordenadas de Argentina (para validación) ---
ARGENTINA_BOUNDS = {
    "lat_min": -55.0,
    "lat_max": -21.0,
    "lng_min": -74.0,
    "lng_max": -53.0,
}
