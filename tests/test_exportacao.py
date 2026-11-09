
import csv
import io
from datetime import datetime

from app.services.exportacao import gerar_csv, gerar_pdf


def criar_relatorio_teste():
    data = datetime(2026, 11, 8)

    return {
        "jornadas": [
            {
                "funcionario": "Funcionario Teste",
                "data": data.date(),
                "horarios": {
                    "ENTRADA": data.replace(hour=8),
                    "SAIDA_INTERVALO": data.replace(hour=12),
                    "RETORNO_INTERVALO": data.replace(hour=13),
                    "SAIDA": data.replace(hour=17)
                },
                "intervalo": "01:00",
                "trabalhado": "08:00",
                "status": "Completa"
            }
        ],
        "total_trabalhado": "08:00",
        "total_intervalo": "01:00",
        "quantidade_jornadas": 1,
        "jornadas_completas": 1
    }


def test_gerar_csv():
    arquivo = gerar_csv(criar_relatorio_teste())

    assert isinstance(arquivo, io.BytesIO)

    conteudo = arquivo.getvalue().decode("utf-8-sig")

    assert "Funcionario Teste" in conteudo
    assert "08:00" in conteudo
    assert "01:00" in conteudo


def test_csv_possui_colunas():
    arquivo = gerar_csv(criar_relatorio_teste())

    conteudo = arquivo.getvalue().decode("utf-8-sig")

    linhas = list(
        csv.reader(io.StringIO(conteudo), delimiter=";")
    )

    assert linhas[0][0] == "Funcionário"
    assert linhas[0][1] == "Data"
    assert linhas[0][7] == "Horas trabalhadas"
    assert len(linhas[1]) == 9


def test_gerar_pdf():
    arquivo = gerar_pdf(
        criar_relatorio_teste(),
        "2026-11-01",
        "2026-11-30"
    )

    assert isinstance(arquivo, io.BytesIO)

    conteudo = arquivo.getvalue()

    assert conteudo.startswith(b"%PDF-")
    assert len(conteudo) > 1000


def test_relatorio_sem_registros():
    relatorio = {
        "jornadas": [],
        "total_trabalhado": "00:00",
        "total_intervalo": "00:00",
        "quantidade_jornadas": 0,
        "jornadas_completas": 0
    }

    csv_arquivo = gerar_csv(relatorio)

    pdf_arquivo = gerar_pdf(
        relatorio,
        "2026-11-01",
        "2026-11-30"
    )

    assert csv_arquivo.getvalue()
    assert pdf_arquivo.getvalue().startswith(b"%PDF-")
