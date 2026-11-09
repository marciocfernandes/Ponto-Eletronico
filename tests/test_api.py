
import pytest

from sqlalchemy.engine import make_url
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models.usuario import Usuario
from config import TestConfig


@pytest.fixture
def ambiente_api():
    # Impede a utilização do banco principal
    url = make_url(TestConfig.SQLALCHEMY_DATABASE_URI)

    if url.database != "pontoeletronico_testes":
        pytest.fail(
            "Os testes devem utilizar exclusivamente "
            "o banco pontoeletronico_testes."
        )

    app = create_app(TestConfig)

    with app.app_context():
        admin = Usuario(
            nome="Admin API Teste",
            email="admin_api_teste@exemplo.com",
            senha=generate_password_hash("SenhaTeste123"),
            perfil="ADMIN",
            ativo=True
        )

        db.session.add(admin)
        db.session.commit()

        admin_id = admin.id

    with app.test_client() as client:
        # Autentica o administrador no ambiente de teste
        with client.session_transaction() as sessao:
            sessao["_user_id"] = str(admin_id)
            sessao["_fresh"] = True

        yield client

    with app.app_context():
        usuario = db.session.get(Usuario, admin_id)

        if usuario:
            db.session.delete(usuario)
            db.session.commit()


def test_api_registros_admin(ambiente_api):
    resposta = ambiente_api.get("/api/registros")

    assert resposta.status_code == 200

    dados = resposta.get_json()

    assert "total" in dados
    assert "limite" in dados
    assert "registros" in dados
    assert isinstance(dados["registros"], list)


def test_api_funcionario_id_invalido(ambiente_api):
    resposta = ambiente_api.get(
        "/api/registros?funcionario_id=abc"
    )

    assert resposta.status_code == 400
    assert "erro" in resposta.get_json()


def test_api_data_invalida(ambiente_api):
    resposta = ambiente_api.get(
        "/api/registros?data_inicio=2026-99-99"
    )

    assert resposta.status_code == 400
    assert "erro" in resposta.get_json()


def test_api_periodo_invalido(ambiente_api):
    resposta = ambiente_api.get(
        "/api/registros"
        "?data_inicio=2026-11-30"
        "&data_fim=2026-11-01"
    )

    assert resposta.status_code == 400
    assert "erro" in resposta.get_json()
