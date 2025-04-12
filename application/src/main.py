from dotenv import load_dotenv

import csv
from pathlib import Path

from application.src.conciliador import Conciliador
from application.src.models.extrato import Extrato
from application.src.planilha_utils import PlanilhaUtils

load_dotenv()

def carregar_extratos(pasta_extratos: str) -> list[Extrato]:
    extratos = []
    caminho_pasta = Path(pasta_extratos)
    for arquivo in caminho_pasta.glob("*.csv"):
        with open(arquivo, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for linha in reader:
                nome = linha.get("Nome", "").strip()
                valor_str = linha.get("Valor", "0").replace(",", ".").strip()
                try:
                    valor = float(valor_str)
                except ValueError:
                    valor = 0.0
                extratos.append(Extrato(nome=nome, valor=valor))
    return extratos


def main():
    planilha_utils = PlanilhaUtils()
    extratos = carregar_extratos("extrato-bancario")

    conciliador = Conciliador(planilha_utils, extratos)
    conciliador.conciliar()

    conciliados = conciliador.get_conciliados()
    nao_conciliados = conciliador.get_nao_conciliados()

    Path("conciliados").mkdir(exist_ok=True)
    planilha_utils.salvar_excel_conciliado(conciliados, nao_conciliados)


if __name__ == "__main__":
    main()
