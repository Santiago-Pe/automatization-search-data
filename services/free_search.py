# services/free_search.py - VERSIÓN MEJORADA COMPLETA
import requests
import re
import json
import time
import random
import hashlib
import logging
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin, urlparse
from config.config import USER_AGENTS, BLACKLISTED_DOMAINS
from tenacity import retry, stop_after_attempt, wait_exponential

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sesiones HTTP separadas para cada motor
SESSIONS = {
    "duckduckgo": requests.Session(),
    "bing": requests.Session(),
    "startpage": requests.Session(),
    "yandex": requests.Session(),
    "directories": requests.Session(),
}

# Directorios argentinos para scraping
ARGENTINA_DIRECTORIES = [
    {
        "name": "PaginasAmarillas",
        "url": "https://www.paginasamarillas.com.ar/buscar",
        "params": {"que": "{query}", "donde": "{location}"},
        "result_selector": ".results-item h3 a",
        "link_attr": "href",
    },
    {
        "name": "GuiaOleo",
        "url": "https://www.guiaoleo.com.ar/buscar",
        "params": {"q": "{query}"},
        "result_selector": ".listing-item h3 a",
        "link_attr": "href",
    },
]

# Proxies gratuitos rotativos (opcional)
FREE_PROXIES = [
    # Se pueden agregar proxies gratuitos aquí
    # {'http': 'http://proxy:port', 'https': 'https://proxy:port'}
]


def get_random_headers():
    """Genera headers aleatorios realistas."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": random.choice(
            ["es-AR,es;q=0.9,en;q=0.8", "en-US,en;q=0.8,es;q=0.6"]
        ),
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def get_cache_key(query, location=None):
    """Genera clave única para cache."""
    data = f"{query}_{location or ''}"
    return hashlib.md5(data.encode()).hexdigest()


def get_cached_result(cache_key):
    """Obtiene resultado desde cache local."""
    try:
        with open("cache.json", "r", encoding="utf-8") as f:
            cache = json.load(f)
            cached_item = cache.get(cache_key)
            if cached_item:
                # Verificar TTL (24 horas)
                cached_time = cached_item.get("timestamp", 0)
                if time.time() - cached_time < 86400:  # 24 horas
                    logger.info(f"Cache hit para {cache_key}")
                    return cached_item.get("result")
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return None


def save_to_cache(cache_key, result):
    """Guarda resultado en cache local."""
    try:
        try:
            with open("cache.json", "r", encoding="utf-8") as f:
                cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            cache = {}

        cache[cache_key] = {"result": result, "timestamp": time.time()}

        with open("cache.json", "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error guardando cache: {e}")


def extract_domain(url):
    """Extrae dominio limpio de una URL."""
    try:
        parsed = urlparse(url if url.startswith("http") else f"http://{url}")
        return parsed.netloc.lower().replace("www.", "")
    except Exception:
        return url.lower()


def score_url_relevance(url, company_name, location=None):
    """Sistema de puntuación para URLs encontradas."""
    if not url:
        return 0

    score = 0
    domain = extract_domain(url)
    company_clean = re.sub(
        r"\b(S\.?A\.?|SRL|LIMITADA|SOCIEDAD|CIA)\b", "", company_name.upper()
    ).strip()

    # +15 si contiene nombre de empresa exacto
    if company_clean.lower() in domain:
        score += 15

    # +10 si contiene palabras clave de la empresa
    company_words = company_clean.split()
    for word in company_words:
        if len(word) > 3 and word.lower() in domain:
            score += 3

    # +8 si es dominio argentino
    if domain.endswith(".ar"):
        score += 8
    elif domain.endswith(".com"):
        score += 3

    # +5 si contiene localidad
    if location and location.lower().replace(" ", "") in domain.replace(
        "-", ""
    ).replace(".", ""):
        score += 5

    # -10 si está en blacklist
    if any(bl in domain for bl in BLACKLISTED_DOMAINS):
        score -= 10

    # -5 si es red social o marketplace
    social_patterns = [
        "facebook",
        "instagram",
        "twitter",
        "linkedin",
        "mercadolibre",
        "olx",
    ]
    if any(pattern in domain for pattern in social_patterns):
        score -= 5

    # +5 si parece ser sitio corporativo
    corporate_patterns = ["www", "empresa", "corp", "company", "oficial"]
    if any(pattern in domain for pattern in corporate_patterns):
        score += 2

    return score


def generate_smart_queries(company_name, location=None, cuit=None):
    """Genera múltiples variaciones de consulta inteligentes."""
    # Limpiar nombre de empresa
    company_clean = re.sub(
        r"\b(S\.?A\.?|SRL|LIMITADA|SOCIEDAD|Y?\s*CIA)\b", "", company_name
    ).strip()

    queries = [
        company_name,
        company_clean,
        f'"{company_name}" sitio web',
        f'"{company_name}" página web',
        f"{company_name} contacto",
        f"{company_name} empresa",
    ]

    if location:
        queries.extend(
            [
                f"{company_name} {location}",
                f"{company_clean} {location}",
                f'"{company_name}" {location} contacto',
            ]
        )

    if cuit:
        queries.extend([f"CUIT {cuit}", f"{cuit} empresa"])

    # Filtrar duplicados y queries vacías
    return list(filter(None, list(dict.fromkeys(queries))))


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
def robust_request(session, url, **kwargs):
    """Request robusto con reintentos."""
    response = session.get(url, timeout=15, **kwargs)
    response.raise_for_status()
    return response


def search_duckduckgo(query):
    """Búsqueda en DuckDuckGo mejorada."""
    try:
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        headers = get_random_headers()

        response = robust_request(SESSIONS["duckduckgo"], search_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # Múltiples selectores para mayor compatibilidad
        selectors = ["a.result__url", ".result__url", ".result-link", 'a[href^="http"]']

        urls_found = []
        for selector in selectors:
            links = soup.select(selector)
            for link in links[:5]:  # Top 5 resultados
                url = (
                    link.get_text(strip=True)
                    if selector == "a.result__url"
                    else link.get("href")
                )
                if url and url.startswith("http"):
                    urls_found.append(url)

        return urls_found

    except Exception as e:
        logger.error(f"Error en DuckDuckGo: {e}")
        return []


def search_bing(query):
    """Búsqueda en Bing mediante scraping."""
    try:
        search_url = f"https://www.bing.com/search?q={quote_plus(query)}"
        headers = get_random_headers()
        headers["Accept-Language"] = "es-AR,es;q=0.9"

        response = robust_request(SESSIONS["bing"], search_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        urls_found = []
        # Selectores específicos de Bing
        links = soup.select('h2 a[href^="http"], .b_algo h2 a, cite')

        for link in links[:5]:
            url = link.get("href") or link.get_text(strip=True)
            if url and url.startswith("http") and "bing.com" not in url:
                urls_found.append(url)

        return urls_found

    except Exception as e:
        logger.error(f"Error en Bing: {e}")
        return []


def search_startpage(query):
    """Búsqueda en Startpage."""
    try:
        search_url = f"https://www.startpage.com/sp/search?query={quote_plus(query)}"
        headers = get_random_headers()

        response = robust_request(SESSIONS["startpage"], search_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        urls_found = []
        links = soup.select(".w-gl__result-url, .result-link, a.result-url")

        for link in links[:5]:
            url = link.get("href") or link.get_text(strip=True)
            if url and url.startswith("http"):
                urls_found.append(url)

        return urls_found

    except Exception as e:
        logger.error(f"Error en Startpage: {e}")
        return []


def search_yandex(query):
    """Búsqueda en Yandex (sin JavaScript)."""
    try:
        search_url = f"https://yandex.com/search/?text={quote_plus(query)}&lr=2"
        headers = get_random_headers()

        response = robust_request(SESSIONS["yandex"], search_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        urls_found = []
        links = soup.select('.organic__url, .path__item, .organic a[href^="http"]')

        for link in links[:5]:
            url = link.get("href") or link.get_text(strip=True)
            if url and url.startswith("http") and "yandex" not in url:
                urls_found.append(url)

        return urls_found

    except Exception as e:
        logger.error(f"Error en Yandex: {e}")
        return []


def search_business_directories(company_name, location=None):
    """Búsqueda en directorios de empresas argentinos."""
    urls_found = []

    for directory in ARGENTINA_DIRECTORIES:
        try:
            # Construir parámetros de búsqueda
            params = {}
            for key, template in directory["params"].items():
                if "{query}" in template:
                    params[key] = template.format(query=company_name)
                elif "{location}" in template and location:
                    params[key] = template.format(location=location)

            headers = get_random_headers()
            response = robust_request(
                SESSIONS["directories"],
                directory["url"],
                headers=headers,
                params=params,
            )

            soup = BeautifulSoup(response.text, "html.parser")
            links = soup.select(directory["result_selector"])

            for link in links[:3]:  # Top 3 por directorio
                url = link.get(directory["link_attr"])
                if url:
                    # Convertir URL relativa a absoluta
                    if not url.startswith("http"):
                        base_url = f"https://{urlparse(directory['url']).netloc}"
                        url = urljoin(base_url, url)
                    urls_found.append(url)

            logger.info(
                f"Directorio {directory['name']}: {len([u for u in urls_found if u])} URLs encontradas"
            )
            time.sleep(random.uniform(1, 2))  # Rate limiting cortés

        except Exception as e:
            logger.error(f"Error en directorio {directory['name']}: {e}")
            continue

    return urls_found


def search_by_cuit(cuit):
    """Búsqueda específica por CUIT en fuentes conocidas."""
    urls_found = []

    # Fuentes específicas de CUIT
    sources = [
        f"https://www.cuitonline.com/detalle/{cuit}/",
        f"https://www.dateas.com/cuit/{cuit}",
    ]

    for source_url in sources:
        try:
            headers = get_random_headers()
            response = robust_request(
                SESSIONS["directories"], source_url, headers=headers
            )
            soup = BeautifulSoup(response.text, "html.parser")

            # Buscar enlaces a sitios web en la página del CUIT
            web_links = soup.find_all(
                "a", href=re.compile(r"^https?://(?!.*(?:cuitonline|dateas))")
            )
            for link in web_links[:2]:
                url = link.get("href")
                if url and not any(
                    bl in extract_domain(url) for bl in BLACKLISTED_DOMAINS
                ):
                    urls_found.append(url)

        except Exception as e:
            logger.error(f"Error buscando por CUIT en {source_url}: {e}")
            continue

    return urls_found


def get_web_multi_engine(query, location=None, cuit=None):
    """Motor principal de búsqueda multi-engine con fallback inteligente."""
    logger.info(f"Iniciando búsqueda multi-engine para: {query}")

    # Verificar cache primero
    cache_key = get_cache_key(query, location)
    cached_result = get_cached_result(cache_key)
    if cached_result:
        return cached_result

    all_urls = []
    scored_urls = {}

    # Generar queries inteligentes
    queries = generate_smart_queries(query, location, cuit)
    logger.info(f"Generadas {len(queries)} variaciones de consulta")

    # FASE 1: Búsquedas en motores principales
    search_engines = [
        ("DuckDuckGo", search_duckduckgo),
        ("Bing", search_bing),
        ("Startpage", search_startpage),
        ("Yandex", search_yandex),
    ]

    for engine_name, engine_func in search_engines:
        for query_variant in queries[:3]:  # Top 3 variantes por motor
            try:
                logger.info(f"Buscando en {engine_name}: '{query_variant}'")
                urls = engine_func(query_variant)
                all_urls.extend(urls)

                # Pequeña pausa entre queries
                time.sleep(random.uniform(1, 2))

            except Exception as e:
                logger.error(f"Error en {engine_name}: {e}")
                continue

    # FASE 2: Búsqueda en directorios argentinos
    logger.info("Buscando en directorios argentinos...")
    directory_urls = search_business_directories(query, location)
    all_urls.extend(directory_urls)

    # FASE 3: Búsqueda por CUIT si está disponible
    if cuit:
        logger.info(f"Buscando por CUIT: {cuit}")
        cuit_urls = search_by_cuit(cuit)
        all_urls.extend(cuit_urls)

    # FASE 4: Scoring y selección de mejor URL
    logger.info(f"Analizando {len(all_urls)} URLs encontradas...")

    for url in all_urls:
        if url and url.startswith("http"):
            domain = extract_domain(url)
            if domain not in scored_urls:  # Evitar duplicados por dominio
                score = score_url_relevance(url, query, location)
                scored_urls[domain] = {"url": url, "score": score}

    if not scored_urls:
        logger.warning("No se encontraron URLs válidas")
        save_to_cache(cache_key, None)
        return None

    # Ordenar por score y retornar la mejor
    best_result = max(scored_urls.values(), key=lambda x: x["score"])
    best_url = best_result["url"]
    best_score = best_result["score"]

    logger.info(f"Mejor URL encontrada: {best_url} (score: {best_score})")

    # Solo retornar si el score es razonable (> 5)
    result = best_url if best_score > 5 else None
    save_to_cache(cache_key, result)

    return result


# === FUNCIONES ORIGINALES MEJORADAS ===


def get_razon_social(cuit):
    """Intenta obtener la Razón Social desde CuitOnline - MEJORADO."""
    print("    -> [Gratis] Buscando Razón Social...")
    try:
        url = f"https://www.cuitonline.com/detalle/{cuit}/"
        headers = get_random_headers()
        response = robust_request(SESSIONS["directories"], url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # Múltiples selectores para mayor robustez
        selectors = ["h1.denominacion", ".denominacion", "h1", ".company-name"]
        for selector in selectors:
            header = soup.select_one(selector)
            if header:
                razon_social = header.get_text(strip=True)
                if razon_social and len(razon_social) > 3:
                    return razon_social

        return None
    except Exception as e:
        logger.error(f"Error al scrapear CuitOnline: {e}")
        return None


def get_web(query, location=None, cuit=None):
    """Función principal mejorada para obtener URL del sitio web."""
    print("    -> [Gratis] Buscando URL del sitio web...")
    return get_web_multi_engine(query, location, cuit)


def validate_email(email):
    """Valida formato de email."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_phone(phone):
    """Valida números de teléfono argentinos."""
    if not phone:
        return False
    clean_phone = re.sub(r"[^\d+]", "", phone)
    # Números argentinos: +54 + código área + número (mín 8 dígitos total)
    return len(clean_phone) >= 8 and (
        clean_phone.startswith("+54") or len(clean_phone) >= 8
    )


def get_contactos_from_web(url):
    """Extrae emails y teléfonos de una URL dada - MEJORADO."""
    if not url:
        return {}

    print(f"    -> [Gratis] Scrapeando contactos desde: {url}")
    try:
        headers = get_random_headers()
        response = robust_request(SESSIONS["directories"], url, headers=headers)

        # Parsear tanto HTML como texto plano
        soup = BeautifulSoup(response.text, "html.parser")

        # Remover scripts y estilos
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text()

        # Patrones mejorados para Argentina
        email_pattern = r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"
        phone_patterns = [
            r"\+?54\s?9?\s?\d{2,4}\s?\d{3,4}[-\s]?\d{4}",  # Formato argentino completo
            r"\(\+?54\)\s?\d{2,4}\s?\d{3,4}[-\s]?\d{4}",  # Con paréntesis
            r"\b\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4}\b",  # Formato local
            r"\(\d{3,4}\)\s?\d{3,4}[-\s]?\d{4}",  # Con código de área
        ]

        # Buscar emails
        emails = re.findall(email_pattern, text, re.IGNORECASE)
        valid_emails = [email.lower() for email in emails if validate_email(email)]

        # Buscar teléfonos
        all_phones = []
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            all_phones.extend(phones)

        # Limpiar y validar teléfonos
        valid_phones = []
        for phone in all_phones:
            clean_phone = re.sub(r"[^\d+()]", " ", phone).strip()
            if validate_phone(clean_phone):
                valid_phones.append(clean_phone)

        # Preparar resultado
        data = {}
        if valid_emails:
            # Priorizar emails corporativos
            corporate_emails = [
                e
                for e in valid_emails
                if not any(
                    provider in e
                    for provider in ["gmail", "yahoo", "hotmail", "outlook"]
                )
            ]
            data["EMAIL"] = corporate_emails[0] if corporate_emails else valid_emails[0]

        # Agregar hasta 3 teléfonos únicos
        unique_phones = list(dict.fromkeys(valid_phones))  # Remover duplicados
        for i, phone in enumerate(unique_phones[:3]):
            key = "TELEFONO" if i == 0 else f"TELEFONO_{i+1}"
            data[key] = phone

        if data:
            logger.info(f"Contactos extraídos: {len(data)} campos")

        return data

    except Exception as e:
        logger.error(f"Error al scrapear contactos: {e}")
        return {}


def get_maps_data(query, location=None):
    """Intenta obtener datos de Google Maps - MEJORADO."""
    print("    -> [Gratis] Buscando datos de Google Maps...")
    try:
        # Construir query más específica
        full_query = f"{query} {location}" if location else query
        search_url = f"https://www.google.com/maps/search/{quote_plus(full_query)}"

        headers = get_random_headers()
        response = robust_request(SESSIONS["directories"], search_url, headers=headers)

        final_url = response.url

        # Múltiples patrones para coordenadas
        coord_patterns = [
            r"/@(-?\d+\.\d+),(-?\d+\.\d+),(\d+(?:\.\d+)?z)",
            r"/@(-?\d+\.\d+),(-?\d+\.\d+)",
            r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)",
        ]

        for pattern in coord_patterns:
            coords_match = re.search(pattern, final_url)
            if coords_match:
                if len(coords_match.groups()) >= 2:
                    lat, lon = coords_match.groups()[:2]
                    try:
                        lat_float = float(lat)
                        lon_float = float(lon)

                        # Verificar que las coordenadas están en Argentina (aproximadamente)
                        if -55 <= lat_float <= -21 and -74 <= lon_float <= -53:
                            logger.info(
                                "Coordenadas argentinas encontradas por scraping"
                            )
                            return {
                                "LATITUD": lat_float,
                                "LONGITUD": lon_float,
                                "URL_Gmaps": final_url,
                            }
                    except ValueError:
                        continue

        logger.warning("No se encontraron coordenadas válidas en Google Maps")
        return {}

    except Exception as e:
        logger.error(f"Error al scrapear Google Maps: {e}")
        return {}


# === FUNCIÓN DE LIMPIEZA DE CACHE ===
def clean_old_cache():
    """Limpia entradas de cache más antiguas a 7 días."""
    try:
        with open("cache.json", "r", encoding="utf-8") as f:
            cache = json.load(f)

        current_time = time.time()
        cleaned_cache = {}

        for key, value in cache.items():
            if isinstance(value, dict) and "timestamp" in value:
                if current_time - value["timestamp"] < 604800:  # 7 días
                    cleaned_cache[key] = value

        with open("cache.json", "w", encoding="utf-8") as f:
            json.dump(cleaned_cache, f, indent=2, ensure_ascii=False)

        logger.info(
            f"Cache limpiado: {len(cache) - len(cleaned_cache)} entradas eliminadas"
        )

    except Exception as e:
        logger.error(f"Error limpiando cache: {e}")


# Limpiar cache automáticamente al importar el módulo
clean_old_cache()
