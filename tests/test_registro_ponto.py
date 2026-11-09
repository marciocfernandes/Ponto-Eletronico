
import pytest

from datetime import datetime, timedelta

from sqlalchemy.engine import make_url
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models.usuario import Usuario
from app.models.registro_ponto import RegistroPonto
from config import TestConfig


@pytest.fixture
def ambiente():
    # Proteção contra uso do banco principal
    url = make_url(TestConfig.SQLALCHEMY_DATABASE_URI)

    if url.database != "pontoeletronico_testes":
        pytest.fail(
            "Os testes devem utilizar o banco "
            "pontoeletronico_testes."
        )

    app = create_app(TestConfig)

    with app.app_context():
        usuario = Usuario(
            nome="Teste Registro",
            email="teste_registro@exemplo.com",
            senha=generate_password_hash("SenhaTeste123"),
            perfil="FUNCIONARIO",
            ativo=True
        )

        db.session.add(usuario)
        db.session.commit()

        usuario_id = usuario.id

    with app.test_client() as client:
        # Simula uma sessão autenticada
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


def enviar_ponto(client, tipo):
    # Busca o token CSRF na página
    resposta = client.get("/home")

    assert resposta.status_code == 200

    from bs4 import BeautifulSoup

    html = BeautifulSoup(
        resposta.data,
        "html.parser"
    )

    campo = html.find(
        "input",
        {"name": "csrf_token"}
    )

    assert campo is not None

    token = campo["value"]

    return client.post(
        f"/registrar-ponto/{tipo}",
        data={"csrf_token": token},
        follow_redirects=True
    )


def contar_registros(app, usuario_id):
    with app.app_context():
        return RegistroPonto.query.filter_by(
            usuario_id=usuario_id
        ).count()


def test_registrar_entrada(ambiente):
    client, app, usuario_id = ambiente

    resposta = enviar_ponto(client, "ENTRADA")

    assert resposta.status_code == 200
    assert contar_registros(app, usuario_id) == 1


def test_impedir_saida_antes_da_entrada(ambiente):
    client, app, usuario_id = ambiente

    resposta = enviar_ponto(client, "SAIDA")

    assert resposta.status_code == 200
    assert contar_registros(app, usuario_id) == 0


def test_impedir_entrada_duplicada(ambiente):
    client, app, usuario_id = ambiente

    enviar_ponto(client, "ENTRADA")
    enviar_ponto(client, "ENTRADA")

    assert contar_registros(app, usuario_id) == 1


def test_sequencia_completa(ambiente):
    client, app, usuario_id = ambiente

    sequencia = [
        "ENTRADA",
        "SAIDA_INTERVALO",
        "RETORNO_INTERVALO",
        "SAIDA"
    ]

    for tipo in sequencia:
        resposta = enviar_ponto(client, tipo)
        assert resposta.status_code == 200

    assert contar_registros(app, usuario_id) == 4



def test_impedir_quinto_registro(ambiente):
    client, app, usuario_id = ambiente

    sequencia = [
        "ENTRADA",
        "SAIDA_INTERVALO",
        "RETORNO_INTERVALO",
        "SAIDA"
    ]

    # Executa as quatro marcações permitidas
    for tipo in sequencia:
        resposta = enviar_ponto(client, tipo)
        assert resposta.status_code == 200

    # Confirma que a jornada possui quatro registros
    assert contar_registros(app, usuario_id) == 4

    # Obtém um token CSRF válido para testar a rota
    # diretamente, sem depender do botão no dashboard.
    from flask_wtf.csrf import generate_csrf

    with app.test_request_context():
        with client.session_transaction() as sessao:
            from flask import session
            session.update(dict(sessao))
            token = generate_csrf()
            sessao["csrf_token"] = session["csrf_token"]

    resposta = client.post(
        "/registrar-ponto/ENTRADA",
        data={"csrf_token": token},
        follow_redirects=True
    )

    assert resposta.status_code == 200

    # A quinta marcação não pode ser gravada
    assert contar_registros(app, usuario_id) == 4


def test_calculo_horas_trabalhadas(ambiente):
    client, app, usuario_id = ambiente

    hoje = datetime.now().replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0
    )

    horarios = [
        ("ENTRADA", hoje),
        ("SAIDA_INTERVALO", hoje + timedelta(hours=4)),
        ("RETORNO_INTERVALO", hoje + timedelta(hours=5)),
        ("SAIDA", hoje + timedelta(hours=9))
    ]

    with app.app_context():
        for tipo, horario in horarios:
            db.session.add(
                RegistroPonto(
                    usuario_id=usuario_id,
                    tipo=tipo,
                    data_hora=horario
                )
            )

        db.session.commit()

    resposta = client.get("/home")

    assert resposta.status_code == 200
    assert b"8:00:00" in resposta.data
    assert b"1:00:00" in resposta.data
