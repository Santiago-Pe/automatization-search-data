# scraper.py
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ===================================================================
# Configuración del Módulo
# ===================================================================

# Se crea una única sesión de requests para reutilizar la conexión.
HTTP_SESSION = requests.Session()
# Definimos un User-Agent por defecto para simular un navegador.
HTTP_SESSION.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

# ===================================================================
# Funciones Auxiliares (Helpers)
# ===================================================================

def _extract_data_from_soup(soup):
    """
    Función auxiliar que busca un email y un teléfono en un objeto BeautifulSoup.
    """
    email = None
    phone = None
    
    # Búsqueda de Email: Prioriza enlaces 'mailto:', luego busca con RegEx.
    mailto_link = soup.find('a', href=re.compile(r'^mailto:'))
    if mailto_link:
        email = mailto_link['href'].replace('mailto:', '').strip()
    else:
        email_regex = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
        email_match = email_regex.search(soup.get_text())
        if email_match:
            email = email_match.group(0)
        
    # Búsqueda de Teléfono: Usa RegEx para encontrar secuencias de números.
    phone_regex = re.compile(r'\(?\+?\d[\d\s\-\(\)]{7,}\d')
    phone_match = phone_regex.search(soup.get_text())
    if phone_match:
        phone = phone_match.group(0).strip()
        
    return email, phone

# ===================================================================
# Función Principal de Scraping
# ===================================================================

def scrape_contact_info(url):
    """
    Visita una URL, busca una página de 'Contacto' y extrae el email y teléfono.

    Args:
        url (str): La URL del sitio web a analizar.

    Returns:
        tuple: (email, phone) o (None, None) si no se encuentran datos.
    """
    if not url:
        return None, None
        
    print(f"  Analizando página en busca de datos: {url}")
    try:
        response = HTTP_SESSION.get(url, timeout=15)
        response.raise_for_status()
        
        main_soup = BeautifulSoup(response.text, 'html.parser')
        
        # Estrategia: Busca un enlace a una página de "Contacto".
        contact_regex = re.compile(r'contact', re.IGNORECASE)
        contact_link = main_soup.find('a', href=True, string=contact_regex)
        if not contact_link:
            contact_link = main_soup.find('a', href=contact_regex)
            
        # Si encuentra una página de contacto, la analiza prioritariamente.
        if contact_link:
            contact_url = urljoin(url, contact_link['href'])
            print(f"  -> Página de contacto encontrada, analizándola: {contact_url}")
            try:
                contact_response = HTTP_SESSION.get(contact_url, timeout=15)
                contact_response.raise_for_status()
                contact_soup = BeautifulSoup(contact_response.text, 'html.parser')
                email, phone = _extract_data_from_soup(contact_soup)
                # Si encuentra algo en la página de contacto, lo devuelve.
                if email or phone:
                    return email, phone
            except requests.exceptions.RequestException as e:
                print(f"  -> No se pudo acceder a la página de contacto: {e}")
        
        # Si no, busca en la página principal como último recurso.
        return _extract_data_from_soup(main_soup)

    except requests.exceptions.RequestException as e:
        print(f"  -> Error al acceder a la URL para scraping: {e}")
        return None, None
    except Exception as e:
        print(f"  -> Error inesperado durante el scraping: {e}")
        return None, None
