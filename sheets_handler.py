# sheets_handler.py
import gspread
import pandas as pd
import datetime
from config import SHEET_NAME

# ===================================================================
# FUNCIONES DE CONEXIÓN Y LECTURA
# ===================================================================
def setup_google_sheets_client():
    """Autentica y devuelve un cliente para interactuar con Google Sheets."""
    try:
        gc = gspread.service_account(filename='credentials.json')
        spreadsheet = gc.open("TEST_SCRAPING")
        return spreadsheet.sheet1
    except Exception as e:
        print(f"ERROR al conectar con Google Sheets: {e}")
        return None

def leer_datos_de_entrada():
    """Lee los datos de Google Sheets, añade el número de fila y devuelve las pendientes."""
    worksheet = setup_google_sheets_client()
    if worksheet is None: return pd.DataFrame()
    try:
        print("Leyendo todos los registros de la hoja...")
        todos_los_datos = worksheet.get_all_records()
        if not todos_los_datos: return pd.DataFrame()
        df = pd.DataFrame(todos_los_datos)
        df['sheet_row_number'] = df.index + 2
        if 'estado' not in df.columns: df['estado'] = ''
        df['estado'] = df['estado'].fillna('')
        empresas_pendientes = df[df['estado'] == ''].copy()
        print(f"Se encontraron {len(empresas_pendientes)} empresas pendientes de procesar.")
        return empresas_pendientes
    except Exception as e:
        print(f"Ocurrió un error al leer o procesar los datos: {e}")
        return pd.DataFrame()

# ===================================================================
# FUNCIÓN DE ESCRITURA
# ===================================================================
def escribir_resultados_en_sheet(df_resultados):
    """Toma un DataFrame con los resultados y actualiza la hoja de Google Sheets en un solo lote."""
    print("\nActualizando Google Sheet con los resultados...")
    worksheet = setup_google_sheets_client()
    if worksheet is None: return

    try:
        headers = worksheet.row_values(1)
        col_map = {header: i + 1 for i, header in enumerate(headers)}

        required_cols = ['url_encontrada', 'email_encontrado', 'telefono_encontrado', 'estado', 'fecha_actualizacion']
        for col in required_cols:
            if col not in col_map:
                print(f"ERROR: La columna '{col}' no se encuentra en tu Google Sheet.")
                return

        cells_to_update = []
        fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for index, row in df_resultados.iterrows():
            sheet_row = int(row['sheet_row_number'])
            if pd.notna(row['url_final']): cells_to_update.append(gspread.Cell(row=sheet_row, col=col_map['url_encontrada'], value=row['url_final']))
            if pd.notna(row['email_final']): cells_to_update.append(gspread.Cell(row=sheet_row, col=col_map['email_encontrado'], value=row['email_final']))
            if pd.notna(row['telefono_final']): cells_to_update.append(gspread.Cell(row=sheet_row, col=col_map['telefono_encontrado'], value=row['telefono_final']))
            cells_to_update.append(gspread.Cell(row=sheet_row, col=col_map['estado'], value='BUSCADO'))
            cells_to_update.append(gspread.Cell(row=sheet_row, col=col_map['fecha_actualizacion'], value=fecha_actual))

        if cells_to_update:
            worksheet.update_cells(cells_to_update, value_input_option='USER_ENTERED')
            print("¡Google Sheet actualizado exitosamente!")
    except Exception as e:
        print(f"Ocurrió un error al actualizar Google Sheets: {e}")