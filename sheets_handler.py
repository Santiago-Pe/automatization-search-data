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
        spreadsheet = gc.open(SHEET_NAME)
        return spreadsheet.sheet1 ## retorno la primera hoja del documento
    except Exception as e:
        print(f"ERROR al conectar con Google Sheets: {e}")
        return None

def read_input_data():
    """
    Lee los datos de Google Sheets, añade el número de fila
    y devuelve las empresas pendientes como un DataFrame.
    """
    worksheet = setup_google_sheets_client()
    if worksheet is None: 
        return pd.DataFrame() # To do: que hace el pd.DataFrame()
        
    try:
        print("Leyendo todos los registros de la hoja...")
        all_data = worksheet.get_all_records()
        if not all_data:
            print("La hoja parece estar vacía.")
            return pd.DataFrame()

        df = pd.DataFrame(all_data)
        # Añadimos el número de fila original para poder actualizar la celda correcta más tarde.
        df['sheet_row_number'] = df.index + 2
        
        # Lógica de filtrado para encontrar empresas pendientes.
        # Asumimos que la columna en la hoja se llama 'estado'.
        if 'estado' not in df.columns: 
            df['estado'] = ''
            
        df['estado'] = df['estado'].fillna('')
        pending_companies = df[df['estado'] == ''].copy()
        
        print(f"Se encontraron {len(pending_companies)} empresas para procesar.")
        return pending_companies
        
    except Exception as e:
        print(f"Ocurrió un error al leer o procesar los datos: {e}")
        return pd.DataFrame()

# ===================================================================
# FUNCIÓN DE ESCRITURA
# ===================================================================
def write_results_to_sheet(results_df):
    """Toma un DataFrame con los resultados y actualiza la hoja de Google Sheets en un solo lote."""
    print("\nActualizando Google Sheet con los resultados...")
    worksheet = setup_google_sheets_client()
    if worksheet is None: 
        return

    try:
        headers = worksheet.row_values(1)
        column_map = {header: i + 1 for i, header in enumerate(headers)}

        required_cols = ['url_encontrada', 'email_encontrado', 'telefono_encontrado', 'estado', 'fecha_actualizacion']
        for col in required_cols:
            if col not in column_map:
                print(f"ERROR: La columna '{col}' no se encuentra en tu Google Sheet.")
                return

        cells_to_update = []
        current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for index, row in results_df.iterrows():
            sheet_row = int(row['sheet_row_number'])
            if pd.notna(row['url_final']): 
                cells_to_update.append(gspread.Cell(row=sheet_row, col=column_map['url_encontrada'], value=row['url_final']))
            if pd.notna(row['email_final']): 
                cells_to_update.append(gspread.Cell(row=sheet_row, col=column_map['email_encontrado'], value=row['email_final']))
            if pd.notna(row['telefono_final']): 
                cells_to_update.append(gspread.Cell(row=sheet_row, col=column_map['telefono_encontrado'], value=row['telefono_final']))
            
            cells_to_update.append(gspread.Cell(row=sheet_row, col=column_map['estado'], value='BUSCADO'))
            cells_to_update.append(gspread.Cell(row=sheet_row, col=column_map['fecha_actualizacion'], value=current_date))

        if cells_to_update:
            worksheet.update_cells(cells_to_update, value_input_option='USER_ENTERED')
            print("¡Google Sheet actualizado exitosamente!")
            
    except Exception as e:
        print(f"Ocurrió un error al actualizar Google Sheets: {e}")