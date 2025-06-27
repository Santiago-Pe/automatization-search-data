GUÍA DE USO - ENRIQUECEDOR DE DATOS V1.0

Hola, sigue estos pasos para poner en marcha la herramienta.

**PASO 1: INSTALAR PYTHON (Si no lo tienes)**

- Ve a https://www.python.org/downloads/ y descarga la última versión de Python.
- Durante la instalación, ASEGÚRATE de marcar la casilla que dice "Add Python to PATH".

**PASO 2: PREPARAR LA CARPETA**

- Descomprime el archivo .zip que te envié en un lugar fácil de encontrar (ej. en tu Escritorio).

**PASO 3: CONFIGURAR Y EJECUTAR EL SCRIPT**

1. Abre una terminal o Símbolo del sistema:

   - En Windows: Abre la carpeta, haz clic en la barra de direcciones de arriba, escribe "cmd" y presiona Enter.
   - En Mac/Linux: Abre la aplicación "Terminal" y escribe `cd ` (con un espacio al final), luego arrastra la carpeta del proyecto a la ventana de la terminal y presiona Enter.

2. Crea un entorno virtual para no afectar tu sistema (solo se hace la primera vez):

   - Escribe en la terminal: `python -m venv venv`

3. Activa el entorno virtual:

   - En Windows: `venv\Scripts\activate`
   - En Mac/Linux: `source venv/bin/activate`
   - Verás que aparece `(venv)` al principio de la línea en tu terminal.

4. Instala las librerías necesarias (solo se hace la primera vez):

   - Escribe en la terminal: `pip install -r requirements.txt`
   - Espera a que termine la instalación.

5. ¡Ejecuta el programa!
   - Escribe en la terminal: `python enricher.py`

**¿CÓMO FUNCIONA?**

- El programa leerá la hoja de Google Sheet llamada "Empresas a Enriquecer".
- Buscará todas las filas que tengan el estado "PENDIENTE".
- Procesará una por una y actualizará la misma hoja con los resultados.
- Puedes cerrar la terminal en cualquier momento. La próxima vez que ejecutes el script, continuará donde se quedó.

## librerias

gspread
pandas
oauth2client
google-api-python-client
requests
beautifulsoup4
python-dotenv

# Notas

En las listas de empresas que solo este la razon social, cualquier otra osa debe ir en un agregado a parte
