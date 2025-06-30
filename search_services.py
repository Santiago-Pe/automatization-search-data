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
    # Define los campos específicos que queremos de la API de Place Details.
    fields = "website,formatted_phone_number,url,geometry"
    details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields={fields}&key={GOOGLE_API_KEY}"
    
    response = requests.get(details_url, timeout=10)
    response.raise_for_status()  # Lanza un error si la petición HTTP falla.
    
    data = response.json()
    return data.get('result', {}) if data.get('status') == 'OK' else None

# ===================================================================
# Funciones Principales de Búsqueda
# ===================================================================

def search_google_maps(query):
    """
    Busca información en Google Maps, analizando hasta 3 candidatos.
    """
    print(f"  Buscando en Google Maps: '{query}'")
    try:
        find_place_url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={query}&inputtype=textquery&fields=place_id&key={GOOGLE_API_KEY}"
        response = requests.get(find_place_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data['status'] != 'OK' or not data.get('candidates'):
            print("  -> No se encontraron candidatos en Google Maps.")
            return None, [], None, None, None

        # Obtener detalles para los primeros 3 candidatos
        detailed_candidates = []
        for candidate in data['candidates'][:3]:
            details = _get_place_details(candidate['place_id'])
            if details:
                detailed_candidates.append(details)

        if not detailed_candidates:
            return None, [], None, None, None

        # Estrategia: El "mejor" candidato es el primero con más datos.
        best_candidate = detailed_candidates[0]
        website = best_candidate.get('website')
        maps_url = best_candidate.get('url')
        lat = best_candidate.get('geometry', {}).get('location', {}).get('lat')
        lng = best_candidate.get('geometry', {}).get('location', {}).get('lng')

        # Recopilar hasta 3 teléfonos únicos de TODOS los candidatos.
        phone_list = []
        for candidate in detailed_candidates:
            phone = candidate.get('formatted_phone_number')
            if phone and phone not in phone_list:
                phone_list.append(phone)
        
        return website, phone_list, maps_url, lat, lng

    except requests.exceptions.RequestException as e:
        print(f"  -> Error de red en API de Maps: {e}")
    except Exception as e:
        print(f"  -> Error inesperado en API de Maps: {e}")
    
    return None, [], None, None, None


def search_web_fallback(query):
    """
    Plan B: Busca una URL en la web usando la Custom Search API.

    Args:
        query (str): El texto a buscar.

    Returns:
        str: La primera URL encontrada o None.
    """
    print(f"  Fallback: Buscando en la web con Custom Search: '{query}'")
    try:
        # Construye el servicio de Google API.
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        
        # Ejecuta la búsqueda pidiendo solo el primer resultado.
        response = service.cse().list(q=query, cx=CX_ID, num=1).execute()
        
        # Devuelve el enlace si existe en la respuesta.
        return response['items'][0]['link'] if 'items' in response and response['items'] else None
        
    except Exception as e:
        print(f"  -> Error en API de Custom Search: {e}")
        return None
