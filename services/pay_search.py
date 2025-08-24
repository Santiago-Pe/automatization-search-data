# services/paid_search.py
import requests
import google.generativeai as genai
from googleapiclient.discovery import build
from config.config import GOOGLE_API_KEY, CX_ID
import os
import json

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def get_data_with_places(query):
    """Prioridad 1 (API): Usa Places API para obtener un paquete de datos."""
    print("    -> [API de Pago] Buscando con Google Places...")
    try:
        find_place_url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={query}&inputtype=textquery&fields=place_id&key={GOOGLE_API_KEY}"
        response = requests.get(find_place_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data["status"] != "OK" or not data.get("candidates"):
            return {}
        place_id = data["candidates"][0]["place_id"]

        fields = "website,formatted_phone_number,url,geometry,name,formatted_address"
        details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields={fields}&key={GOOGLE_API_KEY}"
        response = requests.get(details_url, timeout=10)
        response.raise_for_status()
        result = response.json().get("result", {})

        return {
            "TELEFONO": result.get("formatted_phone_number"),
            "URL_Gmaps": result.get("url"),
            "LATITUD": result.get("geometry", {}).get("location", {}).get("lat"),
            "LONGITUD": result.get("geometry", {}).get("location", {}).get("lng"),
            "DIRECCION": result.get("formatted_address"),
            "WEB": result.get("website"),
        }
    except Exception as e:
        print(f"      -> Error en API de Places: {e}")
        return {}


def get_data_with_gemini(query, data_needed):
    """Prioridad 2 (API): Usa Gemini para buscar datos específicos faltantes."""
    print(f"    -> [API de Pago] Consultando a Gemini por: {data_needed}")
    try:
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        prompt = f"Para la empresa '{query}', necesito los siguientes datos: {', '.join(data_needed)}. Devuelve el resultado en formato JSON. Si no encuentras un dato, usa null."
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("`", "").replace("json", "")
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"      -> Error en API de Gemini: {e}")
        return {}


def get_web_with_custom_search(query):
    """Prioridad 3 (API): Usa Custom Search como último recurso para la WEB."""
    print("    -> [API de Pago] Usando Custom Search como último recurso...")
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        response = service.cse().list(q=query, cx=CX_ID, num=1).execute()
        return (
            response["items"][0]["link"]
            if "items" in response and response["items"]
            else None
        )
    except Exception as e:
        print(f"      -> Error en API de Custom Search: {e}")
        return None
