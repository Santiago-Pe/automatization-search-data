# main.py
import time
import pandas as pd
from sheets_handler import read_input_data, write_results_to_sheet
from search_services import (
    find_url_with_gemini,
    find_url_with_custom_search,
    get_places_data_fallback,
)
from scraper import scrape_website
from config import PROCESSING_LIMIT


def main():
    """
    Orquesta el proceso de enriquecimiento siguiendo la cascada de costo cero.
    """
    start_time = time.time()

    print("\n--- Inicio del Proceso de Enriquecimiento (Flujo Óptimo) ---")
    companies_df = read_input_data()

    if companies_df.empty:
        print("\n[RESULTADO] No se encontraron empresas pendientes.")
        return

    companies_to_process = companies_df.head(PROCESSING_LIMIT)
    print(
        f"Aplicando límite de procesamiento: se procesarán un máximo de {len(companies_to_process)} filas."
    )

    all_results = []
    for index, row in companies_to_process.iterrows():
        result_data = {"sheet_row_number": row["sheet_row_number"]}

        # ### CAMBIO: Leemos la columna PAIS para usarla en las búsquedas ###
        # Usamos .get() para evitar errores si la columna no existe o está vacía
        nombre = row.get("NOMBRE_ESTABLECIMIENTO") or row.get("NOMBRE_COMERCIAL")
        pais = row.get("PAIS", "Argentina")  # Usamos "Argentina" como valor por defecto

        # Priorizamos CUIT como la mejor llave de búsqueda si existe
        query = row.get("CUIT") or f"{nombre} {pais}"

        # Convert query to string and check if it's valid
        if not query or not str(query).strip():
            print(
                f"\n[!] Saltando Fila: {row['sheet_row_number']} (sin datos de entrada válidos)"
            )
            continue

        print(f"\n[+] Procesando: '{query}' (Fila: {row['sheet_row_number']})")

        # 2. Cascada para obtener la URL
        # Usamos la query construida para las búsquedas
        url = find_url_with_gemini(str(query))
        if not url:
            url = find_url_with_custom_search(str(query))

        # ### CAMBIO: Guardamos la URL encontrada en la columna WEB ###
        result_data["WEB"] = url

        # 3. Scrapeo del sitio web (si se encontró URL)
        scraped_data = scrape_website(url)
        result_data.update(scraped_data)

        # 4. Último recurso: Google Places
        if not result_data.get("TELEFONO") and not result_data.get("TELEFONO_2"):
            # Usamos la query más completa para Places
            places_query = f"{nombre} {row.get('LOCALIDAD', '')} {row.get('PROVINCIA', '')}".strip()
            places_data = get_places_data_fallback(places_query)
            for key, value in places_data.items():
                if key not in result_data or result_data[key] is None:
                    result_data[key] = value

        all_results.append(result_data)
        time.sleep(2)

    if all_results:
        results_df = pd.DataFrame(all_results)
        write_results_to_sheet(results_df)

    end_time = time.time()
    total_time = end_time - start_time
    print(f"\n--- Proceso completado en {total_time:.2f} segundos. ---")


if __name__ == "__main__":
    main()
