"""Prototipo funcional de RescateBot El Alto (Proyecto Integrador II)."""
import csv
import io
import os
import sqlite3
from functools import wraps

from flask import (Flask, Response, abort, flash, g, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash

from . import db as dbmod
from .reglas import (DIRECCIONES, UNIDADES, evaluar_alerta, evaluar_orden,
                     validar_lectura, validar_login)

MAX_INTENTOS = 5


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(
        SECRET_KEY=os.environ.get("RESCATEBOT_SECRET", "solo-para-desarrollo"),
        DATABASE=os.path.join(app.instance_path, "rescatebot.db"),
    )
    if config:
        app.config.update(config)
    os.makedirs(app.instance_path, exist_ok=True)
    app.teardown_appcontext(dbmod.close_db)

    @app.cli.command("init-db")
    def init_db_command():
        dbmod.init_db()
        print("Base de datos inicializada con datos de demostración.")

    # ------------------------------------------------------------ utilidades
    def login_requerido(rol=None):
        def deco(vista):
            @wraps(vista)
            def envuelta(*args, **kwargs):
                if "id_usuario" not in session:
                    return redirect(url_for("login"))
                if rol and session.get("rol") != rol:
                    abort(403)
                return vista(*args, **kwargs)
            return envuelta
        return deco

    def sesion_activa():
        return dbmod.get_db().execute(
            "SELECT s.*, r.codigo FROM sesion s JOIN robot r USING(id_robot) "
            "WHERE s.id_usuario = ? AND s.fin IS NULL", (session["id_usuario"],)).fetchone()

    def ultima(db, id_sesion, variable):
        fila = db.execute(
            "SELECT valor FROM lectura WHERE id_sesion=? AND variable=? "
            "ORDER BY id_lectura DESC LIMIT 1", (id_sesion, variable)).fetchone()
        return fila["valor"] if fila else None

    # ------------------------------------------------------------ F1: login
    @app.route("/", methods=["GET", "POST"])
    def login():
        errores = []
        correo = ""
        if request.method == "POST":
            correo = request.form.get("correo", "")
            clave = request.form.get("clave", "")
            errores = validar_login(correo, clave)
            if not errores:
                db = dbmod.get_db()
                u = db.execute("SELECT * FROM usuario WHERE correo = ?",
                               (correo.strip().lower(),)).fetchone()
                if u and u["intentos_fallidos"] >= MAX_INTENTOS:
                    errores.append("Cuenta bloqueada por intentos fallidos. Contacte al administrador.")
                elif u and check_password_hash(u["clave_hash"], clave):
                    db.execute("UPDATE usuario SET intentos_fallidos = 0 WHERE id_usuario = ?", (u["id_usuario"],))
                    db.commit()
                    session.clear()
                    session.update(id_usuario=u["id_usuario"], nombre=u["nombre"], rol=u["rol"])
                    return redirect(url_for("panel"))
                else:
                    if u:
                        db.execute("UPDATE usuario SET intentos_fallidos = intentos_fallidos + 1 "
                                   "WHERE id_usuario = ?", (u["id_usuario"],))
                        db.commit()
                    errores.append("Correo o contraseña incorrectos")
        return render_template("login.html", errores=errores, correo=correo)

    @app.route("/salir")
    def salir():
        session.clear()
        return redirect(url_for("login"))

    # ------------------------------------------------------------ F2: misión
    @app.route("/mision/nueva", methods=["GET", "POST"])
    @login_requerido()
    def mision_nueva():
        db = dbmod.get_db()
        robots = db.execute("SELECT * FROM robot ORDER BY codigo").fetchall()
        errores = []
        if request.method == "POST":
            id_robot = request.form.get("robot", "")
            escenario = request.form.get("escenario", "").strip()
            if not id_robot.isdigit():
                errores.append("Seleccione un robot")
            if len(escenario) < 3:
                errores.append("El escenario es obligatorio (mínimo 3 caracteres)")
            if not errores:
                try:
                    db.execute("INSERT INTO sesion (id_usuario, id_robot, escenario) VALUES (?,?,?)",
                               (session["id_usuario"], int(id_robot), escenario))
                    db.commit()
                    flash("Misión iniciada", "ok")
                    return redirect(url_for("panel"))
                except sqlite3.IntegrityError:
                    errores.append("Ese robot ya tiene una misión activa")
        return render_template("mision.html", robots=robots, errores=errores)

    @app.route("/mision/finalizar", methods=["POST"])
    @login_requerido()
    def mision_finalizar():
        s = sesion_activa()
        if s:
            db = dbmod.get_db()
            db.execute("UPDATE sesion SET fin = datetime('now','localtime') WHERE id_sesion=?", (s["id_sesion"],))
            db.commit()
            flash("Misión finalizada", "ok")
        return redirect(url_for("panel"))

    # ------------------------------------------------------------ F3/F4: panel, lecturas, órdenes
    @app.route("/panel")
    @login_requerido()
    def panel():
        s = sesion_activa()
        lecturas, alertas, ultimo = [], [], {}
        if s:
            db = dbmod.get_db()
            lecturas = db.execute("SELECT * FROM lectura WHERE id_sesion=? ORDER BY id_lectura DESC LIMIT 8",
                                  (s["id_sesion"],)).fetchall()
            alertas = db.execute("SELECT * FROM alerta WHERE id_sesion=? ORDER BY id_alerta DESC LIMIT 5",
                                 (s["id_sesion"],)).fetchall()
            ultimo = {v: ultima(db, s["id_sesion"], v) for v in UNIDADES}
        return render_template("panel.html", s=s, lecturas=lecturas, alertas=alertas,
                               ultimo=ultimo, unidades=UNIDADES, direcciones=sorted(DIRECCIONES))

    @app.route("/lecturas", methods=["POST"])
    @login_requerido()
    def registrar_lectura():
        s = sesion_activa()
        if not s:
            flash("Primero inicie una misión", "error")
            return redirect(url_for("panel"))
        variable = request.form.get("variable", "")
        ok, valor, mensaje = validar_lectura(variable, request.form.get("valor"))
        if not ok:
            flash(mensaje, "error")
            return redirect(url_for("panel"))
        db = dbmod.get_db()
        db.execute("INSERT INTO lectura (id_sesion, variable, valor, unidad, valida) VALUES (?,?,?,?,?)",
                   (s["id_sesion"], variable, valor, UNIDADES[variable], valor is not None))
        texto = evaluar_alerta(variable, valor)
        if texto:
            origen = "tecnica" if variable == "bateria" else "ambiental"
            db.execute("INSERT INTO alerta (id_sesion, origen, descripcion) VALUES (?,?,?)",
                       (s["id_sesion"], origen, texto))
        db.commit()
        flash(mensaje or "Lectura registrada", "aviso" if valor is None else "ok")
        return redirect(url_for("panel"))

    @app.route("/orden", methods=["POST"])
    @login_requerido()
    def orden():
        s = sesion_activa()
        if not s:
            flash("Primero inicie una misión", "error")
            return redirect(url_for("panel"))
        db = dbmod.get_db()
        resultado = evaluar_orden(request.form.get("direccion", ""),
                                  ultima(db, s["id_sesion"], "distancia"),
                                  ultima(db, s["id_sesion"], "bateria"))
        textos = {"EJECUTAR": ("Orden enviada al robot", "ok"),
                  "DETENER": ("Robot detenido", "ok"),
                  "RECHAZADA": ("Orden no válida", "error"),
                  "BLOQUEO_BATERIA": ("Bloqueado: batería baja", "error"),
                  "BLOQUEO_PROXIMIDAD": ("Parada por proximidad: obstáculo a menos de 20 cm", "error")}
        texto, tipo = textos[resultado]
        if resultado.startswith("BLOQUEO"):
            db.execute("INSERT INTO alerta (id_sesion, origen, descripcion) VALUES (?,?,?)",
                       (s["id_sesion"], "tecnica", texto))
            db.commit()
        flash(texto, tipo)
        return redirect(url_for("panel"))

    # ------------------------------------------------------------ F5: detecciones
    @app.route("/detecciones")
    @login_requerido(rol="supervisor")
    def detecciones():
        db = dbmod.get_db()
        estado = request.args.get("estado", "pendiente")
        filas = db.execute(
            "SELECT d.*, r.codigo, s.escenario FROM deteccion d JOIN sesion s USING(id_sesion) "
            "JOIN robot r USING(id_robot) WHERE (? = 'todas' OR d.decision = ?) ORDER BY d.confianza DESC",
            (estado, estado)).fetchall()
        return render_template("detecciones.html", filas=filas, estado=estado)

    @app.route("/detecciones/<int:id_det>", methods=["POST"])
    @login_requerido(rol="supervisor")
    def decidir(id_det):
        decision = request.form.get("decision")
        if decision not in ("confirmado", "descartado", "no_concluyente"):
            flash("Decisión no válida", "error")
        else:
            db = dbmod.get_db()
            cur = db.execute("UPDATE deteccion SET decision=?, revisado_por=? WHERE id_deteccion=?",
                             (decision, session["id_usuario"], id_det))
            db.commit()
            flash("Detección actualizada" if cur.rowcount else "La detección no existe",
                  "ok" if cur.rowcount else "error")
        return redirect(url_for("detecciones"))

    @app.route("/api/detecciones", methods=["POST"])
    def api_deteccion():
        """Endpoint usado por el servicio de visión (YOLO11n) para reportar candidatos."""
        datos = request.get_json(silent=True) or {}
        try:
            conf = float(datos["confianza"])
            cuadro = int(datos["nro_cuadro"])
            id_sesion = int(datos["id_sesion"])
        except (KeyError, TypeError, ValueError):
            return {"error": "Datos incompletos o inválidos"}, 400
        if not 0 <= conf <= 1 or cuadro < 0:
            return {"error": "confianza debe estar entre 0 y 1 y nro_cuadro >= 0"}, 400
        db = dbmod.get_db()
        try:
            cur = db.execute("INSERT INTO deteccion (id_sesion, nro_cuadro, confianza, sector) VALUES (?,?,?,?)",
                             (id_sesion, cuadro, conf, datos.get("sector")))
            db.commit()
        except sqlite3.IntegrityError:
            return {"error": "La sesión no existe"}, 404
        return {"id_deteccion": cur.lastrowid}, 201

    # ------------------------------------------------------------ F6: historial y exportación
    @app.route("/historial")
    @login_requerido()
    def historial():
        filas = dbmod.get_db().execute(
            "SELECT s.*, r.codigo, (SELECT count(*) FROM lectura l WHERE l.id_sesion=s.id_sesion) AS n_lect, "
            "(SELECT count(*) FROM alerta a WHERE a.id_sesion=s.id_sesion) AS n_alert "
            "FROM sesion s JOIN robot r USING(id_robot) ORDER BY s.id_sesion DESC").fetchall()
        return render_template("historial.html", filas=filas)

    @app.route("/historial/<int:id_sesion>.csv")
    @login_requerido()
    def exportar(id_sesion):
        db = dbmod.get_db()
        s = db.execute("SELECT * FROM sesion WHERE id_sesion=?", (id_sesion,)).fetchone()
        if s is None:
            abort(404)
        if s["fin"] is None:
            flash("Finalice la misión antes de exportar", "error")
            return redirect(url_for("historial"))
        salida = io.StringIO()
        w = csv.writer(salida)
        w.writerow(["id_lectura", "variable", "valor", "unidad", "valida", "fecha_hora"])
        for f in db.execute("SELECT * FROM lectura WHERE id_sesion=? ORDER BY id_lectura", (id_sesion,)):
            w.writerow([f["id_lectura"], f["variable"], "" if f["valor"] is None else f["valor"],
                        f["unidad"], bool(f["valida"]), f["fecha_hora"]])
        return Response(salida.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition": f"attachment; filename=sesion_{id_sesion}.csv"})

    @app.errorhandler(403)
    def prohibido(_e):
        return render_template("error.html", codigo=403, mensaje="No tiene permiso para ver esta página"), 403

    @app.errorhandler(404)
    def no_encontrado(_e):
        return render_template("error.html", codigo=404, mensaje="Página no encontrada"), 404

    return app
