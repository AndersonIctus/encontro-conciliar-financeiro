from dotenv import load_dotenv

import csv
import sys
import os
import re

from pathlib import Path
from typing import List, Set

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from application.src.conciliador import Conciliador
from application.src.models.extrato import Extrato
from application.src.planilha_utils import PlanilhaUtils

load_dotenv()

print("GOOGLE_SHEET_CREDENTIALS_PATH:", os.getenv("GOOGLE_SHEET_CREDENTIALS_PATH"))

def carregar_extratos(pasta_extratos: str) -> list[Extrato]:
    extratos = []
    caminho_pasta = Path(pasta_extratos)
    cabecalho_alvo = ["Data Lançamento", "Histórico", "Descrição", "Valor", "Saldo"]
    registros_unicos: Set[str] = set()
    
    for arquivo in caminho_pasta.glob("*.csv"):
        with open(arquivo, mode="r", encoding="utf-8") as f:
            linhas = f.readlines()
        
            # Procurar a linha do cabeçalho
            idx_cabecalho = -1
            for idx, linha in enumerate(linhas):
                if all(col in linha for col in cabecalho_alvo):
                    idx_cabecalho = idx
                    break

            if idx_cabecalho == -1:
                print(f"⚠️ Cabeçalho não encontrado no arquivo {arquivo.name}. Ignorando.")
                continue

            # Lê a partir do cabeçalho encontrado
            dados_csv = linhas[idx_cabecalho:]
            reader = csv.DictReader(dados_csv, delimiter=';')
            index = 0
            for linha in reader:
                data_lancamento = linha.get("Data Lançamento", "").strip()
                
                nome_bruto = linha.get("Descrição", "").strip()
                nome = re.sub(r'\d+', '', nome_bruto).strip()
                
                tipo = linha.get("Histórico", "").strip()
                saldo = linha.get("Saldo", "").strip()
                valor_str = linha.get("Valor", "0").replace(".", "").replace(",", ".").strip()

                try:
                    valor = float(valor_str)
                except ValueError:
                    print(f"❌ Valor inválido '{valor_str}' no arquivo {arquivo.name}, na linha {index + idx_cabecalho}. Usando 0.0.")
                    valor = 0.0
                    
                # Criar uma chave única para identificar duplicatas
                chave_unica = f"{nome.lower()}|{data_lancamento}|{valor:.2f}|{saldo}"
                if chave_unica in registros_unicos:
                    continue  # Pula se já existe
                registros_unicos.add(chave_unica)
                
                index = index + 1
                extratos.append(
                    Extrato(nome=nome, dt_lancamento=data_lancamento, tipo=tipo, valor=valor)
                )
    return extratos


def main():
    planilha_utils = PlanilhaUtils()
    extratos = carregar_extratos("extrato-bancario")

    conciliador = Conciliador(planilha_utils, extratos)
    conciliador.conciliar_encontreiro()

    conciliados = conciliador.get_conciliados_encontreiro()
    nao_conciliados = conciliador.get_nao_conciliados_encontreiro()
    
    print("-------------------- CONCILIADOS")
    for con in conciliados:
        print(con)
        
    print("-------------------- NÃO - CONCILIADOS")
    for n_con in nao_conciliados:
        print(n_con)

    # Path("conciliado").mkdir(exist_ok=True)
    # planilha_utils.salvar_excel_conciliado(conciliados, nao_conciliados)


if __name__ == "__main__":
    main()
    print(" ######################## FINAL ######################## ")
