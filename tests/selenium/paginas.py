"""Acciones reutilizables (patrón Page Object simplificado)."""
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from conftest import URL

MARCA = "return window.__pagina_anterior === undefined && document.readyState === 'complete';"


def _esperar(driver, segundos, condicion):
    return WebDriverWait(driver, segundos, ignored_exceptions=(WebDriverException,)).until(
        lambda d: d.execute_script(condicion))


def enviar_y_esperar(driver, boton):
    """Hace clic en un botón que envía un formulario y espera la página de respuesta.

    Historial de correcciones (ver informe, sección 5):
    1. CP12: sin espera, el siguiente driver.get() cancelaba el envío del formulario.
    2. Chrome 157: EC.staleness_of() fallaba con «Node with given id does not belong to
       the document»; se reemplazó por una marca JavaScript en la página actual.
    3. Chrome 157: a veces el clic nativo no enviaba el formulario (el servidor no recibía
       el POST). Ahora se espera a que la página esté completa, se centra el botón y, si en
       3 s no hubo navegación, se repite el clic con JavaScript (el formulario aún no se
       había enviado, así que no hay doble envío).
    """
    _esperar(driver, 10, "return document.readyState === 'complete';")
    driver.execute_script("window.__pagina_anterior = true;"
                          "arguments[0].scrollIntoView({block: 'center'});", boton)
    boton.click()
    try:
        _esperar(driver, 3, MARCA)
    except TimeoutException:
        driver.execute_script("arguments[0].click();", boton)
        _esperar(driver, 10, MARCA)


def escribir(driver, campo, texto):
    """Escribe en un campo y verifica que el valor quedó.

    Corrección 4 (Chrome 157 en equipos lentos): a veces send_keys() no llegaba al campo
    y el formulario se enviaba vacío. Si en 2 s el campo no contiene el texto, se asigna
    con JavaScript y se dispara el evento «input».
    """
    campo.clear()
    campo.send_keys(texto)
    try:
        WebDriverWait(driver, 2, ignored_exceptions=(WebDriverException,)).until(
            lambda d: campo.get_attribute("value") == texto)
    except TimeoutException:
        driver.execute_script(
            "arguments[0].value = arguments[1];"
            "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", campo, texto)
    assert campo.get_attribute("value") == texto


def seleccionar(driver, id_select, valor):
    """Elige una opción de una lista y verifica que quedó seleccionada (misma idea que escribir)."""
    driver.find_element(By.CSS_SELECTOR, f"#{id_select} option[value='{valor}']").click()
    lista = driver.find_element(By.ID, id_select)
    try:
        WebDriverWait(driver, 2, ignored_exceptions=(WebDriverException,)).until(
            lambda d: lista.get_attribute("value") == valor)
    except TimeoutException:
        driver.execute_script("arguments[0].value = arguments[1];"
                              "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", lista, valor)
    assert lista.get_attribute("value") == valor


def ingresar(driver, correo, clave):
    driver.get(URL + "/")                                       # 1. abrir la aplicación
    campo_correo = driver.find_element(By.ID, "correo")          # 2. localizar elementos (id)
    campo_clave = driver.find_element(By.NAME, "clave")          #    (name)
    escribir(driver, campo_correo, correo)                       # 3. ingresar datos
    escribir(driver, campo_clave, clave)
    enviar_y_esperar(driver, driver.find_element(By.XPATH, "//button[@id='btn-ingresar']"))  # 4. ejecutar (xpath)


def mensajes(driver):
    return [e.text for e in driver.find_elements(By.CSS_SELECTOR, ".msg")]  # (css)


def iniciar_mision(driver, escenario="E9 incendio simulado - laboratorio"):
    driver.get(URL + "/mision/nueva")
    seleccionar(driver, "robot", "1")
    escribir(driver, driver.find_element(By.ID, "escenario"), escenario)
    enviar_y_esperar(driver, driver.find_element(By.ID, "btn-iniciar"))


def registrar_lectura(driver, variable, valor):
    seleccionar(driver, "variable", variable)
    escribir(driver, driver.find_element(By.ID, "valor"), valor)
    enviar_y_esperar(driver, driver.find_element(By.ID, "btn-lectura"))
