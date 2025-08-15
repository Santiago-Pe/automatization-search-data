# scraper.py
import os
import json
import requests
import re
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from config import USER_AGENTS
import google.generativeai as genai

# --- Configuración del Módulo ---
HTTP_SESSION = requests.Session()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# --- Funciones de Extracción ---


def _extract_with_regex(text):
    """Extrae emails y teléfonos usando expresiones regulares."""
    emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    phones = re.findall(r"\(?\+?\d[\d\s\-\(\)]{7,}\d", text)

    # Limpieza básica
    cleaned_phones = [re.sub(r"\s+", " ", p).strip() for p in phones]

    return list(set(emails)), list(set(cleaned_phones))


def _extract_with_gemini(text):
    """Usa Gemini para extraer datos complejos si regex falla."""
    print("    -> Usando IA (Gemini) para análisis de texto profundo...")
    try:
        # Truncamos el texto para no exceder los límites de la API y ahorrar costos
        max_chars = 15000
        truncated_text = text[:max_chars]

        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        prompt = (
            "Analiza el siguiente texto de un sitio web y extrae la dirección física principal y el número de teléfono de contacto principal. "
            'Devuelve el resultado en formato JSON: {"direccion": "...", "telefono": "..."}. Si no encuentras un dato, usa null.'
            f"\n\nTEXTO:\n{truncated_text}"
        )
        response = model.generate_content(prompt)
        # Limpieza para asegurar que sea un JSON válido
        cleaned_response = response.text.strip().replace("`", "").replace("json", "")
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"    -> Error en extracción con Gemini: {e}")
        return {}


# --- Función Principal ---


def scrape_website(url):
    """
    Orquesta el proceso de scraping: descarga, extrae con regex y, si es necesario, con IA.
    """
    if not url:
        return {}

    print(f"  -> Plan C (Análisis Profundo): Scrapeando {url}")
    try:
        # Rotación de User-Agent
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = HTTP_SESSION.get(url, timeout=15, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Primero, intentar encontrar una página de contacto para un análisis más enfocado
        contact_regex = re.compile(r"contact", re.IGNORECASE)
        contact_link = soup.find("a", href=contact_regex)
        if contact_link:
            contact_url = urljoin(url, contact_link["href"])
            try:
                contact_response = HTTP_SESSION.get(
                    contact_url, timeout=15, headers=headers
                )
                if contact_response.ok:
                    soup = BeautifulSoup(contact_response.text, "html.parser")
                    print(
                        f"    -> Análisis enfocado en la página de contacto: {contact_url}"
                    )
            except requests.RequestException:
                pass  # Si falla, continuamos con la página principal

        page_text = soup.get_text()

        # 1. Extracción rápida con Regex
        emails, regex_phones = _extract_with_regex(page_text)

        scraped_data = {
            "EMAIL": emails[0] if emails else None,
            "TELEFONO_2": regex_phones[0] if len(regex_phones) > 0 else None,
            "TELEFONO_3": regex_phones[1] if len(regex_phones) > 1 else None,
        }

        # 2. Si faltan datos clave, usamos la IA como respaldo
        if not scraped_data.get(
            "TELEFONO_2"
        ):  # Asumimos que el teléfono principal puede estar aquí
            gemini_data = _extract_with_gemini(page_text)
            # Integramos los resultados de Gemini, sin sobreescribir lo que ya encontramos
            if gemini_data.get("telefono") and not scraped_data.get("TELEFONO_2"):
                scraped_data["TELEFONO_2"] = gemini_data["telefono"]
            # Podríamos también extraer la dirección aquí si fuera necesario
            # if gemini_data.get("direccion"):
            #     scraped_data["DIRECCION"] = gemini_data["direccion"]

        return {k: v for k, v in scraped_data.items() if v is not None}

    except requests.RequestException as e:
        print(f"  -> Error de red durante el scraping: {e}")
        return {"ERROR": str(e)}
    except Exception as e:
        print(f"  -> Error inesperado durante el scraping: {e}")
        return {"ERROR": str(e)}
