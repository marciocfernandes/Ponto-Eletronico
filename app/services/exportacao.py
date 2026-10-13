
import csv
import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


def montar_linhas(relatorio):
    linhas = []

    for jornada in relatorio["jornadas"]:
        horarios = jornada["horarios"]

        def horario(tipo):
            valor = horarios.get(tipo)
            return valor.strftime("%H:%M:%S") if valor else "--"

        linhas.append([
            jornada["funcionario"],
            jornada["data"].strftime("%d/%m/%Y"),
            horario("ENTRADA"),
            horario("SAIDA_INTERVALO"),
            horario("RETORNO_INTERVALO"),
            horario("SAIDA"),
            jornada["intervalo"],
            jornada["trabalhado"],
            jornada["status"]
        ])

    return linhas


def gerar_csv(relatorio):
    arquivo = io.StringIO(newline="")

    escritor = csv.writer(
        arquivo,
        delimiter=";",
        lineterminator="\r\n"
    )

    escritor.writerow([
        "Funcionário",
        "Data",
        "Entrada",
        "Saída intervalo",
        "Retorno intervalo",
        "Saída",
        "Tempo intervalo",
        "Horas trabalhadas",
        "Status"
    ])

    escritor.writerows(montar_linhas(relatorio))

    escritor.writerow([])

    escritor.writerow([
        "Total trabalhado",
        relatorio["total_trabalhado"]
    ])

    escritor.writerow([
        "Total intervalo",
        relatorio["total_intervalo"]
    ])

    conteudo = "\ufeff" + arquivo.getvalue()

    buffer = io.BytesIO(conteudo.encode("utf-8"))
    buffer.seek(0)

    return buffer


def gerar_pdf(relatorio, data_inicio, data_fim):
    buffer = io.BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=25,
        leftMargin=25,
        topMargin=30,
        bottomMargin=30
    )

    estilos = getSampleStyleSheet()
    elementos = []

    elementos.append(
        Paragraph(
            "Ponto Eletrônico - Relatório de Jornada",
            estilos["Title"]
        )
    )

    elementos.append(Spacer(1, 12))

    elementos.append(
        Paragraph(
            f"Período: {data_inicio} até {data_fim}",
            estilos["Normal"]
        )
    )

    elementos.append(Spacer(1, 15))

    estilo_celula = estilos["BodyText"].clone(
        "CelulaRelatorio"
    )
    estilo_celula.fontName = "Helvetica"
    estilo_celula.fontSize = 7
    estilo_celula.leading = 9

    estilo_cabecalho = estilo_celula.clone(
        "CabecalhoRelatorio"
    )
    estilo_cabecalho.textColor = colors.white
    estilo_cabecalho.fontName = "Helvetica-Bold"

    cabecalho = [
        "Funcionário",
        "Data",
        "Entrada",
        "Saída int.",
        "Retorno",
        "Saída",
        "Intervalo",
        "Trabalhado",
        "Status"
    ]

    dados = [
        [
            Paragraph(escape(valor), estilo_cabecalho)
            for valor in cabecalho
        ]
    ]

    for linha in montar_linhas(relatorio):
        dados.append([
            Paragraph(escape(str(valor)), estilo_celula)
            for valor in linha
        ])

    tabela = Table(
        dados,
        colWidths=[140, 65, 65, 65, 65, 65, 65, 75, 80],
        repeatRows=1,
        hAlign="LEFT"
    )

    tabela.setStyle(TableStyle([
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            colors.HexColor("#343a40")
        ),
        (
            "ROWBACKGROUNDS",
            (0, 1),
            (-1, -1),
            [
                colors.white,
                colors.HexColor("#f1f3f5")
            ]
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.3,
            colors.grey
        ),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
    ]))

    elementos.append(tabela)
    elementos.append(Spacer(1, 18))

    elementos.append(
        Paragraph(
            f"Total trabalhado: {relatorio['total_trabalhado']}",
            estilos["Heading3"]
        )
    )

    elementos.append(
        Paragraph(
            f"Total de intervalo: {relatorio['total_intervalo']}",
            estilos["Normal"]
        )
    )

    documento.build(elementos)

    buffer.seek(0)

    return buffer
