"""Capa de presentación (Flask). No contiene lógica de negocio: solo traduce
peticiones a llamadas de servicio y errores de dominio a mensajes claros."""
import os
from datetime import date, time
from functools import wraps

from flask import (
    Flask, abort, flash, g, redirect, render_template, request, session, url_for,
)

from medischedule.composicion import Servicios, construir_servicios
from medischedule.dominio.excepciones import ConflictoHorario, ErrorDominio, NoEncontrado


def crear_app(servicios: Servicios | None = None) -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "clave-solo-para-desarrollo")
    s = servicios or construir_servicios()
    app.config["SERVICIOS"] = s

    app.jinja_env.globals.update(
        medico_de=lambda c: s.catalogo.medico(c.medico_id),
        clinica_de=lambda c: s.catalogo.clinica(c.clinica_id),
    )

    def login_requerido(vista):
        @wraps(vista)
        def envoltura(*a, **kw):
            if "paciente_id" not in session:
                return redirect(url_for("login"))
            try:
                g.paciente = s.cuentas.obtener(session["paciente_id"])
            except NoEncontrado:
                session.clear()
                return redirect(url_for("login"))
            return vista(*a, **kw)
        return envoltura

    @app.errorhandler(NoEncontrado)
    def no_encontrado(e):
        return render_template("mensaje.html", titulo="No encontrado", mensaje=str(e)), 404

    # ---------- 1. Inicio de sesión / Registro / Recuperar ----------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            try:
                p = s.cuentas.iniciar_sesion(request.form["correo"], request.form["clave"])
                session["paciente_id"] = p.id
                return redirect(url_for("inicio"))
            except ErrorDominio as e:
                flash(str(e), "error")
        return render_template("login.html")

    @app.route("/registro", methods=["GET", "POST"])
    def registro():
        if request.method == "POST":
            f = request.form
            try:
                s.cuentas.registrar(f["nombre"], f["correo"], f.get("telefono", ""), f["clave"])
                flash("Cuenta creada. Inicia sesión.", "ok")
                return redirect(url_for("login"))
            except ErrorDominio as e:
                flash(str(e), "error")
        return render_template("registro.html")

    @app.route("/recuperar", methods=["GET", "POST"])
    def recuperar():
        if request.method == "POST":
            s.cuentas.recuperar_clave(request.form["correo"])
            flash("Si el correo existe, enviamos una contraseña temporal.", "ok")
            return redirect(url_for("login"))
        return render_template("recuperar.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    # ---------- 2. Inicio ----------
    @app.route("/")
    @login_requerido
    def inicio():
        pid = g.paciente.id
        return render_template(
            "inicio.html",
            proxima=s.citas.proxima(pid),
            total_proximas=len(s.citas.proximas(pid)),
            total_historial=len(s.citas.historial(pid)),
        )

    # ---------- 3. Agendar cita (clínica → especialidad → médico) ----------
    @app.route("/agendar")
    @login_requerido
    def agendar():
        clinica_id = request.args.get("clinica")
        especialidad = request.args.get("especialidad")
        ctx = {"clinicas": s.catalogo.clinicas(), "clinica_id": clinica_id,
               "especialidad": especialidad, "especialidades": [], "medicos": []}
        if clinica_id:
            ctx["especialidades"] = s.catalogo.especialidades(clinica_id)
        if clinica_id and especialidad:
            ctx["medicos"] = s.catalogo.medicos(clinica_id, especialidad)
        return render_template("agendar.html", **ctx)

    # ---------- 4. Calendario (fechas y horarios) ----------
    @app.route("/calendario/<medico_id>")
    @login_requerido
    def calendario(medico_id):
        medico = s.catalogo.medico(medico_id)
        fechas = s.citas.fechas_disponibles()
        try:
            fecha = date.fromisoformat(request.args.get("fecha", ""))
        except ValueError:
            fecha = fechas[0]
        return render_template(
            "calendario.html", medico=medico, fechas=fechas, fecha=fecha,
            horarios=s.citas.horarios(medico_id, fecha),
        )

    # ---------- 7. Confirmación (éxito o conflicto) ----------
    @app.route("/confirmar", methods=["POST"])
    @login_requerido
    def confirmar():
        medico_id = request.form["medico_id"]
        try:
            fecha = date.fromisoformat(request.form["fecha"])
            hora = time.fromisoformat(request.form["hora"])
            r = s.citas.agendar(g.paciente.id, medico_id, fecha, hora)
        except ConflictoHorario as e:
            return render_template("confirmacion.html", error=str(e), medico_id=medico_id), 409
        except (ErrorDominio, ValueError) as e:
            return render_template("confirmacion.html", error=str(e), medico_id=medico_id), 400
        if not r.notificado:
            flash("Tu cita está confirmada, pero no pudimos enviar el correo. "
                  "Revisa 'Mis citas'.", "warn")
        return redirect(url_for("confirmacion", cita_id=r.cita.id))

    @app.route("/confirmacion/<int:cita_id>")
    @login_requerido
    def confirmacion(cita_id):
        return render_template("confirmacion.html", cita=s.citas.obtener(cita_id, g.paciente.id))

    # ---------- 5. Mis citas ----------
    @app.route("/mis-citas")
    @login_requerido
    def mis_citas():
        pid = g.paciente.id
        return render_template("mis_citas.html", proximas=s.citas.proximas(pid),
                               historial=s.citas.historial(pid))

    @app.route("/citas/<int:cita_id>")
    @login_requerido
    def detalle_cita(cita_id):
        cita = s.citas.obtener(cita_id, g.paciente.id)
        return render_template("detalle.html", cita=cita,
                               cancelable=cita in s.citas.proximas(g.paciente.id))

    @app.route("/citas/<int:cita_id>/cancelar", methods=["POST"])
    @login_requerido
    def cancelar(cita_id):
        try:
            s.citas.cancelar(cita_id, g.paciente.id)
            flash("Cita cancelada.", "ok")
        except ErrorDominio as e:
            flash(str(e), "error")
        return redirect(url_for("mis_citas"))

    # ---------- 6. Perfil ----------
    @app.route("/perfil", methods=["GET", "POST"])
    @login_requerido
    def perfil():
        if request.method == "POST":
            try:
                s.cuentas.actualizar_perfil(g.paciente.id, request.form["nombre"],
                                            request.form.get("telefono", ""))
                flash("Datos actualizados.", "ok")
            except ErrorDominio as e:
                flash(str(e), "error")
            return redirect(url_for("perfil"))
        return render_template("perfil.html", paciente=g.paciente)

    return app
