# services/google_sheets.py
import gspread
import pandas as pd
import datetime
from config.config import SHEET_NAME


def get_gspread_client():
    """Autentica y devuelve el cliente principal de gspread."""
    try:
        return gspread.service_account(filename="credentials.json")
    except Exception as e:
        print(f"ERROR al conectar con Google Sheets (credentials.json): {e}")
        return None


def get_all_worksheets(client):
    """Obtiene y devuelve una lista de todas las hojas en el documento."""
    if not client:
        return []
    try:
        spreadsheet = client.open(SHEET_NAME)
        return spreadsheet.worksheets()
    except Exception as e:
        print(f"ERROR al abrir el documento '{SHEET_NAME}': {e}")
        return []


def analyze_worksheet(worksheet):
    """Analiza una hoja de cálculo y devuelve un resumen de su estado."""
    try:
        all_data = worksheet.get_all_records()
        if not all_data:
            return {"total": 0, "completed": 0, "pending": 0}

        df = pd.DataFrame(all_data)
        total_rows = len(df)

        if "ESTADO" in df.columns:
            df["ESTADO"] = df["ESTADO"].fillna("").str.upper()
            completed_rows = len(df[df["ESTADO"] == "COMPLETADO"])
        else:
            completed_rows = 0

        return {
            "total": total_rows,
            "completed": completed_rows,
            "pending": total_rows - completed_rows,
        }
    except Exception as e:
        print(f"Ocurrió un error al analizar la hoja '{worksheet.title}': {e}")
        return None


def read_pending_data(worksheet, limit):
    """Lee los datos pendientes de una hoja y los devuelve como un DataFrame."""
    try:
        all_data = worksheet.get_all_records()
        df = pd.DataFrame(all_data)
        df["sheet_row_number"] = df.index + 2

        if "ESTADO" not in df.columns:
            df["ESTADO"] = "PENDIENTE"

        df["ESTADO"] = df["ESTADO"].fillna("").str.upper()
        pending_companies = df[df["ESTADO"] != "COMPLETADO"].copy()

        return pending_companies.head(limit)
    except Exception as e:
        print(f"Ocurrió un error al leer los datos de la hoja: {e}")
        return pd.DataFrame()


def write_results_to_sheet(worksheet, results_df):
    """Toma un DataFrame con los resultados y actualiza la hoja en un solo lote."""
    if results_df.empty:
        return
    print("\nActualizando Google Sheet con los resultados...")
    try:
        headers = worksheet.row_values(1)
        col_map = {header: i + 1 for i, header in enumerate(headers)}

        cells_to_update = []
        current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for _, row in results_df.iterrows():
            sheet_row_index = int(row["sheet_row_number"])

            for col_name, value in row.items():
                if pd.notna(value) and col_name in col_map:
                    cells_to_update.append(
                        gspread.Cell(
                            row=sheet_row_index, col=col_map[col_name], value=str(value)
                        )
                    )

            cells_to_update.append(
                gspread.Cell(
                    row=sheet_row_index, col=col_map["ESTADO"], value="COMPLETADO"
                )
            )
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
