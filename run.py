# run.py
import sys
from services import google_sheets
from core import enricher


def main():
    """Punto de entrada interactivo para el usuario."""
    print("--- Bienvenido Automatization Search ---")

    client = google_sheets.get_gspread_client()
    if not client:
        sys.exit(1)  # Termina el programa si no se puede conectar

    worksheets = google_sheets.get_all_worksheets(client)
    if not worksheets:
        print(
            "No se encontraron hojas en el documento. Asegúrate de que el nombre es correcto."
        )
        sys.exit(1)

    # Paso 1: Listar y elegir hoja
    print("\nHojas de cálculo disponibles:")
    for i, ws in enumerate(worksheets):
        print(f"  {i + 1}: {ws.title}")

    try:
        choice = int(input("Por favor, elige el número de la hoja a procesar: ")) - 1
        if not 0 <= choice < len(worksheets):
            print("Selección inválida.")
            sys.exit(1)
        selected_ws = worksheets[choice]
    except ValueError:
        print("Entrada inválida. Debes introducir un número.")
        sys.exit(1)

    # Paso 2: Analizar la hoja
    print(f"\nAnalizando '{selected_ws.title}'...")
    stats = google_sheets.analyze_worksheet(selected_ws)
    if not stats or stats["pending"] == 0:
        print("No hay empresas pendientes de búsqueda en esta hoja.")
        sys.exit(0)

    print(f"- Total de empresas: {stats['total']}")
    print(f"- Empresas completadas: {stats['completed']}")
    print(f"- Empresas pendientes: {stats['pending']}")

    # Paso 3: Decidir cuántas procesar
    try:
        limit_input = input(
            f"\n¿Cuántas de las {stats['pending']} empresas pendientes quieres procesar? (Presiona Enter para procesar todas): "
        )
        limit = int(limit_input) if limit_input else stats["pending"]
        if limit > stats["pending"]:
            limit = stats["pending"]
    except ValueError:
        print("Entrada inválida. Se procesarán todas las pendientes.")
        limit = stats["pending"]

    # Paso 4: Confirmar y ejecutar
    confirm = input(
        f"\nSe procesarán {limit} empresas de la hoja '{selected_ws.title}'. ¿Continuar? (s/n): "
    )
    if confirm.lower() == "s":
        enricher.run_enrichment_process(selected_ws, limit)
        print("\n--- Proceso finalizado. ---")
    else:
        print("Proceso cancelado por el usuario.")


if __name__ == "__main__":
    main()
