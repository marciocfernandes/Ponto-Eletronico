
import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)

    with app.test_client() as client:
        yield client


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
