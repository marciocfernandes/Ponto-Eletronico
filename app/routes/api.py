
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_login import current_user
from functools import wraps

from app import db
from app.models.usuario import Usuario
from app.models.registro_ponto import RegistroPonto


api = Blueprint("api", __name__, url_prefix="/api")


def api_admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):

        if not current_user.is_authenticated:
            return jsonify({
                "erro": "Autenticação necessária."
            }), 401

        if not current_user.ativo:
            return jsonify({
                "erro": "Usuário desativado."
            }), 403

        if current_user.perfil != "ADMIN":
            return jsonify({
                "erro": "Acesso permitido somente ao administrador."
            }), 403

        return func(*args, **kwargs)

    return decorated_view


@api.route("/status", methods=["GET"])
def status():
    return jsonify({
        "sistema": "Ponto Eletrônico",
        "api": "v1",
        "status": "online"
    }), 200


@api.route("/funcionarios", methods=["GET"])
@api_admin_required
def listar_funcionarios():

    funcionarios = (
        Usuario.query
        .filter_by(perfil="FUNCIONARIO")
        .order_by(Usuario.nome.asc())
        .all()
    )

    dados = []

    for funcionario in funcionarios:
        dados.append({
            "id": funcionario.id,
            "nome": funcionario.nome,
            "email": funcionario.email,
            "perfil": funcionario.perfil,
            "ativo": funcionario.ativo
        })

    return jsonify({
        "total": len(dados),
        "funcionarios": dados
    }), 200


@api.route("/registros", methods=["GET"])
@api_admin_required
def listar_registros():

    funcionario_id_texto = request.args.get("funcionario_id")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    funcionario_id = None

    if funcionario_id_texto:
        try:
            funcionario_id = int(funcionario_id_texto)

            if funcionario_id <= 0:
                raise ValueError

        except ValueError:
            return jsonify({
                "erro": "funcionario_id deve ser um inteiro positivo."
            }), 400

    consulta = (
        RegistroPonto.query
        .join(Usuario, RegistroPonto.usuario_id == Usuario.id)
        .filter(Usuario.perfil == "FUNCIONARIO")
    )

    if funcionario_id:
        consulta = consulta.filter(
            RegistroPonto.usuario_id == funcionario_id
        )

    try:
        if data_inicio:
            inicio = datetime.strptime(
                data_inicio, "%Y-%m-%d"
            )

            consulta = consulta.filter(
                RegistroPonto.data_hora >= inicio
            )

        if data_fim:
            fim = datetime.strptime(
                data_fim, "%Y-%m-%d"
            )

            consulta = consulta.filter(
                RegistroPonto.data_hora < fim + timedelta(days=1)
            )

        if data_inicio and data_fim and inicio > fim:
            return jsonify({
                "erro": "Data inicial maior que a data final."
            }), 400

    except (ValueError, OverflowError):
        return jsonify({
            "erro": "Utilize datas válidas no formato AAAA-MM-DD."
        }), 400

    registros = (
        consulta
        .order_by(RegistroPonto.data_hora.desc())
        .limit(500)
        .all()
    )

    dados = []

    for registro in registros:
        dados.append({
            "id": registro.id,
            "usuario_id": registro.usuario_id,
            "funcionario": registro.usuario.nome,
            "data_hora": registro.data_hora.isoformat(),
            "tipo": registro.tipo
        })

    return jsonify({
        "total": len(dados),
        "limite": 500,
        "registros": dados
    }), 200
