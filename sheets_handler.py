# sheets_handler.py
import gspread
import pandas as pd
import datetime
from config import SHEET_NAME, SHEET_INDEX

# ===================================================================
# FUNCIONES DE CONEXIÓN Y LECTURA
# ===================================================================


def setup_google_sheets_client():
    """Autentica y devuelve un cliente para interactuar con Google Sheets."""
    try:
        gc = gspread.service_account(filename="credentials.json")
        spreadsheet = gc.open(SHEET_NAME)
        worksheet = spreadsheet.get_worksheet(SHEET_INDEX)
        print(f"Trabajando con la hoja: '{worksheet.title}' (Índice: {SHEET_INDEX})")
        return worksheet
    except Exception as e:
        print(f"ERROR al conectar con Google Sheets: {e}")
        return None


def read_input_data():
    """
    Lee los datos de Google Sheets y devuelve las empresas pendientes.
    """
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

        if "ESTADO" not in df.columns:
            df["ESTADO"] = "PENDIENTE"

        df["ESTADO"] = df["ESTADO"].fillna("").str.upper()
        pending_companies = df[df["ESTADO"] != "COMPLETADO"].copy()

        print(f"Se encontraron {len(pending_companies)} empresas pendientes en total.")
        return pending_companies

    except Exception as e:
        print(f"Ocurrió un error al leer o procesar los datos de la hoja: {e}")
        return pd.DataFrame()


# ===================================================================
# FUNCIÓN DE ESCRITURA
# ===================================================================


def write_results_to_sheet(results_df):
    """
    Toma un DataFrame con los resultados y actualiza la hoja de Google Sheets en un solo lote.
    """
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

            # ### CAMBIO: Se añade 'WEB' al mapeo de escritura ###
            key_to_col_name = {
                "WEB": "WEB",
                "EMAIL": "EMAIL",
                "TELEFONO": "TELEFONO",
                "TELEFONO_2": "TELEFONO_2",
                "TELEFONO_3": "TELEFONO_3",
                "URL_Gmaps": "URL_Gmaps",
                "LATITUD": "LATITUD",
                "LONGITUD": "LONGITUD",
                "NOMBRE_COMERCIAL": "NOMBRE_COMERCIAL",
                "DIRECCION": "DIRECCION",
            }

            for key, col_name in key_to_col_name.items():
                if pd.notna(row.get(key)) and col_name in col_map:
                    cells_to_update.append(
                        gspread.Cell(
                            row=sheet_row_index,
                            col=col_map[col_name],
                            value=str(row[key]),
                        )
                    )

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
