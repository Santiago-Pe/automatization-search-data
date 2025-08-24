# core/enricher.py
import time
import pandas as pd
from services import google_sheets, free_search


def run_enrichment_process(worksheet, limit):
    """
    Orquesta todo el proceso de enriquecimiento con la lógica corregida.
    """
    companies_df = google_sheets.read_pending_data(worksheet, limit)
    if companies_df.empty:
        print("No hay empresas pendientes para procesar en la selección.")
        return

    print(f"Iniciando procesamiento para {len(companies_df)} empresas...")

    all_results = []
    for index, row in companies_df.iterrows():
        profile = row.to_dict()
        query_name = profile.get("NOMBRE_ESTABLECIMIENTO") or profile.get(
            "NOMBRE_COMERCIAL"
        )

        if not query_name:
            print(f"\n[!] Saltando Fila: {row['sheet_row_number']} (sin nombre)")
            continue

        print(f"\n[+] Procesando: '{query_name}' (Fila: {row['sheet_row_number']})")

        # --- FASE 1: BÚSQUEDA GRATUITA ---
        print("  -> Fase 1: Búsqueda Gratuita...")

        if not profile.get("NOMBRE_ESTABLECIMIENTO") and profile.get("CUIT"):
            profile["NOMBRE_ESTABLECIMIENTO"] = free_search.get_razon_social(
                profile["CUIT"]
            )
            query_name = profile["NOMBRE_ESTABLECIMIENTO"] or query_name

        if not profile.get("WEB"):
            profile["WEB"] = free_search.get_web(query_name)

        # Si encontramos una WEB en Fase 1, la scrapeamos AHORA.
        if profile.get("WEB") and not profile.get("EMAIL"):
            profile.update(free_search.get_contactos_from_web(profile["WEB"]))

        if not profile.get("LATITUD"):
            profile.update(free_search.get_maps_data(query_name))

        # --- FASE 2: ENRIQUECIMIENTO CON APIS ---
        # missing_data = [key for key in CRITICAL_DATA if not profile.get(key)]

        # if missing_data:
        #     print(f"  -> Faltan datos críticos: {missing_data}. Iniciando Fase 2...")

        #     # Prioridad 1: Places API
        #     if any(
        #         k in missing_data for k in ["LATITUD", "TELEFONO", "DIRECCION", "WEB"]
        #     ):
        #         places_data = pay_search.get_data_with_places(query_name)
        #         for key, value in places_data.items():
        #             if not profile.get(key):
        #                 profile[key] = value

        #         # ### CORRECCIÓN CLAVE ###
        #         # Si Places encontró una WEB y todavía no tenemos EMAIL, la scrapeamos.
        #         if profile.get("WEB") and not profile.get("EMAIL"):
        #             print(
        #                 "    -> URL encontrada con Places. Intentando scraping de contactos..."
        #             )
        #             profile.update(free_search.get_contactos_from_web(profile["WEB"]))

        #     missing_data = [key for key in CRITICAL_DATA if not profile.get(key)]

        #     # Prioridad 2: Gemini API
        #     if "WEB" in missing_data:
        #         gemini_res = pay_search.get_data_with_gemini(query_name, ["WEB"])
        #         if gemini_res and gemini_res.get("WEB"):
        #             profile["WEB"] = gemini_res["WEB"]
        #             # Si Gemini encontró una WEB y no tenemos EMAIL, la scrapeamos.
        #             if not profile.get("EMAIL"):
        #                 print(
        #                     "    -> URL encontrada con Gemini. Intentando scraping de contactos..."
        #                 )
        #                 profile.update(
        #                     free_search.get_contactos_from_web(profile["WEB"])
        #                 )

        #     # Prioridad 3: Custom Search API
        #     if not profile.get("WEB"):
        #         profile["WEB"] = pay_search.get_web_with_custom_search(query_name)
        #         # Si Custom Search encontró una WEB y no tenemos EMAIL, la scrapeamos.
        #         if profile.get("WEB") and not profile.get("EMAIL"):
        #             print(
        #                 "    -> URL encontrada con Custom Search. Intentando scraping de contactos..."
        #             )
        #             profile.update(free_search.get_contactos_from_web(profile["WEB"]))

        all_results.append(profile)
        time.sleep(2)

    if all_results:
        results_df = pd.DataFrame(all_results)
        google_sheets.write_results_to_sheet(worksheet, results_df)
