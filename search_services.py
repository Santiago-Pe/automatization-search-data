# search_services.py
import requests
import google.generativeai as genai
from googleapiclient.discovery import build
from config import GOOGLE_API_KEY, SEARCH_ENGINE_ID, BLACKLISTED_DOMAINS
from urllib.parse import urlparse

# --- Configuración del Módulo ---
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except (TypeError, ValueError):
    print(
        "ADVERTENCIA: GOOGLE_API_KEY no configurada para Gemini. El Plan A no funcionará."
    )


# --- Funciones de Búsqueda en Cascada ---
def find_url_with_gemini(query):
    """Intento 1: Usa la API de Google Gemini para encontrar la URL."""
    print(f"  -> Plan A (IA): Buscando URL con Gemini para: '{query}'")
    try:
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        prompt = (
            f"Actúa como un experto en investigación online. ¿Cuál es el sitio web oficial principal de la corporación '{query}'? "
            f"Ignora perfiles de redes sociales o directorios. Devuelve únicamente la URL, y nada más. Si no encuentras un sitio web oficial claro, devuelve la palabra 'NULL'."
        )
        response = model.generate_content(prompt, request_options={"timeout": 45})
        url = response.text.strip().replace("`", "")

        if url != "NULL" and "http" in url:
            print(f"  -> Gemini sugiere la URL: {url}")
            return url
        return None
    except Exception as e:
        print(f"  -> Error en API de Gemini: {e}")
        return None


def find_url_with_custom_search(query):
    """Intento 2: Usa la Custom Search API como respaldo."""
    print(f"  -> Plan B (Búsqueda Web): Buscando con Custom Search para: '{query}'")
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        response = service.cse().list(q=query, cx=SEARCH_ENGINE_ID, num=5).execute()

        if "items" not in response:
            return None

        for item in response["items"]:
            url = item.get("link")
            if url:
                domain = urlparse(url).netloc
                if not any(
                    blacklisted in domain for blacklisted in BLACKLISTED_DOMAINS
                ):
                    print(f"  -> Custom Search encontró una URL válida: {url}")
                    return url
        return None
    except Exception as e:
        print(f"  -> Error en API de Custom Search: {e}")
        return None


def get_places_data_fallback(query):
    """Último Recurso: Usa la Places API para obtener datos estructurados."""
    print(f"  -> Plan D (Último Recurso): Buscando en Google Places para: '{query}'")
    try:
        # 1. Find Place
        find_place_url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={query}&inputtype=textquery&fields=place_id&key={GOOGLE_API_KEY}"
        response = requests.get(find_place_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data["status"] != "OK" or not data.get("candidates"):
            return {}

        # 2. Get Details del primer candidato
        place_id = data["candidates"][0]["place_id"]
        fields = "website,formatted_phone_number,url,geometry,name,formatted_address"
        details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields={fields}&key={GOOGLE_API_KEY}"
        response = requests.get(details_url, timeout=10)
        response.raise_for_status()
        result = response.json().get("result", {})

        # 3. Mapear a un diccionario estandarizado
        places_data = {
            "TELEFONO": result.get("formatted_phone_number"),
            "URL_Gmaps": result.get("url"),
            "LATITUD": result.get("geometry", {}).get("location", {}).get("lat"),
            "LONGITUD": result.get("geometry", {}).get("location", {}).get("lng"),
            "NOMBRE_COMERCIAL": result.get("name"),
            "DIRECCION": result.get("formatted_address"),
            "WEB": result.get("website"),
        }
        return {k: v for k, v in places_data.items() if v is not None}

    except Exception as e:
        print(f"  -> Error en API de Places: {e}")
        return {}
