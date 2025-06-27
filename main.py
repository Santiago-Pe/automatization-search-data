# main.py
import time
import pandas as pd
from sheets_handler import leer_datos_de_entrada, escribir_resultados_en_sheet
from search_services import buscar_info_en_google_maps, buscar_url_oficial_fallback
from scraper import extraer_info_de_pagina

def main():
    """Función principal que orquesta todo el proceso de principio a fin."""
    print("\n--- Inicio del Proceso de Enriquecimiento ---")

    df_empresas = leer_datos_de_entrada()
    if df_empresas.empty:
        print("No hay empresas para procesar. Finalizando.")
        return

    resultados_finales = []
    # Mantenemos el modo de prueba para procesar solo 1 elemento.
    # Quita el .head(1) para procesar todo el archivo.
    for index, row in df_empresas.head(1).iterrows():
        nombre = row.get('nombre_establecimiento', '')
        pais = row.get('pais', '')
        query = f"{nombre} {pais}".strip()
        print(f"\n[+] Procesando empresa: '{nombre}' (Fila: {row['sheet_row_number']})")

        # Lógica de búsqueda multi-capa
        url_final, telefono_final = buscar_info_en_google_maps(query)
        if not url_final:
            url_final = buscar_url_oficial_fallback(query)

        email_scrapeado, telefono_scrapeado = extraer_info_de_pagina(url_final)

        # Consolidar resultados: priorizar datos de Maps, luego de scraping.
        email_final = email_scrapeado
        if not telefono_final:
            telefono_final = telefono_scrapeado

        print(f"  -> Resumen: URL={url_final}, Email={email_final}, Tel={telefono_final}")

        resultados_finales.append({
            'sheet_row_number': row['sheet_row_number'],
            'url_final': url_final,
            'email_final': email_final,
            'telefono_final': telefono_final
        })

        time.sleep(1) # Pausa educada

    if resultados_finales:
        df_resultados = pd.DataFrame(resultados_finales)
        escribir_resultados_en_sheet(df_resultados)

    print("\n--- Proceso completado. ---")

if __name__ == "__main__":
    main()
