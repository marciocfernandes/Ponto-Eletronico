
import pytest

from sqlalchemy.engine import make_url
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models.usuario import Usuario
from config import TestConfig


@pytest.fixture
def app():
    # Verifica o banco ANTES de criar a aplicação.
    config = TestConfig()
    url = make_url(config.SQLALCHEMY_DATABASE_URI)

    if url.database != "pontoeletronico_testes":
        pytest.fail(
            "Segurança: os testes devem utilizar "
            "exclusivamente o banco pontoeletronico_testes."
        )

    aplicacao = create_app(TestConfig)
    aplicacao.config["TESTING"] = True

    yield aplicacao


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def usuarios_teste(app):
    with app.app_context():

        admin = Usuario(
            nome="Administrador Teste",
            email="admin_teste@exemplo.com",
            senha=generate_password_hash("SenhaTeste123"),
            perfil="ADMIN",
            ativo=True
        )

        funcionario = Usuario(
            nome="Funcionário Teste",
            email="funcionario_teste@exemplo.com",
            senha=generate_password_hash("SenhaTeste123"),
            perfil="FUNCIONARIO",
            ativo=True
        )

        db.session.add_all([admin, funcionario])
        db.session.commit()

        ids = {
            "admin": admin.id,
            "funcionario": funcionario.id
        }

        yield ids

        # Remove somente os usuários criados pelo teste.
        # Os testes desta etapa não criam registros de ponto.
        db.session.delete(
            db.session.get(Usuario, ids["admin"])
        )
        db.session.delete(
            db.session.get(Usuario, ids["funcionario"])
        )
        db.session.commit()


def fazer_login(client, email):
    resposta = client.get("/auth/login")
    assert resposta.status_code == 200

    from bs4 import BeautifulSoup

    html = BeautifulSoup(
        resposta.data,
        "html.parser"
    )

    token = html.find(
        "input",
        {"name": "csrf_token"}
    )["value"]

    return client.post(
        "/auth/login",
        data={
            "email": email,
            "senha": "SenhaTeste123",
            "csrf_token": token
        },
        follow_redirects=True
    )


def test_login_disponivel(client):
    resposta = client.get("/auth/login")
    assert resposta.status_code == 200


def test_api_status(client):
    resposta = client.get("/api/status")
    assert resposta.status_code == 200
    assert resposta.get_json()["status"] == "online"


def test_api_funcionarios_sem_login(client):
    resposta = client.get("/api/funcionarios")
    assert resposta.status_code == 401


def test_api_registros_sem_login(client):
    resposta = client.get("/api/registros")
    assert resposta.status_code == 401


def test_dashboard_sem_login(client):
    resposta = client.get("/home")
    assert resposta.status_code == 302


def test_admin_acessa_painel(client, usuarios_teste):
    fazer_login(client, "admin_teste@exemplo.com")

    resposta = client.get("/admin/dashboard")

    assert resposta.status_code == 200


def test_funcionario_nao_acessa_admin(
    client, usuarios_teste
):
    fazer_login(
        client,
        "funcionario_teste@exemplo.com"
    )

    resposta = client.get("/admin/dashboard")

    assert resposta.status_code == 403


def test_admin_acessa_api(client, usuarios_teste):
    fazer_login(client, "admin_teste@exemplo.com")

    resposta = client.get("/api/funcionarios")

    assert resposta.status_code == 200

    dados = resposta.get_json()

    assert "funcionarios" in dados


def test_funcionario_nao_acessa_api(
    client, usuarios_teste
):
    fazer_login(
        client,
        "funcionario_teste@exemplo.com"
    )

    resposta = client.get("/api/funcionarios")

    assert resposta.status_code == 403
