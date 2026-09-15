from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models.registro_ponto import RegistroPonto


main = Blueprint("main", __name__)


@main.route("/")
def index():
    return redirect(url_for("auth.login"))


@main.route("/home")
@login_required
def home():

    hoje = datetime.now().date()

    registros = (
        RegistroPonto.query
        .filter(
            RegistroPonto.usuario_id == current_user.id,
            db.func.date(RegistroPonto.data_hora) == hoje
        )
        .order_by(RegistroPonto.data_hora.asc())
        .all()
    )

    sequencia = [
        "ENTRADA",
        "SAIDA_INTERVALO",
        "RETORNO_INTERVALO",
        "SAIDA"
    ]

    quantidade = len(registros)

    if quantidade >= 4:

        proximo_tipo = None
        status = "Jornada finalizada"

    else:

        proximo_tipo = sequencia[quantidade]

        if quantidade == 0:
            status = "Não iniciou"

        elif quantidade == 1:
            status = "Trabalhando"

        elif quantidade == 2:
            status = "Em intervalo"

        elif quantidade == 3:
            status = "Trabalhando"

    tempo_trabalhado = None
    tempo_intervalo = None

    if quantidade >= 3:

        saida_intervalo = registros[1].data_hora
        retorno_intervalo = registros[2].data_hora

        intervalo = retorno_intervalo - saida_intervalo

        tempo_intervalo = str(intervalo).split(".")[0]

    if quantidade >= 4:

        entrada = registros[0].data_hora
        saida_intervalo = registros[1].data_hora
        retorno_intervalo = registros[2].data_hora
        saida = registros[3].data_hora

        periodo_1 = saida_intervalo - entrada
        periodo_2 = saida - retorno_intervalo

        trabalhado = periodo_1 + periodo_2

        tempo_trabalhado = str(trabalhado).split(".")[0]

    return render_template(
        "dashboard.html",
        usuario=current_user,
        registros=registros,
        proximo_tipo=proximo_tipo,
        status=status,
        tempo_trabalhado=tempo_trabalhado,
        tempo_intervalo=tempo_intervalo
    )


@main.route("/registrar-ponto/<tipo>", methods=["POST"])
@login_required
def registrar_ponto(tipo):

    tipos_validos = [
        "ENTRADA",
        "SAIDA_INTERVALO",
        "RETORNO_INTERVALO",
        "SAIDA"
    ]

    if tipo not in tipos_validos:

        flash("Tipo de ponto inválido.")

        return redirect(url_for("main.home"))

    hoje = datetime.now().date()

    registros_hoje = (
        RegistroPonto.query
        .filter(
            RegistroPonto.usuario_id == current_user.id,
            db.func.date(RegistroPonto.data_hora) == hoje
        )
        .order_by(RegistroPonto.data_hora.asc())
        .all()
    )

    quantidade = len(registros_hoje)

    sequencia = [
        "ENTRADA",
        "SAIDA_INTERVALO",
        "RETORNO_INTERVALO",
        "SAIDA"
    ]

    if quantidade >= 4:

        flash("Todos os registros de hoje já foram realizados.")

        return redirect(url_for("main.home"))

    tipo_esperado = sequencia[quantidade]

    if tipo != tipo_esperado:

        nomes = {
            "ENTRADA": "Entrada",
            "SAIDA_INTERVALO": "Saída para intervalo",
            "RETORNO_INTERVALO": "Retorno do intervalo",
            "SAIDA": "Saída"
        }

        flash(
            f"Registro inválido. "
            f"O próximo ponto deve ser: "
            f"{nomes[tipo_esperado]}."
        )

        return redirect(url_for("main.home"))

    novo_registro = RegistroPonto(
        usuario_id=current_user.id,
        tipo=tipo
    )

    db.session.add(novo_registro)
    db.session.commit()

    flash("Ponto registrado com sucesso!")

    return redirect(url_for("main.home"))


@main.route("/limpar-registros", methods=["POST"])
@login_required
def limpar_registros():

    hoje = datetime.now().date()

    registros = (
        RegistroPonto.query
        .filter(
            RegistroPonto.usuario_id == current_user.id,
            db.func.date(RegistroPonto.data_hora) == hoje
        )
        .all()
    )

    if not registros:

        flash("Não existem registros de hoje para apagar.")

        return redirect(url_for("main.home"))

    for registro in registros:
        db.session.delete(registro)

    db.session.commit()

    flash("Registros de teste de hoje foram apagados.")

    return redirect(url_for("main.home"))