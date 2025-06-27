# search_services.py
import requests
from googleapiclient.discovery import build
from config import GOOGLE_API_KEY, CX_ID

# ===================================================================
# FUNCIONES DE BÚSQUEDA Y EXTRACCIÓN
# ===================================================================
def buscar_info_en_google_maps(query):
    print(f"  Buscando en Google Maps: '{query}'")
    try:
        find_place_url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={query}&inputtype=textquery&fields=place_id&key={GOOGLE_API_KEY}"
        respuesta_find = requests.get(find_place_url, timeout=10)
        respuesta_find.raise_for_status()
        data_find = respuesta_find.json()
        if data_find['status'] == 'OK' and data_find.get('candidates'):
            place_id = data_find['candidates'][0]['place_id']
            details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=website,formatted_phone_number&key={GOOGLE_API_KEY}"
            respuesta_details = requests.get(details_url, timeout=10)
            respuesta_details.raise_for_status()
            data_details = respuesta_details.json()
            if data_details['status'] == 'OK':
                resultado = data_details.get('result', {})
                return resultado.get('website'), resultado.get('formatted_phone_number')
        return None, None
    except Exception as e:
        print(f"  -> Error en API de Maps: {e}")
        return None, None

def buscar_url_oficial_fallback(query):
    print(f"  Fallback: Buscando en la web con Custom Search: '{query}'")
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        res = service.cse().list(q=query, cx=CX_ID, num=1).execute()
        return res['items'][0]['link'] if 'items' in res and res['items'] else None
    except Exception as e:
        print(f"  -> Error en API de Custom Search: {e}")
        return None