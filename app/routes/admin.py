from flask import Blueprint, render_template

from app.utils import admin_required
from app.models.usuario import Usuario
from app.models.registro_ponto import RegistroPonto


admin = Blueprint("admin", __name__, url_prefix="/admin")


@admin.route("/dashboard")
@admin_required
def dashboard():

    total_funcionarios = Usuario.query.filter_by(
        perfil="FUNCIONARIO"
    ).count()

    total_ativos = Usuario.query.filter_by(
        perfil="FUNCIONARIO",
        ativo=True
    ).count()

    total_registros = RegistroPonto.query.count()

    return render_template(
        "admin/dashboard.html",
        total_funcionarios=total_funcionarios,
        total_ativos=total_ativos,
        total_registros=total_registros
    )