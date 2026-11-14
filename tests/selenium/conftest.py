"""Configuración de la suite Selenium.

Levanta el prototipo en un hilo con una base de datos nueva por prueba y crea el navegador.
Navegador: variable de entorno NAVEGADOR = firefox (por defecto) o chrome.
"""
import os
import sys
import threading
from pathlib import Path

import pytest
from selenium import webdriver
from werkzeug.serving import make_server

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
from rescatebot import create_app, db  # noqa: E402

EVIDENCIAS = Path(__file__).with_name("evidencias")
EVIDENCIAS.mkdir(exist_ok=True)
PUERTO = 5055
URL = f"http://127.0.0.1:{PUERTO}"


@pytest.fixture(scope="session")
def app(tmp_path_factory):
    ruta = tmp_path_factory.mktemp("bd") / "selenium.db"
    aplicacion = create_app({"DATABASE": str(ruta), "SECRET_KEY": "selenium"})
    servidor = make_server("127.0.0.1", PUERTO, aplicacion)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    yield aplicacion
    servidor.shutdown()


@pytest.fixture
def base_limpia(app):
    """Base de datos nueva para cada caso: los casos son independientes y reproducibles."""
    ruta = Path(app.config["DATABASE"])
    if ruta.exists():
        ruta.unlink()
    with app.app_context():
        db.init_db()


@pytest.fixture
def driver(base_limpia):
    navegador = os.environ.get("NAVEGADOR", "firefox").lower()
    if navegador == "chrome":
        opciones = webdriver.ChromeOptions()
        opciones.add_argument("--headless=new")
        opciones.add_argument("--window-size=1280,900")
        d = webdriver.Chrome(options=opciones)
    else:
        opciones = webdriver.FirefoxOptions()
        if os.environ.get("HEADLESS", "1") == "1":
            opciones.add_argument("-headless")
        d = webdriver.Firefox(options=opciones)
        d.set_window_size(1280, 900)
    d.implicitly_wait(3)
    yield d
    d.quit()


def evidencia(driver, nombre):
    driver.save_screenshot(str(EVIDENCIAS / f"evidencia_{nombre}.png"))
