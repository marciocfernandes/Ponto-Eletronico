
import pytest

from app import create_app
from config import TestConfig


@pytest.fixture
def client():
    app = create_app(TestConfig)

    with app.test_client() as cliente:
        yield cliente


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
