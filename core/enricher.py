# core/enricher.py - MOTOR MEJORADO (SOLO BÚSQUEDA GRATUITA)
import time
import logging
import pandas as pd
from services import google_sheets, free_search

# IMPORTANTE: NO importamos pay_search - Solo búsqueda gratuita
from config.config import CRITICAL_DATA, RATE_LIMIT_CONFIG

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def evaluate_completeness(profile):
    """Evalúa qué tan completo está un perfil de empresa."""
    missing_critical = [key for key in CRITICAL_DATA if not profile.get(key)]
    completeness_score = (
        (len(CRITICAL_DATA) - len(missing_critical)) / len(CRITICAL_DATA) * 100
    )

    return {
        "missing_critical": missing_critical,
        "completeness_score": completeness_score,
        "is_complete": completeness_score >= 80,  # 80% completitud mínima
    }


def extract_location_from_profile(profile):
    """Extrae información de localización del perfil para mejorar búsquedas."""
    location_fields = ["LOCALIDAD", "CIUDAD", "PROVINCIA", "DIRECCION"]
    location_parts = []

    for field in location_fields:
        value = profile.get(field)
        if value and isinstance(value, str) and len(value.strip()) > 2:
            location_parts.append(value.strip())

    return " ".join(location_parts) if location_parts else None


def enrich_single_company(profile, row_number):
    """
    Enriquece una sola empresa con lógica mejorada y fallbacks inteligentes.
    """
    logger.info(f"=== Procesando empresa en fila {row_number} ===")

    # Extraer datos base para búsqueda
    company_name = profile.get("NOMBRE_ESTABLECIMIENTO") or profile.get(
        "NOMBRE_COMERCIAL"
    )
    cuit = profile.get("CUIT")
    location = extract_location_from_profile(profile)

    if not company_name and not cuit:
        logger.warning(f"Fila {row_number}: Sin nombre ni CUIT para buscar")
        return profile

    # Evaluar estado inicial
    initial_eval = evaluate_completeness(profile)
    logger.info(f"Estado inicial: {initial_eval['completeness_score']:.1f}% completo")

    if initial_eval["is_complete"]:
        logger.info("Empresa ya está completa, saltando...")
        return profile

    # === FASE 1: BÚSQUEDA DE RAZÓN SOCIAL ===
    if not company_name and cuit:
        logger.info("FASE 1: Buscando razón social por CUIT...")
        razon_social = free_search.get_razon_social(cuit)
        if razon_social:
            profile["NOMBRE_ESTABLECIMIENTO"] = razon_social
            company_name = razon_social
            logger.info(f"✓ Razón social encontrada: {razon_social}")
        else:
            logger.warning("✗ No se encontró razón social")

    # === FASE 2: BÚSQUEDA DE SITIO WEB ===
    if not profile.get("WEB") and company_name:
        logger.info("FASE 2: Buscando sitio web...")
        web_url = free_search.get_web(company_name, location, cuit)
        if web_url:
            profile["WEB"] = web_url
            logger.info(f"✓ Sitio web encontrado: {web_url}")
        else:
            logger.warning("✗ No se encontró sitio web")

    # === FASE 3: SCRAPING DE CONTACTOS ===
    if profile.get("WEB") and not all(
        profile.get(field) for field in ["EMAIL", "TELEFONO"]
    ):
        logger.info("FASE 3: Extrayendo contactos del sitio web...")
        contactos = free_search.get_contactos_from_web(profile["WEB"])

        # Actualizar solo campos faltantes
        for key, value in contactos.items():
            if value and not profile.get(key):
                profile[key] = value
                logger.info(f"✓ {key}: {value}")

    # === FASE 4: DATOS DE GEOLOCALIZACIÓN ===
    if not all(profile.get(field) for field in ["LATITUD", "LONGITUD"]):
        logger.info("FASE 4: Buscando datos de geolocalización...")

        # Usar la query más específica posible
        search_query = company_name
        if location:
            search_query = f"{company_name} {location}"

        maps_data = free_search.get_maps_data(search_query, location)

        # Actualizar solo campos faltantes
        for key, value in maps_data.items():
            if value and not profile.get(key):
                profile[key] = value
                logger.info(f"✓ {key}: {value}")

    # === EVALUACIÓN FINAL ===
    final_eval = evaluate_completeness(profile)
    improvement = final_eval["completeness_score"] - initial_eval["completeness_score"]

    logger.info(
        f"Estado final: {final_eval['completeness_score']:.1f}% completo (+{improvement:.1f}%)"
    )
    if final_eval["missing_critical"]:
        logger.info(f"Datos faltantes: {', '.join(final_eval['missing_critical'])}")

    # === MARCADO DE ESTADO INTELIGENTE ===
    # Solo marcar como COMPLETADO si realmente está completo O si ya se hizo máximo esfuerzo
    if final_eval["is_complete"]:
        profile["ESTADO_BUSQUEDA"] = "COMPLETADO"
        profile["COMPLETITUD_SCORE"] = final_eval["completeness_score"]
    elif improvement > 0:
        profile["ESTADO_BUSQUEDA"] = "PARCIAL"
        profile["COMPLETITUD_SCORE"] = final_eval["completeness_score"]
    else:
        profile["ESTADO_BUSQUEDA"] = "SIN_DATOS"
        profile["COMPLETITUD_SCORE"] = final_eval["completeness_score"]

    return profile


def run_enrichment_process(worksheet, limit):
    """
    Orquesta todo el proceso de enriquecimiento con la lógica mejorada.
    """
    logger.info("=== INICIANDO PROCESO DE ENRIQUECIMIENTO ===")

    # Leer datos pendientes
    companies_df = google_sheets.read_pending_data(worksheet, limit)
    if companies_df.empty:
        logger.info("No hay empresas pendientes para procesar en la selección.")
        return

    total_companies = len(companies_df)
    logger.info(f"Procesando {total_companies} empresas...")

    all_results = []
    successful_enrichments = 0
    partial_enrichments = 0
    failed_enrichments = 0

    for index, row in companies_df.iterrows():
        try:
            profile = row.to_dict()
            row_number = profile.get("sheet_row_number", index + 2)

            logger.info(f"\n--- Empresa {index + 1}/{total_companies} ---")

            # Enriquecer empresa individual
            enriched_profile = enrich_single_company(profile, row_number)

            # Clasificar resultado
            estado = enriched_profile.get("ESTADO_BUSQUEDA", "SIN_DATOS")
            if estado == "COMPLETADO":
                successful_enrichments += 1
            elif estado == "PARCIAL":
                partial_enrichments += 1
            else:
                failed_enrichments += 1

            all_results.append(enriched_profile)

            # Rate limiting cortés
            delay = RATE_LIMIT_CONFIG.get("min_delay", 1)
            logger.info(f"Esperando {delay}s antes de continuar...")
            time.sleep(delay)

        except KeyboardInterrupt:
            logger.info("Proceso interrumpido por el usuario.")
            break
        except Exception as e:
            logger.error(f"Error procesando empresa en fila {row_number}: {e}")
            # Agregar perfil sin cambios en caso de error
            profile["ESTADO_BUSQUEDA"] = "ERROR"
            profile["ERROR_MESSAGE"] = str(e)
            all_results.append(profile)
            failed_enrichments += 1
            continue

    # === RESUMEN FINAL ===
    processed_count = len(all_results)
    logger.info("\n=== RESUMEN FINAL ===")
    logger.info(f"Empresas procesadas: {processed_count}")
    logger.info(f"Exitosas (completas): {successful_enrichments}")
    logger.info(f"Parciales: {partial_enrichments}")
    logger.info(f"Fallidas: {failed_enrichments}")

    if successful_enrichments > 0:
        success_rate = (successful_enrichments / processed_count) * 100
        logger.info(f"Tasa de éxito: {success_rate:.1f}%")

    # === ACTUALIZAR GOOGLE SHEETS ===
    if all_results:
        logger.info("Actualizando Google Sheets...")
        results_df = pd.DataFrame(all_results)
        google_sheets.write_results_to_sheet(worksheet, results_df)

        # Estadísticas adicionales para el usuario
        print("\n🎯 PROCESO COMPLETADO:")
        print(f"   ✅ Completadas: {successful_enrichments}")
        print(f"   🔄 Parciales: {partial_enrichments}")
        print(f"   ❌ Fallidas: {failed_enrichments}")
        print(f"   📊 Total procesadas: {processed_count}")

        if successful_enrichments > 0:
            print(f"   🎉 Tasa de éxito: {success_rate:.1f}%")

    logger.info("=== PROCESO DE ENRIQUECIMIENTO FINALIZADO ===")


def analyze_enrichment_potential(worksheet):
    """
    Analiza el potencial de enriquecimiento de una hoja antes de procesarla.
    """
    try:
        companies_df = google_sheets.read_pending_data(worksheet, limit=None)
        if companies_df.empty:
            return {"error": "No hay datos para analizar"}

        analysis = {
            "total_pending": len(companies_df),
            "with_name": 0,
            "with_cuit": 0,
            "with_location": 0,
            "with_web": 0,
            "completely_empty": 0,
            "enrichment_potential": "bajo",
        }

        for _, row in companies_df.iterrows():
            profile = row.to_dict()

            if profile.get("NOMBRE_ESTABLECIMIENTO") or profile.get("NOMBRE_COMERCIAL"):
                analysis["with_name"] += 1

            if profile.get("CUIT"):
                analysis["with_cuit"] += 1

            location_fields = ["LOCALIDAD", "CIUDAD", "PROVINCIA", "DIRECCION"]
            if any(profile.get(field) for field in location_fields):
                analysis["with_location"] += 1

            if profile.get("WEB"):
                analysis["with_web"] += 1

            # Contar completamente vacías
            essential_fields = ["NOMBRE_ESTABLECIMIENTO", "NOMBRE_COMERCIAL", "CUIT"]
            if not any(profile.get(field) for field in essential_fields):
                analysis["completely_empty"] += 1

        # Calcular potencial de enriquecimiento
        searchable = analysis["with_name"] + analysis["with_cuit"]
        if searchable > analysis["total_pending"] * 0.8:
            analysis["enrichment_potential"] = "alto"
        elif searchable > analysis["total_pending"] * 0.5:
            analysis["enrichment_potential"] = "medio"

        return analysis

    except Exception as e:
        logger.error(f"Error analizando potencial de enriquecimiento: {e}")
        return {"error": str(e)}
