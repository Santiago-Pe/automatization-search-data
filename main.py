# main.py
import time
import pandas as pd
from sheets_handler import read_input_data, write_results_to_sheet
from search_services import search_web_fallback, search_google_maps
from scraper import scrape_contact_info
from config import PROCESSING_LIMIT


def main():
    """
    Función principal que orquesta todo el proceso de enriquecimiento.
    """
    print("\n--- Inicio del Proceso de Enriquecimiento ---")
    start_time = time.time()

    companies_df = read_input_data()

    if companies_df.empty:
        print("\n[RESULTADO] No se encontraron empresas pendientes.")
        return

    # Aplicamos el límite de procesamiento desde config.py
    companies_to_process = companies_df.head(PROCESSING_LIMIT)
    print(
        f"Aplicando límite: se procesarán un máximo de {len(companies_to_process)} filas."
    )

    final_results = []
    for index, row in companies_to_process.iterrows():
        # Usamos .get() para evitar errores si las columnas no existen
        company_name = row.get("NOMBRE_ESTABLECIMIENTO") or row.get("NOMBRE_COMERCIAL")
        pais = row.get("PAIS", "Argentina")  # Usamos "Argentina" por defecto

        if not company_name:
            print(
                f"\n[!] Saltando Fila: {row['sheet_row_number']} (sin nombre de empresa)"
            )
            continue

        search_query = f"{company_name} {pais}".strip()
        print(f"\n[+] Procesando: '{search_query}' (Fila: {row['sheet_row_number']})")

        # --- Lógica de Búsqueda Multi-Capa ---
        maps_data = search_google_maps(search_query)

        # Si Maps no dio una URL, usar el fallback de la búsqueda web.
        if not maps_data.get("WEB"):
            maps_data["WEB"] = search_web_fallback(search_query)

        # Analizamos la URL para buscar más datos.
        scraped_email, scraped_phone = scrape_contact_info(maps_data.get("WEB"))

        # --- Consolidación de Resultados ---
        # Creamos un diccionario que coincide con nuestras columnas
        result_data = {
            "sheet_row_number": row["sheet_row_number"],
            "WEB": maps_data.get("WEB"),
            "EMAIL": scraped_email,
            "URL_Gmaps": maps_data.get("URL_Gmaps"),
            "LATITUD": maps_data.get("LATITUD"),
            "LONGITUD": maps_data.get("LONGITUD"),
        }

        # Lógica para asignar múltiples teléfonos
        phone_list = maps_data.get("TELEFONOS", [])
        if scraped_phone and scraped_phone not in phone_list:
            phone_list.append(scraped_phone)

        if len(phone_list) > 0:
            result_data["TELEFONO"] = phone_list[0]
        if len(phone_list) > 1:
            result_data["TELEFONO_2"] = phone_list[1]
        if len(phone_list) > 2:
            result_data["TELEFONO_3"] = phone_list[2]

        final_results.append(result_data)
        time.sleep(1)

    if final_results:
        results_df = pd.DataFrame(final_results)
        write_results_to_sheet(results_df)

    end_time = time.time()
    total_time = end_time - start_time
    print(f"\n--- Proceso completado en {total_time:.2f} segundos. ---")


if __name__ == "__main__":
    main()
