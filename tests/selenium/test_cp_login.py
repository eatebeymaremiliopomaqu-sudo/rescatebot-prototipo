"""CP01–CP04 y CP12: inicio de sesión (partición de equivalencias)."""
from selenium.webdriver.common.by import By
from conftest import evidencia
from paginas import ingresar, mensajes


def test_CP01_login_valido(driver):
    ingresar(driver, "operador@rescatebot.bo", "Operador123")
    evidencia(driver, "CP01")
    assert driver.current_url.endswith("/panel")                         # 5. validar con assert
    assert "Operador Demo" in driver.find_element(By.ID, "usuario-actual").text


def test_CP02_clave_incorrecta(driver):
    ingresar(driver, "operador@rescatebot.bo", "ClaveMala9")
    evidencia(driver, "CP02")
    assert "Correo o contraseña incorrectos" in mensajes(driver)
    assert not driver.current_url.endswith("/panel")


def test_CP03_campos_vacios(driver):
    ingresar(driver, "", "")
    evidencia(driver, "CP03")
    assert mensajes(driver) == ["El correo es obligatorio", "La contraseña es obligatoria"]


def test_CP04_correo_formato_invalido(driver):
    ingresar(driver, "operador.rescatebot.bo", "Operador123")
    evidencia(driver, "CP04")
    assert "El correo no tiene un formato válido" in mensajes(driver)


def test_CP12_bloqueo_tras_5_intentos(driver):
    for _ in range(5):
        ingresar(driver, "operador@rescatebot.bo", "ClaveMala9")
    ingresar(driver, "operador@rescatebot.bo", "Operador123")   # 6.º intento con la clave correcta
    evidencia(driver, "CP12")
    assert any("Cuenta bloqueada" in m for m in mensajes(driver))
