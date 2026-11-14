"""Pruebas de integración de las funcionalidades con el cliente de pruebas de Flask."""
from conftest import ingresar


def test_login_correcto_y_salir(client):
    r = ingresar(client)
    assert "Panel de control" in r.get_data(as_text=True)
    assert client.get("/salir", follow_redirects=True).status_code == 200


def test_login_incorrecto_y_bloqueo(client):
    for _ in range(5):
        r = ingresar(client, clave="mala")
        assert "Correo o contraseña incorrectos" in r.get_data(as_text=True)
    r = ingresar(client)  # aun con la clave correcta
    assert "Cuenta bloqueada" in r.get_data(as_text=True)


def test_login_campos_vacios(client):
    r = client.post("/", data={"correo": "", "clave": ""})
    texto = r.get_data(as_text=True)
    assert "El correo es obligatorio" in texto and "La contraseña es obligatoria" in texto


def test_panel_requiere_login(client):
    r = client.get("/panel")
    assert r.status_code == 302 and r.headers["Location"].endswith("/")


def test_mision_validaciones_y_robot_ocupado(client):
    ingresar(client)
    r = client.post("/mision/nueva", data={"robot": "", "escenario": ""})
    t = r.get_data(as_text=True)
    assert "Seleccione un robot" in t and "El escenario es obligatorio" in t
    r = client.post("/mision/nueva", data={"robot": "1", "escenario": "E1 pasillo"}, follow_redirects=True)
    assert "Misión iniciada" in r.get_data(as_text=True)
    ingresar(client, "supervisor@rescatebot.bo", "Supervisor123")
    r = client.post("/mision/nueva", data={"robot": "1", "escenario": "Intento duplicado"})
    assert "ya tiene una misión activa" in r.get_data(as_text=True)


def _con_mision(client):
    ingresar(client)
    client.post("/mision/nueva", data={"robot": "1", "escenario": "E9 incendio simulado"})


def test_lecturas_validas_invalidas_y_alerta(client):
    _con_mision(client)
    r = client.post("/lecturas", data={"variable": "temp_objeto", "valor": "23.5"}, follow_redirects=True)
    assert "Lectura registrada" in r.get_data(as_text=True)
    r = client.post("/lecturas", data={"variable": "temp_objeto", "valor": "912"}, follow_redirects=True)
    assert "Fuera de rango" in r.get_data(as_text=True)
    r = client.post("/lecturas", data={"variable": "distancia", "valor": ""}, follow_redirects=True)
    assert "Sin dato" in r.get_data(as_text=True)
    r = client.post("/lecturas", data={"variable": "gas_rel", "valor": "45"}, follow_redirects=True)
    assert "gas_rel supera el umbral" in r.get_data(as_text=True)


def test_lectura_sin_mision(client):
    ingresar(client)
    r = client.post("/lecturas", data={"variable": "gas_rel", "valor": "4"}, follow_redirects=True)
    assert "Primero inicie una misión" in r.get_data(as_text=True)
    r = client.post("/orden", data={"direccion": "adelante"}, follow_redirects=True)
    assert "Primero inicie una misión" in r.get_data(as_text=True)


def test_orden_bloqueo_por_proximidad_y_ejecucion(client):
    _con_mision(client)
    client.post("/lecturas", data={"variable": "distancia", "valor": "15"})
    r = client.post("/orden", data={"direccion": "adelante"}, follow_redirects=True)
    assert "Parada por proximidad" in r.get_data(as_text=True)
    r = client.post("/orden", data={"direccion": "atras"}, follow_redirects=True)
    assert "Orden enviada al robot" in r.get_data(as_text=True)


def test_detecciones_solo_supervisor_y_decision(client):
    _con_mision(client)
    assert client.get("/detecciones").status_code == 403
    r = client.post("/api/detecciones", json={"id_sesion": 1, "nro_cuadro": 1842, "confianza": 0.82, "sector": "B"})
    assert r.status_code == 201
    assert client.post("/api/detecciones", json={"id_sesion": 1, "nro_cuadro": 5, "confianza": 1.5}).status_code == 400
    assert client.post("/api/detecciones", json={"id_sesion": 99, "nro_cuadro": 5, "confianza": 0.5}).status_code == 404
    assert client.post("/api/detecciones", json={}).status_code == 400
    ingresar(client, "supervisor@rescatebot.bo", "Supervisor123")
    assert "1842" in client.get("/detecciones").get_data(as_text=True)
    r = client.post("/detecciones/1", data={"decision": "confirmado"}, follow_redirects=True)
    assert "Detección actualizada" in r.get_data(as_text=True)
    r = client.post("/detecciones/1", data={"decision": "otra"}, follow_redirects=True)
    assert "Decisión no válida" in r.get_data(as_text=True)
    r = client.post("/detecciones/77", data={"decision": "descartado"}, follow_redirects=True)
    assert "La detección no existe" in r.get_data(as_text=True)


def test_historial_y_exportar(client):
    _con_mision(client)
    client.post("/lecturas", data={"variable": "bateria", "valor": "7.4"})
    r = client.get("/historial/1.csv", follow_redirects=True)
    assert "Finalice la misión antes de exportar" in r.get_data(as_text=True)
    client.post("/mision/finalizar")
    r = client.get("/historial/1.csv")
    assert r.status_code == 200 and "bateria,7.4,V,True" in r.get_data(as_text=True)
    assert client.get("/historial/99.csv").status_code == 404
    assert "E9 incendio simulado" in client.get("/historial").get_data(as_text=True)


# --- Casos agregados tras el análisis de cobertura (ramas no ejecutadas) ---
def test_login_correo_no_registrado(client):
    r = ingresar(client, "nadie@rescatebot.bo", "Cualquier1")
    assert "Correo o contraseña incorrectos" in r.get_data(as_text=True)


def test_formulario_mision_get_y_finalizar_sin_mision(client):
    ingresar(client)
    assert "Iniciar misión" in client.get("/mision/nueva").get_data(as_text=True)
    r = client.post("/mision/finalizar", follow_redirects=True)
    assert "No tiene una misión activa" in r.get_data(as_text=True)


def test_create_app_por_defecto_y_comando_init_db(tmp_path, monkeypatch):
    from rescatebot import create_app
    app = create_app()
    assert app.config["DATABASE"].endswith("rescatebot.db")
    app.config["DATABASE"] = str(tmp_path / "cli.db")
    salida = app.test_cli_runner().invoke(args=["init-db"])
    assert "Base de datos inicializada" in salida.output
