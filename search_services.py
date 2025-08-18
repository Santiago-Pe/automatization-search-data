# search_services.py
import requests
from googleapiclient.discovery import build
from config import GOOGLE_API_KEY, CX_ID

# ===================================================================
# Configuración del Módulo
# ===================================================================

# Se crea una única sesión de requests para reutilizar la conexión.
# Es una buena práctica para la eficiencia, especialmente si se hacen muchas llamadas.
HTTP_SESSION = requests.Session()

# ===================================================================
# Funciones Auxiliares (Helpers)
# ===================================================================


def _get_place_details(place_id):
    """
    Función auxiliar que toma un Place ID y devuelve los detalles de ese lugar.
    """
    fields = "website,formatted_phone_number,url,geometry"
    details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields={fields}&key={GOOGLE_API_KEY}"
    response = requests.get(details_url, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data.get("result", {}) if data.get("status") == "OK" else None


# ===================================================================
# Funciones Principales de Búsqueda
# ===================================================================


def search_google_maps(query):
    """
    Busca en Google Maps y DEVUELVE UN DICCIONARIO con los datos.
    """
    print(f"  Buscando en Google Maps: '{query}'")
    try:
        find_place_url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={query}&inputtype=textquery&fields=place_id&key={GOOGLE_API_KEY}"
        response = requests.get(find_place_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data["status"] != "OK" or not data.get("candidates"):
            print("  -> No se encontraron candidatos en Google Maps.")
            return {}  # Devuelve un diccionario vacío si no hay resultados

        detailed_candidates = []
        for candidate in data["candidates"][:3]:
            details = _get_place_details(candidate["place_id"])
            if details:
                detailed_candidates.append(details)

        if not detailed_candidates:
            return {}

        best_candidate = detailed_candidates[0]
        phone_list = []
        for candidate in detailed_candidates:
            phone = candidate.get("formatted_phone_number")
            if phone and phone not in phone_list:
                phone_list.append(phone)

        # ### CAMBIO CLAVE: Devolvemos un diccionario en lugar de una tupla ###
        return {
            "WEB": best_candidate.get("website"),
            "TELEFONOS": phone_list,
            "URL_Gmaps": best_candidate.get("url"),
            "LATITUD": best_candidate.get("geometry", {})
            .get("location", {})
            .get("lat"),
            "LONGITUD": best_candidate.get("geometry", {})
            .get("location", {})
            .get("lng"),
        }

    except requests.exceptions.RequestException as e:
        print(f"  -> Error de red en API de Maps: {e}")
    except Exception as e:
        print(f"  -> Error inesperado en API de Maps: {e}")

    return {}  # Devuelve un diccionario vacío en caso de error


def search_web_fallback(query):
    """
    Plan B: Busca una URL en la web usando la Custom Search API.
    """
    print(f"  Fallback: Buscando en la web con Custom Search: '{query}'")
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        response = service.cse().list(q=query, cx=CX_ID, num=1).execute()
        return (
            response["items"][0]["link"]
            if "items" in response and response["items"]
            else None
        )
    except Exception as e:
        print(f"  -> Error en API de Custom Search: {e}")
        return None
