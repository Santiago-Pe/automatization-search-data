# tests/test_scraper.py
from bs4 import BeautifulSoup
from scraper import _buscar_datos_en_soup


def test_encontrar_email_y_telefono():
    """
    Prueba que la función extrae correctamente un email y un teléfono de un HTML simple.
    """
    # 1. Preparación (Arrange): Creamos un HTML falso
    html_falso = """
    <html>
        <body>
            <p>Contáctanos al (555) 123-4567 para más información.</p>
            <a href="mailto:info@ejemplo.com">Enviar un correo</a>
        </body>
    </html>
    """
    soup = BeautifulSoup(html_falso, "html.parser")

    # 2. Actuación (Act): Ejecutamos la función que queremos probar
    email, telefono = _buscar_datos_en_soup(soup)

    # 3. Afirmación (Assert): Verificamos que los resultados son los esperados
    assert email == "info@ejemplo.com"
    assert telefono == "(555) 123-4567"


def test_no_encontrar_datos():
    """
    Prueba que la función devuelve None si no hay datos de contacto.
    """
    # Arrange
    html_falso = "<p>Esta es una página sin información de contacto.</p>"
    soup = BeautifulSoup(html_falso, "html.parser")

    # Act
    email, telefono = _buscar_datos_en_soup(soup)

    # Assert
    assert email is None
    assert telefono is None
