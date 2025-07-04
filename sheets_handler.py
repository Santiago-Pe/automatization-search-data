# sheets_handler.py
import gspread
import pandas as pd
import datetime
from config import SHEET_NAME


# ===================================================================
# Funciones Auxiliares (Helpers)
# ===================================================================
def _get_column_map(worksheet):
    """
    Obtiene y valida el mapeo de los nombres de columna a sus índices numéricos.
    """
    headers = worksheet.row_values(1)
    column_map = {header: i + 1 for i, header in enumerate(headers)}

    # AÑADIMOS LAS NUEVAS COLUMNAS REQUERIDAS
    required_cols = [
        "url_encontrada",
        "email_encontrado",
        "telefono_encontrado",
        "telefono_2",
        "telefono_3",
        "google_maps_url",
        "latitud",
        "longitud",
        "estado",
        "fecha_actualizacion",
    ]
    for col in required_cols:
        if col not in column_map:
            print(
                f"ADVERTENCIA: La columna requerida '{col}' no se encuentra en tu Google Sheet. No se podrá actualizar."
            )

    return column_map


def _prepare_batch_update_list(results_df, column_map):
    """Prepara la lista de objetos gspread.Cell que se deben actualizar en lote."""
    cells_to_update = []
    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for _, row in results_df.iterrows():
        sheet_row_index = int(row["sheet_row_number"])

        # --- Lógica de escritura de datos básicos ---
        if pd.notna(row["url_final"]) and "url_encontrada" in column_map:
            cells_to_update.append(
                gspread.Cell(
                    row=sheet_row_index,
                    col=column_map["url_encontrada"],
                    value=row["url_final"],
                )
            )
        if pd.notna(row["email_final"]) and "email_encontrado" in column_map:
            cells_to_update.append(
                gspread.Cell(
                    row=sheet_row_index,
                    col=column_map["email_encontrado"],
                    value=row["email_final"],
                )
            )

        # --- NUEVA LÓGICA PARA MÚLTIPLES TELÉFONOS ---
        # El `phone_list` es una lista de teléfonos que viene de los resultados.
        phone_list = row.get("phone_list", [])
        if phone_list:
            # Asigna el primer teléfono a la columna principal.
            if "telefono_encontrado" in column_map:
                cells_to_update.append(
                    gspread.Cell(
                        row=sheet_row_index,
                        col=column_map["telefono_encontrado"],
                        value=phone_list[0],
                    )
                )
            # Asigna el segundo teléfono si existe.
            if len(phone_list) > 1 and "telefono_2" in column_map:
                cells_to_update.append(
                    gspread.Cell(
                        row=sheet_row_index,
                        col=column_map["telefono_2"],
                        value=phone_list[1],
                    )
                )
            # Asigna el tercer teléfono si existe.
            if len(phone_list) > 2 and "telefono_3" in column_map:
                cells_to_update.append(
                    gspread.Cell(
                        row=sheet_row_index,
                        col=column_map["telefono_3"],
                        value=phone_list[2],
                    )
                )

        # --- NUEVA LÓGICA PARA DATOS DE GEOLOCALIZACIÓN ---
        if pd.notna(row["maps_url_final"]) and "google_maps_url" in column_map:
            cells_to_update.append(
                gspread.Cell(
                    row=sheet_row_index,
                    col=column_map["google_maps_url"],
                    value=row["maps_url_final"],
                )
            )
        if pd.notna(row["lat_final"]) and "latitud" in column_map:
            cells_to_update.append(
                gspread.Cell(
                    row=sheet_row_index,
                    col=column_map["latitud"],
                    value=str(row["lat_final"]),
                )
            )
        if pd.notna(row["lng_final"]) and "longitud" in column_map:
            cells_to_update.append(
                gspread.Cell(
                    row=sheet_row_index,
                    col=column_map["longitud"],
                    value=str(row["lng_final"]),
                )
            )

        # --- Lógica de estado y fecha ---
        if "estado" in column_map:
            cells_to_update.append(
                gspread.Cell(
                    row=sheet_row_index, col=column_map["estado"], value="BUSCADO"
                )
            )
        if "fecha_actualizacion" in column_map:
            cells_to_update.append(
                gspread.Cell(
                    row=sheet_row_index,
                    col=column_map["fecha_actualizacion"],
                    value=current_date,
                )
            )

    return cells_to_update


# ===================================================================
# FUNCIONES DE CONEXIÓN
# ===================================================================
def setup_google_sheets_client():
    """Autentica y devuelve un cliente para interactuar con Google Sheets."""
    try:
        gc = gspread.service_account(filename="credentials.json")
        spreadsheet = gc.open(SHEET_NAME)
        return spreadsheet.sheet1  ## retorno la primera hoja del documento
    except Exception as e:
        print(f"ERROR al conectar con Google Sheets: {e}")
        return None


# ===================================================================
# FUNCIONES DE LECTURA
# ===================================================================
def read_input_data():
    """
    Lee los datos de Google Sheets, añade el número de fila
    y devuelve las empresas pendientes como un DataFrame.
    """
    worksheet = setup_google_sheets_client()
    if worksheet is None:
        return pd.DataFrame()

    try:
        all_data = worksheet.get_all_records()
        if not all_data:
            print("La hoja parece estar vacía.")
            return pd.DataFrame()

        df = pd.DataFrame(all_data)
        df["sheet_row_number"] = df.index + 2

        if "estado" not in df.columns:
            df["estado"] = ""

        df["estado"] = df["estado"].fillna("")
        pending_companies = df[df["estado"] == ""].copy()

        print(f"Se encontraron {len(pending_companies)} empresas para procesar.")
        return pending_companies

    except Exception as e:
        print(f"Ocurrió un error al leer o procesar los datos: {e}")
        return pd.DataFrame()


# ===================================================================
# FUNCIÓN DE ESCRITURA
# ===================================================================
def write_results_to_sheet(df_resultados):
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

        # Lista de columnas requeridas, incluyendo las nuevas
        required_cols = [
            "url_encontrada",
            "email_encontrado",
            "telefono_encontrado",
            "estado",
            "fecha_actualizacion",
            "google_maps_url",
            "latitud",
            "longitud",
        ]
        for col in required_cols:
            if col not in col_map:
                print(
                    f"ADVERTENCIA: La columna '{col}' no se encuentra en tu Google Sheet. No se podrá actualizar."
                )

        cells_to_update = []
        fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for index, row in df_resultados.iterrows():
            sheet_row = int(row["sheet_row_number"])
            # Actualiza los campos existentes
            if pd.notna(row["url_final"]) and "url_encontrada" in col_map:
                cells_to_update.append(
                    gspread.Cell(
                        row=sheet_row,
                        col=col_map["url_encontrada"],
                        value=row["url_final"],
                    )
                )
            if pd.notna(row["email_final"]) and "email_encontrado" in col_map:
                cells_to_update.append(
                    gspread.Cell(
                        row=sheet_row,
                        col=col_map["email_encontrado"],
                        value=row["email_final"],
                    )
                )

            # Asigna el primer teléfono a la columna principal
            phone_list = row.get("phone_list", [])
            if phone_list and "telefono_encontrado" in col_map:
                cells_to_update.append(
                    gspread.Cell(
                        row=sheet_row,
                        col=col_map["telefono_encontrado"],
                        value=phone_list[0],
                    )
                )

            # Actualiza los nuevos campos de Google Maps
            if pd.notna(row["maps_url_final"]) and "google_maps_url" in col_map:
                cells_to_update.append(
                    gspread.Cell(
                        row=sheet_row,
                        col=col_map["google_maps_url"],
                        value=row["maps_url_final"],
                    )
                )
            if pd.notna(row["lat_final"]) and "latitud" in col_map:
                cells_to_update.append(
                    gspread.Cell(
                        row=sheet_row,
                        col=col_map["latitud"],
                        value=str(row["lat_final"]),
                    )
                )
            if pd.notna(row["lng_final"]) and "longitud" in col_map:
                cells_to_update.append(
                    gspread.Cell(
                        row=sheet_row,
                        col=col_map["longitud"],
                        value=str(row["lng_final"]),
                    )
                )

            # Actualiza el estado y la fecha
            if "estado" in col_map:
                cells_to_update.append(
                    gspread.Cell(row=sheet_row, col=col_map["estado"], value="BUSCADO")
                )
            if "fecha_actualizacion" in col_map:
                cells_to_update.append(
                    gspread.Cell(
                        row=sheet_row,
                        col=col_map["fecha_actualizacion"],
                        value=fecha_actual,
                    )
                )

        if cells_to_update:
            worksheet.update_cells(cells_to_update, value_input_option="USER_ENTERED")
            print("¡Google Sheet actualizado exitosamente!")
    except Exception as e:
        print(f"Ocurrió un error al actualizar Google Sheets: {e}")
