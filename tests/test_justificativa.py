
import pytest

from bs4 import BeautifulSoup
from sqlalchemy.engine import make_url
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models.usuario import Usuario
from app.models.registro_ponto import RegistroPonto
from config import TestConfig


@pytest.fixture
def ambiente():

    # Impede execução no banco principal
    url = make_url(TestConfig.SQLALCHEMY_DATABASE_URI)

    if url.database != "pontoeletronico_testes":
        pytest.fail(
            "Os testes devem utilizar o banco "
            "pontoeletronico_testes."
        )

    app = create_app(TestConfig)

    with app.app_context():
        usuario = Usuario(
            nome="Teste Justificativa",
            email="teste_justificativa@exemplo.com",
            senha=generate_password_hash("SenhaTeste123"),
            perfil="FUNCIONARIO",
            ativo=True
        )

        db.session.add(usuario)
        db.session.commit()

        usuario_id = usuario.id

    with app.test_client() as client:

        with client.session_transaction() as sessao:
            sessao["_user_id"] = str(usuario_id)
            sessao["_fresh"] = True

        yield client, app, usuario_id

    with app.app_context():

        RegistroPonto.query.filter_by(
            usuario_id=usuario_id
        ).delete()

        usuario = db.session.get(Usuario, usuario_id)

        if usuario:
            db.session.delete(usuario)

        db.session.commit()


def enviar_entrada(client, justificativa):

    # Obtém token CSRF válido do formulário
    resposta = client.get("/home")

    assert resposta.status_code == 200

    html = BeautifulSoup(
        resposta.data,
        "html.parser"
    )

    formulario = html.find(
        "form",
        action="/registrar-ponto/ENTRADA"
    )

    assert formulario is not None

    campo = formulario.find(
        "input",
        {"name": "csrf_token"}
    )

    assert campo is not None

    return client.post(
        "/registrar-ponto/ENTRADA",
        data={
            "csrf_token": campo["value"],
            "justificativa": justificativa
        },
        follow_redirects=True
    )


def buscar_entrada(app, usuario_id):

    with app.app_context():

        registro = RegistroPonto.query.filter_by(
            usuario_id=usuario_id,
            tipo="ENTRADA"
        ).first()

        if registro is None:
            return None

        return registro.justificativa


def contar_entradas(app, usuario_id):

    with app.app_context():
        return RegistroPonto.query.filter_by(
            usuario_id=usuario_id,
            tipo="ENTRADA"
        ).count()


def test_registrar_entrada_com_justificativa(ambiente):

    client, app, usuario_id = ambiente

    resposta = enviar_entrada(
        client,
        "Atraso devido ao trânsito."
    )

    assert resposta.status_code == 200
    assert contar_entradas(app, usuario_id) == 1

    assert buscar_entrada(
        app, usuario_id
    ) == "Atraso devido ao trânsito."


def test_registrar_entrada_sem_justificativa(ambiente):

    client, app, usuario_id = ambiente

    resposta = enviar_entrada(client, "")

    assert resposta.status_code == 200
    assert contar_entradas(app, usuario_id) == 1
    assert buscar_entrada(app, usuario_id) is None


def test_justificativa_acima_de_500_caracteres(ambiente):

    client, app, usuario_id = ambiente

    resposta = enviar_entrada(
        client,
        "A" * 501
    )

    assert resposta.status_code == 200

    # Entrada não deve ser gravada
    assert contar_entradas(app, usuario_id) == 0


def test_justificativa_com_500_caracteres(ambiente):

    client, app, usuario_id = ambiente

    justificativa = "A" * 500

    resposta = enviar_entrada(
        client,
        justificativa
    )

    assert resposta.status_code == 200
    assert contar_entradas(app, usuario_id) == 1

    assert buscar_entrada(
        app, usuario_id
    ) == justificativa
