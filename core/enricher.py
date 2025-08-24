# core/enricher.py
import time
import pandas as pd
from services import google_sheets, free_search, pay_search
from config.config import CRITICAL_DATA


def run_enrichment_process(worksheet, limit):
    """
    Orquesta todo el proceso de enriquecimiento para una hoja y un límite dados.
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

        if profile.get("WEB") and not profile.get("EMAIL"):
            profile.update(free_search.get_contactos_from_web(profile["WEB"]))

        if not profile.get("LATITUD"):
            profile.update(free_search.get_maps_data(query_name))

        # --- FASE 2: ENRIQUECIMIENTO CON APIS ---
        missing_data = [key for key in CRITICAL_DATA if not profile.get(key)]

        if missing_data:
            print(f"  -> Faltan datos críticos: {missing_data}. Iniciando Fase 2...")

            if any(k in missing_data for k in ["LATITUD", "TELEFONO", "DIRECCION"]):
                places_data = pay_search.get_data_with_places(query_name)
                for key, value in places_data.items():
                    if not profile.get(key):
                        profile[key] = value

            missing_data = [key for key in CRITICAL_DATA if not profile.get(key)]

            if "WEB" in missing_data:
                gemini_res = pay_search.get_data_with_gemini(query_name, ["WEB"])
                if gemini_res and gemini_res.get("WEB"):
                    profile["WEB"] = gemini_res["WEB"]

            if not profile.get("WEB"):
                profile["WEB"] = pay_search.get_web_with_custom_search(query_name)

        all_results.append(profile)
        time.sleep(2)

    if all_results:
        results_df = pd.DataFrame(all_results)
        google_sheets.write_results_to_sheet(worksheet, results_df)
