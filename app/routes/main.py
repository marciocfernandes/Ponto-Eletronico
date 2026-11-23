
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request
)

from flask_login import login_required, current_user

from app import db
from app.models.registro_ponto import RegistroPonto


main = Blueprint("main", __name__)


# =====================================================
# PÁGINA INICIAL
# =====================================================

@main.route("/")
def index():
    return redirect(url_for("auth.login"))


# =====================================================
# DASHBOARD DO FUNCIONÁRIO
# =====================================================

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

    # Identifica o próximo registro permitido
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

        else:
            status = "Trabalhando"

    # Cálculo da jornada
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


# =====================================================
# REGISTRAR PONTO
# =====================================================

@main.route("/registrar-ponto/<tipo>", methods=["POST"])
@login_required
def registrar_ponto(tipo):

    sequencia = [
        "ENTRADA",
        "SAIDA_INTERVALO",
        "RETORNO_INTERVALO",
        "SAIDA"
    ]

    # Valida o tipo de registro
    if tipo not in sequencia:

        flash("Tipo de ponto inválido.")

        return redirect(url_for("main.home"))

    # Impede registros de usuários desativados
    if not current_user.ativo:

        flash("Seu usuário está desativado.")

        return redirect(url_for("auth.logout"))

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

    # Impede mais de quatro registros
    if quantidade >= 4:

        flash("Todos os registros de hoje já foram realizados.")

        return redirect(url_for("main.home"))

    tipo_esperado = sequencia[quantidade]

    # Valida a sequência
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

    # =================================================
    # NOVA FUNCIONALIDADE: JUSTIFICATIVA DE ATRASO
    # =================================================

    justificativa = None

    if tipo == "ENTRADA":

        justificativa = request.form.get(
            "justificativa", ""
        ).strip()

        # Limite máximo de caracteres
        if len(justificativa) > 500:

            flash(
                "A justificativa deve ter no máximo "
                "500 caracteres."
            )

            return redirect(url_for("main.home"))

        # Campo vazio será armazenado como NULL
        justificativa = justificativa or None

    # =================================================
    # SALVAR REGISTRO NO POSTGRESQL
    # =================================================

    novo_registro = RegistroPonto(
        usuario_id=current_user.id,
        tipo=tipo,
        justificativa=justificativa
    )

    db.session.add(novo_registro)
    db.session.commit()

    if justificativa:
        flash(
            "Ponto registrado com sucesso! "
            "Justificativa armazenada."
        )
    else:
        flash("Ponto registrado com sucesso!")

    return redirect(url_for("main.home"))
