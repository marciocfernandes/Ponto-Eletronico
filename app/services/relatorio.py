from collections import defaultdict
from datetime import timedelta


def formatar_duracao(duracao):
    if duracao is None:
        return "--"

    segundos = int(duracao.total_seconds())
    horas, resto = divmod(segundos, 3600)
    minutos, _ = divmod(resto, 60)

    return f"{horas:02d}:{minutos:02d}"


def gerar_relatorio(registros):
    agrupados = defaultdict(list)

    for registro in registros:
        chave = (
            registro.usuario_id,
            registro.data_hora.date()
        )
        agrupados[chave].append(registro)

    jornadas = []
    total_trabalhado = timedelta()
    total_intervalo = timedelta()

    tipos_esperados = [
        "ENTRADA",
        "SAIDA_INTERVALO",
        "RETORNO_INTERVALO",
        "SAIDA"
    ]

    for (usuario_id, data), marcacoes in sorted(
        agrupados.items(),
        key=lambda item: (item[0][1], item[0][0]),
        reverse=True
    ):
        marcacoes.sort(key=lambda r: r.data_hora)

        horarios = {
            "ENTRADA": None,
            "SAIDA_INTERVALO": None,
            "RETORNO_INTERVALO": None,
            "SAIDA": None
        }

        tipos = [r.tipo for r in marcacoes]

        completa = (
            tipos == tipos_esperados
            and all(
                marcacoes[i].data_hora <= marcacoes[i + 1].data_hora
                for i in range(3)
            )
        )

        for registro in marcacoes:
            if registro.tipo in horarios:
                horarios[registro.tipo] = registro.data_hora

        trabalhado = None
        intervalo = None

        if completa:
            entrada = horarios["ENTRADA"]
            saida_intervalo = horarios["SAIDA_INTERVALO"]
            retorno = horarios["RETORNO_INTERVALO"]
            saida = horarios["SAIDA"]

            intervalo = retorno - saida_intervalo

            trabalhado = (
                (saida_intervalo - entrada)
                + (saida - retorno)
            )

            total_trabalhado += trabalhado
            total_intervalo += intervalo

        jornadas.append({
            "usuario_id": usuario_id,
            "funcionario": marcacoes[0].usuario.nome,
            "data": data,
            "horarios": horarios,
            "trabalhado": formatar_duracao(trabalhado),
            "intervalo": formatar_duracao(intervalo),
            "status": "Completa" if completa else "Incompleta"
        })

    return {
        "jornadas": jornadas,
        "total_trabalhado": formatar_duracao(total_trabalhado),
        "total_intervalo": formatar_duracao(total_intervalo),
        "quantidade_jornadas": len(jornadas),
        "jornadas_completas": sum(
            1 for jornada in jornadas
            if jornada["status"] == "Completa"
        )
    }