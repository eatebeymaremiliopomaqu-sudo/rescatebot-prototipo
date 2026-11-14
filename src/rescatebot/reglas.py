"""Reglas de negocio de RescateBot (sin dependencias de Flask).

Estas funciones son las que se analizan con prueba de caja blanca:
- validar_lectura(): valida una lectura de sensor antes de guardarla.
- evaluar_orden(): decide si una orden de movimiento se ejecuta o se bloquea.
"""
import re

# Rangos físicos de cada sensor (iguales a los CHECK de la base de datos)
RANGOS = {
    "distancia": (2.0, 400.0),      # HC-SR04, cm
    "temp_objeto": (-70.0, 380.0),  # MLX90614, °C
    "gas_rel": (0.0, 100.0),        # MQ-2, % relativo
    "bateria": (5.0, 9.0),          # V
}
UNIDADES = {"distancia": "cm", "temp_objeto": "C", "gas_rel": "%", "bateria": "V"}

DIRECCIONES = {"adelante", "atras", "izquierda", "derecha", "detener"}
DIST_BLOQUEO_CM = 20.0
BATERIA_MIN_V = 6.4

UMBRAL_ALERTA = {"gas_rel": 30.0, "temp_objeto": 60.0}

PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$")


def validar_lectura(variable, valor):
    """Valida una lectura. Devuelve (ok, valor_normalizado, mensaje).

    - Variable desconocida            -> (False, None, error)
    - Valor vacío (sensor sin dato)   -> (True, None, 'sin dato')   se guarda NULL
    - Valor no numérico               -> (False, None, error)
    - Valor fuera del rango físico    -> (False, None, error)
    - Valor válido                    -> (True, float, None)
    """
    if variable not in RANGOS:
        return False, None, "Variable desconocida"
    if valor is None or str(valor).strip() == "":
        return True, None, "Sin dato: se guarda como lectura inválida (NULL)"
    try:
        numero = float(str(valor).strip().replace(",", "."))  # acepta 23,5 (BUG-CP09)
    except ValueError:
        return False, None, "El valor debe ser numérico"
    minimo, maximo = RANGOS[variable]
    if minimo <= numero <= maximo:
        return True, numero, None
    return False, None, f"Fuera de rango: {variable} debe estar entre {minimo:g} y {maximo:g}"


def evaluar_orden(direccion, distancia_cm, bateria_v):
    """Decide qué hacer con una orden de movimiento.

    Devuelve uno de: RECHAZADA, DETENER, BLOQUEO_BATERIA, BLOQUEO_PROXIMIDAD, EJECUTAR.
    distancia_cm puede ser None (sensor sin eco): en ese caso no se bloquea por proximidad.
    """
    if direccion not in DIRECCIONES:
        return "RECHAZADA"
    if direccion == "detener":
        return "DETENER"
    if bateria_v is not None and bateria_v < BATERIA_MIN_V:
        return "BLOQUEO_BATERIA"
    if direccion == "adelante":
        if distancia_cm is not None and distancia_cm < DIST_BLOQUEO_CM:
            return "BLOQUEO_PROXIMIDAD"
    return "EJECUTAR"


def evaluar_alerta(variable, valor):
    """Devuelve el texto de alerta si la lectura supera su umbral, o None."""
    if valor is None:
        return None
    if variable == "bateria" and valor < BATERIA_MIN_V:
        return f"Batería baja ({valor:g} V)"
    umbral = UMBRAL_ALERTA.get(variable)
    if umbral is not None and valor > umbral:
        return f"{variable} supera el umbral ({valor:g} > {umbral:g})"
    return None


def validar_login(correo, clave):
    """Valida el formato de los campos de inicio de sesión. Devuelve lista de errores."""
    errores = []
    if not correo or not correo.strip():
        errores.append("El correo es obligatorio")
    elif not PATRON_CORREO.match(correo.strip().lower()):
        errores.append("El correo no tiene un formato válido")
    if not clave:
        errores.append("La contraseña es obligatoria")
    return errores
