# sheets_handler.py
import gspread
import pandas as pd
import datetime
from config import SHEET_NAME, SHEET_INDEX, COLUMNS


# ===================================================================
# FUNCIONES DE CONEXIÓN
# ===================================================================
def setup_google_sheets_client():
    """Autentica y devuelve un objeto de la hoja de cálculo específica."""
    try:
        gc = gspread.service_account(filename="credentials.json")
        spreadsheet = gc.open(SHEET_NAME)
        # Seleccionamos la hoja por su índice (posición) desde config.py
        worksheet = spreadsheet.get_worksheet(SHEET_INDEX)
        print(f"Trabajando con la hoja: '{worksheet.title}' (Índice: {SHEET_INDEX})")
        return worksheet
    except Exception as e:
        print(f"ERROR al conectar con Google Sheets: {e}")
        return None


# ===================================================================
# FUNCIONES DE LECTURA
# ===================================================================
def read_input_data():
    """Lee los datos, añade el número de fila y devuelve las empresas pendientes."""
    worksheet = setup_google_sheets_client()
    if worksheet is None:
        return pd.DataFrame()

    try:
        print("Leyendo datos desde Google Sheets...")
        all_data = worksheet.get_all_records()
        if not all_data:
            print("La hoja de cálculo parece estar vacía.")
            return pd.DataFrame()

        df = pd.DataFrame(all_data)
        df["sheet_row_number"] = df.index + 2

        # Estandarizamos el manejo del estado
        if "ESTADO" not in df.columns:
            df["ESTADO"] = "PENDIENTE"

        df["ESTADO"] = df["ESTADO"].fillna("").str.upper()
        pending_companies = df[df["ESTADO"] != "COMPLETADO"].copy()

        print(f"Se encontraron {len(pending_companies)} empresas pendientes en total.")
        return pending_companies
    except Exception as e:
        print(f"Ocurrió un error al leer los datos de la hoja: {e}")
        return pd.DataFrame()


# ===================================================================
# FUNCIÓN DE ESCRITURA
# ===================================================================
def write_results_to_sheet(results_df):
    """Toma un DataFrame con los resultados y actualiza la hoja en un solo lote."""
    print("\nActualizando Google Sheet con los resultados...")
    worksheet = setup_google_sheets_client()
    if worksheet is None:
        return

    try:
        headers = worksheet.row_values(1)
        col_map = {header: i + 1 for i, header in enumerate(headers)}

        cells_to_update = []
        current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for _, row in results_df.iterrows():
            sheet_row_index = int(row["sheet_row_number"])

            # Iteramos sobre las columnas definidas en config.py para escribir los datos
            for col_name in COLUMNS:
                # Verificamos que el dato exista en nuestros resultados y que la columna exista en el Sheet
                if pd.notna(row.get(col_name)) and col_name in col_map:
                    cells_to_update.append(
                        gspread.Cell(
                            row=sheet_row_index,
                            col=col_map[col_name],
                            value=str(row[col_name]),
                        )
                    )

            # Actualizar estado y fecha siempre
            if "ESTADO" in col_map:
                cells_to_update.append(
                    gspread.Cell(
                        row=sheet_row_index, col=col_map["ESTADO"], value="COMPLETADO"
                    )
                )
            if "FECHA_ACTUALIZACION" in col_map:
                cells_to_update.append(
                    gspread.Cell(
                        row=sheet_row_index,
                        col=col_map["FECHA_ACTUALIZACION"],
                        value=current_date,
                    )
                )

        if cells_to_update:
            worksheet.update_cells(cells_to_update, value_input_option="USER_ENTERED")
            print(
                f"¡Google Sheet actualizado exitosamente! Se modificaron {len(results_df)} filas."
            )

    except Exception as e:
        print(f"Ocurrió un error al actualizar Google Sheets: {e}")
