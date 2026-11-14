"""CP05–CP09: misión y registro de lecturas (particiones y valores límite)."""
import pytest
from selenium.webdriver.common.by import By
from conftest import evidencia
from paginas import ingresar, iniciar_mision, mensajes, registrar_lectura


@pytest.fixture
def operador_con_mision(driver):
    ingresar(driver, "operador@rescatebot.bo", "Operador123")
    iniciar_mision(driver)
    return driver


def test_CP05_mision_sin_escenario_y_valida(driver):
    ingresar(driver, "operador@rescatebot.bo", "Operador123")
    iniciar_mision(driver, escenario="")
    evidencia(driver, "CP05a")
    assert "El escenario es obligatorio (mínimo 3 caracteres)" in mensajes(driver)
    iniciar_mision(driver)
    evidencia(driver, "CP05b")
    assert "Misión iniciada" in mensajes(driver)
    assert "ROB-001" in driver.find_element(By.ID, "mision-actual").text


def test_CP06_lectura_valida(operador_con_mision):
    d = operador_con_mision
    registrar_lectura(d, "temp_objeto", "23.5")
    evidencia(d, "CP06")
    assert "Lectura registrada" in mensajes(d)
    assert d.find_element(By.ID, "ultimo-temp_objeto").text == "23.5 C"


@pytest.mark.parametrize("valor, aceptado", [("2", True), ("1.99", False), ("400", True), ("400.01", False)])
def test_CP07_limites_distancia(operador_con_mision, valor, aceptado):
    d = operador_con_mision
    registrar_lectura(d, "distancia", valor)
    evidencia(d, f"CP07_{valor}")
    if aceptado:
        assert "Lectura registrada" in mensajes(d)
    else:
        assert "Fuera de rango: distancia debe estar entre 2 y 400" in mensajes(d)


def test_CP08_valor_no_numerico(operador_con_mision):
    d = operador_con_mision
    registrar_lectura(d, "gas_rel", "abc")
    evidencia(d, "CP08")
    assert "El valor debe ser numérico" in mensajes(d)


def test_CP09_decimal_con_coma(operador_con_mision):
    """En Bolivia es habitual escribir decimales con coma: 23,5 debe aceptarse como 23.5."""
    d = operador_con_mision
    registrar_lectura(d, "temp_objeto", "23,5")
    evidencia(d, "CP09")
    assert "Lectura registrada" in mensajes(d)
    assert d.find_element(By.ID, "ultimo-temp_objeto").text == "23.5 C"
