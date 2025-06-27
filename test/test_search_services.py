# tests/test_search_services.py
from search_services import buscar_info_en_google_maps

def test_buscar_info_maps_exitoso(mocker):
    """
    Prueba el flujo exitoso de buscar_info_en_google_maps usando un mock.
    """
    # 1. Arrange: Preparamos las respuestas falsas que simularán a la API
    respuesta_find_place_falsa = {
        'status': 'OK',
        'candidates': [{'place_id': 'fake_place_id'}]
    }
    respuesta_details_falsa = {
        'status': 'OK',
        'result': {
            'website': 'http://pagina-falsa.com',
            'formatted_phone_number': '+54 9 11 1234-5678'
        }
    }
    
    # Aquí está la magia del mock:
    # Le decimos a pytest que cuando se llame a 'requests.get', en lugar de
    # ejecutar la llamada real, devuelva un objeto que tiene un método .json()
    # que a su vez devuelve nuestra data falsa.
    mock_response_find = mocker.Mock()
    mock_response_find.json.return_value = respuesta_find_place_falsa
    
    mock_response_details = mocker.Mock()
    mock_response_details.json.return_value = respuesta_details_falsa
    
    # Hacemos que la primera llamada a get devuelva el find_place y la segunda el details
    mocker.patch('requests.get', side_effect=[mock_response_find, mock_response_details])

    # 2. Act: Llamamos a nuestra función
    website, telefono = buscar_info_en_google_maps("query de prueba")
    
    # 3. Assert: Verificamos que nuestra función procesó correctamente la data falsa
    assert website == 'http://pagina-falsa.com'
    assert telefono == '+54 9 11 1234-5678'
