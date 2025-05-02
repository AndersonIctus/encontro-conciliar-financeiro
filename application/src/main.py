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
from application.src.models.encontrista import Encontrista
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

def carregar_encontristas(pasta_extratos: str) -> list[Encontrista]:
    extratos = []
    caminho_pasta = Path(pasta_extratos) / 'valores-encontristas.csv'
    print(caminho_pasta.resolve())  # mostra o caminho absoluto

    
    with open(caminho_pasta, newline='', encoding='utf-8') as csvfile:
        leitor = csv.DictReader(csvfile, delimiter=';')
        
        index = 0
        for linha in leitor:
            id_str = linha["ID"]
            data = linha["Data Lançamento"]
            pagador = linha["Pagador"]
            tipo = linha["Tipo"]
            valor_str = linha["Valor"]
            
            try:
                id_ = int(id_str)
                valor = float(valor_str)
            except ValueError:
                print(f"❌ Valor inválido '{valor_str}' no arquivo valores-encontristas.csv, na linha {index + 1}. Usando 0.0.")
                valor = 0.0
                
            index = index + 1
            extratos.append(
                Encontrista(id=id_, pagador=pagador, dt_lancamento=data, tipo=tipo, valor=valor)
            )
    
    return extratos
    

def main():
    planilha_utils = PlanilhaUtils()
    extratos = carregar_extratos("extrato-bancario")
    encontristas = carregar_encontristas("extrato-encontrista")

    conciliador = Conciliador(planilha_utils, extratos, encontristas)
    # conciliador.conciliar_encontreiro()
    conciliador.conciliar_encontrista()

    # conciliados = conciliador.get_encontreiros_conciliados()
    # nao_conciliados = conciliador.get_encontreiros_nao_conciliados()
    
    # extrato_conciliado = conciliador.get_extratos_conciliados()
    
    # print("---------------------------------------------------")
    # print("---------------------------------------------------")
    # print("-------------------- ENCONTREIRO CONCILIADOS")
    # idx = 0
    # for con in conciliados:
    #     print('##  ' + str(idx))
    #     print(con)
    #     print('\r\n')
    #     idx = idx + 1
        
    # print("---------------------------------------------------")
    # print("---------------------------------------------------")
    # print("-------------------- ENCONTREIROS NÃO - CONCILIADOS")
    # idx = 0
    # for n_con in nao_conciliados:
    #     print('##  ' + str(idx))
    #     print(n_con)
    #     print('\r\n')
    #     idx = idx + 1
    
    
    encontrista_conciliado = conciliador.get_encontrista_conciliados()
    print("---------------------------------------------------")
    print("---------------------------------------------------")
    print("-------------------- ENCONTRISTA CONCILIADOS")
    idx = 0
    for con in encontrista_conciliado:
        print('##  ' + str(idx))
        print(con)
        print('\r\n')
        idx = idx + 1
        
    print("--------------------             ------------------")
        

    # Path("conciliado").mkdir(exist_ok=True)
    # planilha_utils.salvar_excel_conciliado(conciliados, nao_conciliados)


if __name__ == "__main__":
    main()
    print(" ######################## FINAL ######################## ")
