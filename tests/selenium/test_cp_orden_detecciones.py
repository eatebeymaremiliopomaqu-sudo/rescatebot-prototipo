"""CP10–CP11: parada por proximidad (valor límite 20 cm) y revisión de detecciones (roles)."""
import pytest
import requests
from selenium.webdriver.common.by import By
from conftest import URL, evidencia
from paginas import enviar_y_esperar, ingresar, iniciar_mision, mensajes, registrar_lectura, seleccionar


@pytest.mark.parametrize("distancia, esperado", [
    ("19.9", "Parada por proximidad: obstáculo a menos de 20 cm"),
    ("20", "Orden enviada al robot"),
])
def test_CP10_orden_adelante_limite_20cm(driver, distancia, esperado):
    ingresar(driver, "operador@rescatebot.bo", "Operador123")
    iniciar_mision(driver)
    registrar_lectura(driver, "distancia", distancia)
    enviar_y_esperar(driver, driver.find_element(By.ID, "btn-adelante"))
    evidencia(driver, f"CP10_{distancia}")
    assert esperado in mensajes(driver)


def test_CP11_supervisor_confirma_y_operador_sin_permiso(driver):
    ingresar(driver, "operador@rescatebot.bo", "Operador123")
    iniciar_mision(driver)
    r = requests.post(URL + "/api/detecciones",
                      json={"id_sesion": 1, "nro_cuadro": 1842, "confianza": 0.82, "sector": "B - Pasillo"})
    assert r.status_code == 201
    driver.get(URL + "/detecciones")
    evidencia(driver, "CP11a")
    assert "No tiene permiso" in driver.find_element(By.ID, "mensaje-error").text
    ingresar(driver, "supervisor@rescatebot.bo", "Supervisor123")
    enviar_y_esperar(driver, driver.find_element(By.ID, "nav-detecciones"))
    enviar_y_esperar(driver, driver.find_element(By.CSS_SELECTOR, "#det-1 button[value='confirmado']"))
    seleccionar(driver, "filtro-estado", "todas")
    enviar_y_esperar(driver, driver.find_element(By.ID, "btn-filtrar"))
    evidencia(driver, "CP11b")
    assert driver.find_element(By.CSS_SELECTOR, "#det-1 .decision").text == "confirmado"
