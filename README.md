# RescateBot El Alto — Prototipo funcional (H4 · Tarea 2)

Prototipo web del sistema de teleoperación y monitoreo del vehículo robótico de rescate
(Proyecto Integrador II, UNIFRANZ El Alto). Autor: Beymar Emilio Poma Queso.

## Funcionalidades
1. Inicio de sesión con roles (operador / supervisor), validaciones y bloqueo tras 5 intentos.
2. Inicio y fin de misión (robot + escenario; un robot solo puede tener una misión activa).
3. Registro de lecturas de sensores con validación de rangos físicos (lectura sin dato = NULL).
4. Panel de telemetría con alertas automáticas y órdenes de movimiento con parada por proximidad (< 20 cm) y por batería (< 6,4 V).
5. Revisión de detecciones de personas (solo supervisor) y API `/api/detecciones` para el servicio de visión.
6. Historial de misiones y exportación del reporte en CSV.

## Estructura
```
src/rescatebot/      código (app Flask, reglas de negocio, base de datos, plantillas)
tests/unit/          pruebas unitarias y de integración (pytest) — caja blanca
tests/selenium/      pruebas funcionales automatizadas (Selenium) — caja negra
docs/                diagramas de flujo y grafos de control
```

## Ejecutar
```bash
python -m venv venv && venv\Scripts\activate      # Windows (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
python run.py                                        # http://127.0.0.1:5000
```
Usuarios de demostración: `operador@rescatebot.bo / Operador123`, `supervisor@rescatebot.bo / Supervisor123`.

## Pruebas
```bash
pytest -v                                            # pruebas unitarias
coverage run --branch -m pytest && coverage report -m   # cobertura de sentencias y ramas
pytest tests/selenium -v                             # Selenium con Firefox (geckodriver lo gestiona Selenium Manager)
set NAVEGADOR=chrome && pytest tests/selenium -v     # o con Chrome
```
Las capturas de cada caso se guardan en `tests/selenium/evidencias/`.
