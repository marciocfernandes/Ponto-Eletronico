from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash
)
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

from app import db
from app.utils import admin_required
from app.models.usuario import Usuario
from app.models.registro_ponto import RegistroPonto
from datetime import datetime, timedelta

admin = Blueprint("admin", __name__, url_prefix="/admin")


@admin.route("/dashboard")
@admin_required
def dashboard():
    total_funcionarios = Usuario.query.filter_by(
        perfil="FUNCIONARIO"
    ).count()

    total_ativos = Usuario.query.filter_by(
        perfil="FUNCIONARIO", ativo=True
    ).count()

    total_registros = RegistroPonto.query.count()

    return render_template(
        "admin/dashboard.html",
        total_funcionarios=total_funcionarios,
        total_ativos=total_ativos,
        total_registros=total_registros
    )


@admin.route("/funcionarios")
@admin_required
def listar_funcionarios():
    funcionarios = (
        Usuario.query
        .filter_by(perfil="FUNCIONARIO")
        .order_by(Usuario.nome.asc())
        .all()
    )

    return render_template(
        "admin/funcionarios.html",
        funcionarios=funcionarios
    )


@admin.route("/funcionarios/novo", methods=["GET", "POST"])
@admin_required
def novo_funcionario():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        if not nome or not email or not senha:
            flash("Preencha todos os campos.")
            return redirect(url_for("admin.novo_funcionario"))

        if len(senha) < 8:
            flash("A senha deve ter pelo menos 8 caracteres.")
            return redirect(url_for("admin.novo_funcionario"))

        if Usuario.query.filter_by(email=email).first():
            flash("Este e-mail já está cadastrado.")
            return redirect(url_for("admin.novo_funcionario"))

        funcionario = Usuario(
            nome=nome,
            email=email,
            senha=generate_password_hash(senha),
            perfil="FUNCIONARIO",
            ativo=True
        )

        try:
            db.session.add(funcionario)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Não foi possível cadastrar: e-mail já utilizado.")
            return redirect(url_for("admin.novo_funcionario"))

        flash("Funcionário cadastrado com sucesso!")
        return redirect(url_for("admin.listar_funcionarios"))

    return render_template(
        "admin/form_funcionario.html",
        funcionario=None
    )


@admin.route("/funcionarios/<int:id>/editar", methods=["GET", "POST"])
@admin_required
def editar_funcionario(id):
    funcionario = db.get_or_404(Usuario, id)

    if funcionario.perfil != "FUNCIONARIO":
        flash("Este usuário não pode ser editado nesta área.")
        return redirect(url_for("admin.listar_funcionarios"))

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        if not nome or not email:
            flash("Nome e e-mail são obrigatórios.")
            return redirect(url_for("admin.editar_funcionario", id=id))

        existente = Usuario.query.filter_by(email=email).first()

        if existente and existente.id != funcionario.id:
            flash("Este e-mail já está cadastrado.")
            return redirect(url_for("admin.editar_funcionario", id=id))

        if senha and len(senha) < 8:
            flash("A nova senha deve ter pelo menos 8 caracteres.")
            return redirect(url_for("admin.editar_funcionario", id=id))

        funcionario.nome = nome
        funcionario.email = email

        if senha:
            funcionario.senha = generate_password_hash(senha)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Não foi possível salvar: e-mail já utilizado.")
            return redirect(url_for("admin.editar_funcionario", id=id))

        flash("Funcionário atualizado com sucesso!")
        return redirect(url_for("admin.listar_funcionarios"))

    return render_template(
        "admin/form_funcionario.html",
        funcionario=funcionario
    )


@admin.route("/funcionarios/<int:id>/alterar-status", methods=["POST"])
@admin_required
def alterar_status(id):
    funcionario = db.get_or_404(Usuario, id)

    if funcionario.perfil != "FUNCIONARIO":
        flash("Não é permitido alterar este usuário.")
        return redirect(url_for("admin.listar_funcionarios"))

    funcionario.ativo = not funcionario.ativo
    db.session.commit()

    flash("Status do funcionário atualizado!")
    return redirect(url_for("admin.listar_funcionarios"))

@admin.route("/registros")
@admin_required
def consultar_registros():

    funcionarios = (
        Usuario.query
        .filter_by(perfil="FUNCIONARIO")
        .order_by(Usuario.nome.asc())
        .all()
    )

    funcionario_id = request.args.get("funcionario_id", type=int)
    data_inicio = request.args.get("data_inicio", "").strip()
    data_fim = request.args.get("data_fim", "").strip()

    consulta = (
        db.session.query(RegistroPonto, Usuario)
        .join(Usuario, RegistroPonto.usuario_id == Usuario.id)
    )

    if funcionario_id:
        consulta = consulta.filter(
            Usuario.id == funcionario_id,
            Usuario.perfil == "FUNCIONARIO"
        )
    else:
        consulta = consulta.filter(
            Usuario.perfil == "FUNCIONARIO"
        )

    try:
        if data_inicio:
            inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
            consulta = consulta.filter(
                RegistroPonto.data_hora >= inicio
            )

        if data_fim:
            fim = datetime.strptime(data_fim, "%Y-%m-%d")
            fim_exclusivo = fim + timedelta(days=1)

            consulta = consulta.filter(
                RegistroPonto.data_hora < fim_exclusivo
            )

    except ValueError:
        flash("Informe datas válidas no formato AAAA-MM-DD.")
        return redirect(url_for("admin.consultar_registros"))

    registros = (
        consulta
        .order_by(RegistroPonto.data_hora.desc())
        .limit(500)
        .all()
    )

    return render_template(
        "admin/registros.html",
        registros=registros,
        funcionarios=funcionarios,
        funcionario_id=funcionario_id,
        data_inicio=data_inicio,
        data_fim=data_fim
    )