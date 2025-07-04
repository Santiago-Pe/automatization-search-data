# main.py
import time
import pandas as pd
from sheets_handler import read_input_data, write_results_to_sheet
from search_services import search_web_fallback, search_google_maps
from scraper import scrape_contact_info


def main():
    """
    Función principal que orquesta todo el proceso de principio a fin.
    """
    print("\n--- Inicio del Proceso de Enriquecimiento ---")

    # Llama a la función de lectura para obtener las empresas pendientes.
    companies_df = read_input_data()

    # Verifica si hay trabajo que hacer.
    if companies_df.empty:
        print(
            "\n[RESULTADO] No se encontraron empresas pendientes para procesar. Finalizando el programa."
        )
        return
    else:
        print(
            "\n[RESULTADO] Empresas pendientes encontradas. Iniciando el bucle de procesamiento..."
        )

    final_results = []
    # Mantenemos el modo de prueba procesando solo el primer elemento.
    # Para procesar todo, quita el `.head(1)`.
    for index, row in companies_df.iterrows():
        # Extrae los datos de la fila actual.
        company_name = row.get("nombre_establecimiento", "")
        country = row.get("pais", "")
        search_query = f"{company_name} {country}".strip()
        print(
            f"\n[+] Procesando empresa: '{company_name}' (Fila: {row['sheet_row_number']})"
        )

        # --- Lógica de Búsqueda Multi-Capa ---

        # Plan A: Buscar en Google Maps para obtener la máxima cantidad de datos estructurados.
        final_url, phone_list, final_maps_url, final_lat, final_lng = (
            search_google_maps(search_query)
        )

        # Plan B: Si Maps no dio una URL, usar el fallback de la búsqueda web.
        if not final_url:
            final_url = search_web_fallback(search_query)

        # Plan C: Si tenemos una URL (de cualquier fuente), la analizamos para buscar más datos.
        scraped_email, scraped_phone = scrape_contact_info(final_url)

        # --- Consolidación de Resultados ---
        final_email = scraped_email
        # Si la lista de teléfonos de Maps está vacía, usamos el del scraping como respaldo.
        if not phone_list and scraped_phone:
            phone_list.append(scraped_phone)

        print(
            f"  -> Resumen de Búsqueda: URL={final_url}, Email={final_email}, Teléfonos={phone_list}"
        )

        # Añadimos los resultados finales a una lista.
        final_results.append(
            {
                "sheet_row_number": row["sheet_row_number"],
                "url_final": final_url,
                "email_final": final_email,
                "phone_list": phone_list,
                "maps_url_final": final_maps_url,
                "lat_final": final_lat,
                "lng_final": final_lng,
            }
        )

        time.sleep(1)  # Pausa educada entre peticiones.

    # Si se procesaron empresas, se escriben los resultados.
    if final_results:
        results_df = pd.DataFrame(final_results)
        write_results_to_sheet(results_df)

    print("\n--- Proceso completado. ---")


if __name__ == "__main__":
    main()
