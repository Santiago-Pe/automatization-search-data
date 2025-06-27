# scraper.py
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def _buscar_datos_en_soup(soup):
    """Función auxiliar que busca email y teléfono en un objeto BeautifulSoup."""
    email = None
    telefono = None
    
    # Búsqueda de Email
    mailto_link = soup.find('a', href=re.compile(r'^mailto:'))
    if mailto_link:
        email = mailto_link['href'].replace('mailto:', '').strip()
    else:
        email_regex = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
        email_match = email_regex.search(soup.get_text())
        if email_match: email = email_match.group(0)
        
    # Búsqueda de Teléfono
    phone_regex = re.compile(r'\(?\+?\d[\d\s\-\(\)]{7,}\d')
    phone_match = phone_regex.search(soup.get_text())
    if phone_match: telefono = phone_match.group(0).strip()
        
    return email, telefono

def extraer_info_de_pagina(url):
    """Visita una URL, busca una página de 'Contacto' y extrae email y teléfono."""
    if not url: return None, None
    print(f"  Analizando página en busca de datos: {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        respuesta = requests.get(url, headers=headers, timeout=15)
        if respuesta.status_code != 200: return None, None
        
        soup_principal = BeautifulSoup(respuesta.text, 'html.parser')
        
        regex_contacto = re.compile(r'contact', re.IGNORECASE)
        link_contacto = soup_principal.find('a', href=True, string=regex_contacto)
        if not link_contacto: link_contacto = soup_principal.find('a', href=regex_contacto)
            
        if link_contacto:
            url_contacto = urljoin(url, link_contacto['href'])
            print(f"  -> Página de contacto encontrada, analizándola: {url_contacto}")
            try:
                resp_contacto = requests.get(url_contacto, headers=headers, timeout=15)
                if resp_contacto.status_code == 200:
                    email, telefono = _buscar_datos_en_soup(BeautifulSoup(resp_contacto.text, 'html.parser'))
                    if email or telefono: return email, telefono
            except requests.exceptions.RequestException: pass
        
        return _buscar_datos_en_soup(soup_principal)
    except requests.exceptions.RequestException: return None, None