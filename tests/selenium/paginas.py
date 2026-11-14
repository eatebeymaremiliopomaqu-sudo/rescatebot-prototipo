"""Acciones reutilizables (patrón Page Object simplificado)."""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from conftest import URL


def enviar_y_esperar(driver, boton):
    """Hace clic y espera a que el navegador cargue la página de respuesta.

    Corrección del fallo CP12: sin esta espera, el siguiente driver.get() cancelaba el
    envío del formulario y algunos intentos de login nunca llegaban al servidor.
    """
    boton.click()
    WebDriverWait(driver, 5).until(EC.staleness_of(boton))


def ingresar(driver, correo, clave):
    driver.get(URL + "/")                                       # 1. abrir la aplicación
    campo_correo = driver.find_element(By.ID, "correo")          # 2. localizar elementos (id)
    campo_clave = driver.find_element(By.NAME, "clave")          #    (name)
    campo_correo.clear(); campo_correo.send_keys(correo)         # 3. ingresar datos
    campo_clave.clear(); campo_clave.send_keys(clave)
    enviar_y_esperar(driver, driver.find_element(By.XPATH, "//button[@id='btn-ingresar']"))  # 4. ejecutar (xpath)


def mensajes(driver):
    return [e.text for e in driver.find_elements(By.CSS_SELECTOR, ".msg")]  # (css)


def iniciar_mision(driver, escenario="E9 incendio simulado - laboratorio"):
    driver.get(URL + "/mision/nueva")
    driver.find_element(By.CSS_SELECTOR, "#robot option[value='1']").click()
    driver.find_element(By.ID, "escenario").send_keys(escenario)
    enviar_y_esperar(driver, driver.find_element(By.ID, "btn-iniciar"))


def registrar_lectura(driver, variable, valor):
    driver.find_element(By.CSS_SELECTOR, f"#variable option[value='{variable}']").click()
    campo = driver.find_element(By.ID, "valor")
    campo.clear(); campo.send_keys(valor)
    enviar_y_esperar(driver, driver.find_element(By.ID, "btn-lectura"))
