# services/free_search.py
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from config.config import USER_AGENTS, BLACKLISTED_DOMAINS
import random

HTTP_SESSION = requests.Session()


def get_razon_social(cuit):
    """Intenta obtener la Razón Social desde CuitOnline."""
    print("    -> [Gratis] Buscando Razón Social...")
    try:
        url = f"https://www.cuitonline.com/detalle/{cuit}/"
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = HTTP_SESSION.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        header = soup.find("h1", class_="denominacion")
        return header.get_text(strip=True) if header else None
    except requests.RequestException as e:
        print(f"      -> Error al scrapear CuitOnline: {e}")
        return None


def get_web(query):
    """Intenta obtener la URL del sitio web usando métodos de scraping gratuitos."""
    print("    -> [Gratis] Buscando URL del sitio web...")
    # Intento 1: Scrapear DuckDuckGo
    try:
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = HTTP_SESSION.get(search_url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        links = soup.find_all("a", class_="result__url")
        for link in links:
            url = link.get_text(strip=True)
            domain = url.split("/")[2]
            if not any(blacklisted in domain for blacklisted in BLACKLISTED_DOMAINS):
                print(f"      -> DuckDuckGo encontró: {url}")
                return url
        return None
    except requests.RequestException as e:
        print(f"      -> Error al scrapear DuckDuckGo: {e}")
        return None


def get_contactos_from_web(url):
    """Extrae emails y teléfonos de una URL dada."""
    if not url:
        return {}
    print(f"    -> [Gratis] Scrapeando contactos desde: {url}")
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = HTTP_SESSION.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        text = BeautifulSoup(response.text, "html.parser").get_text()

        emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text)
        phones = re.findall(r"\(?\+?\d[\d\s\-\(\)]{7,}\d", text)

        data = {}
        if emails:
            data["EMAIL"] = emails[0]
        if len(phones) > 0:
            data["TELEFONO"] = phones[0].strip()
        if len(phones) > 1:
            data["TELEFONO_2"] = phones[1].strip()
        if len(phones) > 2:
            data["TELEFONO_3"] = phones[2].strip()
        return data
    except requests.RequestException as e:
        print(f"      -> Error de red al scrapear contactos: {e}")
        return {}


def get_maps_data(query):
    """Intenta obtener datos de Google Maps scrapeando la URL de búsqueda."""
    print("    -> [Gratis] Buscando datos de Google Maps...")
    try:
        search_url = f"https://www.google.com/maps/search/{quote_plus(query)}"
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = HTTP_SESSION.get(search_url, timeout=10, headers=headers)
        response.raise_for_status()

        final_url = response.url
        coords_match = re.search(r"/@(-?\d+\.\d+),(-?\d+\.\d+)", final_url)

        if coords_match:
            lat, lon = coords_match.groups()
            print("      -> Coordenadas encontradas por scraping.")
            return {
                "LATITUD": float(lat),
                "LONGITUD": float(lon),
                "URL_Gmaps": final_url,
            }
        return {}
    except requests.RequestException as e:
        print(f"      -> Error al scrapear Google Maps: {e}")
        return {}
