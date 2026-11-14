"""Pruebas de caja blanca: un caso por cada camino independiente del grafo de flujo."""
import pytest
from rescatebot.reglas import evaluar_alerta, evaluar_orden, validar_lectura, validar_login


# ---------------- validar_lectura: V(G) = 5 -> 5 caminos ----------------
@pytest.mark.parametrize("cp, variable, valor, esperado", [
    ("C1", "humedad", "50", (False, None, "Variable desconocida")),
    ("C2", "distancia", "", (True, None, "Sin dato: se guarda como lectura inválida (NULL)")),
    ("C3", "temp_objeto", "abc", (False, None, "El valor debe ser numérico")),
    ("C4", "temp_objeto", "912", (False, None, "Fuera de rango: temp_objeto debe estar entre -70 y 380")),
    ("C5", "temp_objeto", "23.5", (True, 23.5, None)),
])
def test_validar_lectura_caminos(cp, variable, valor, esperado):
    assert validar_lectura(variable, valor) == esperado


@pytest.mark.parametrize("valor, ok", [("2", True), ("1.99", False), ("400", True), ("400.01", False)])
def test_validar_lectura_limites_distancia(valor, ok):
    assert validar_lectura("distancia", valor)[0] is ok


def test_validar_lectura_decimal_con_coma():
    # Regresión del defecto encontrado con Selenium (CP09)
    assert validar_lectura("temp_objeto", "23,5") == (True, 23.5, None)


def test_validar_lectura_none_es_sin_dato():
    assert validar_lectura("bateria", None) == (True, None, "Sin dato: se guarda como lectura inválida (NULL)")


# ---------------- evaluar_orden: V(G) = 6 -> 6 caminos ----------------
@pytest.mark.parametrize("cp, direccion, distancia, bateria, esperado", [
    ("C1", "saltar", 50, 7.4, "RECHAZADA"),
    ("C2", "detener", 5, 5.0, "DETENER"),
    ("C3", "adelante", 50, 6.0, "BLOQUEO_BATERIA"),
    ("C4", "adelante", 19.9, 7.4, "BLOQUEO_PROXIMIDAD"),
    ("C5", "adelante", 20, 7.4, "EJECUTAR"),
    ("C6", "izquierda", 5, 7.4, "EJECUTAR"),
])
def test_evaluar_orden_caminos(cp, direccion, distancia, bateria, esperado):
    assert evaluar_orden(direccion, distancia, bateria) == esperado


def test_evaluar_orden_sin_eco_no_bloquea():
    assert evaluar_orden("adelante", None, 7.4) == "EJECUTAR"


def test_evaluar_orden_bateria_en_limite():
    assert evaluar_orden("adelante", 50, 6.4) == "EJECUTAR"


# ---------------- funciones auxiliares ----------------
@pytest.mark.parametrize("variable, valor, hay_alerta", [
    ("bateria", 6.0, True), ("bateria", 7.4, False), ("gas_rel", 45, True),
    ("gas_rel", 30, False), ("temp_objeto", 61, True), ("distancia", 10, False), ("gas_rel", None, False)])
def test_evaluar_alerta(variable, valor, hay_alerta):
    assert (evaluar_alerta(variable, valor) is not None) is hay_alerta


@pytest.mark.parametrize("correo, clave, n_errores", [
    ("operador@rescatebot.bo", "x", 0), ("", "", 2), ("correo-sin-arroba", "x", 1), ("a@b.bo", "", 1)])
def test_validar_login(correo, clave, n_errores):
    assert len(validar_login(correo, clave)) == n_errores
