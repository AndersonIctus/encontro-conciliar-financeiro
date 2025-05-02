from operator import eq
from typing import List
import unicodedata

from application.src.models.extrato import Extrato
from application.src.models.encontrista import Encontrista
from application.src.models.despesa import Despesa
from application.src.planilha_utils import PlanilhaUtils
from datetime import datetime


class Conciliador:
    def __init__(self, planilha_utils: PlanilhaUtils, extratos: List[Extrato], encontristas: list[Encontrista], despesas: list[Despesa]):
        self.planilha_utils = planilha_utils
        self.extratos_conciliados = []
        self.extratos_nao_conciliados = extratos.copy()
        self.encontreiros_conciliados = []
        self.encontreiros_nao_conciliados = []
        self.encontristas_conciliados = []
        self.encontrista_nao_conciliado = encontristas.copy()
        
        self.despesas_conciliados = []
        self.despesas_nao_conciliados = despesas.copy()
        self.valores_em_dinheiro = []
        

    def conciliar_encontreiro(self):
        linhas_planilha_encontreiro = self.planilha_utils.carregar_dados_planilha_google()
        self.encontreiros_nao_conciliados = linhas_planilha_encontreiro.copy()

        for encontreiro in linhas_planilha_encontreiro:
            nome_pagador = str(encontreiro.get("NOME DO PAGADOR:", "")).strip()
            valor_pago = float(str(encontreiro.get("VALOR PAGO:", "")).replace(",", ".").replace('R$', '').strip())/100
            observacao = str(encontreiro.get("DETALHES DO PAGAMENTO", "")).strip()
            data_inscricao = str(encontreiro.get("Carimbo de data/hora", "")).strip()
            data_pgto = datetime.strptime(str(encontreiro.get("DATA DO PAGAMENTO", "")).strip(), '%d/%m/%Y')
            
            data_corte = datetime.strptime('02/05/2025', '%d/%m/%Y')
            if data_pgto > data_corte:
                self.encontreiros_nao_conciliados.remove(encontreiro)
                continue
            
            if "dinheiro" in observacao.lower():
                self.encontreiros_nao_conciliados.remove(encontreiro)
                self.valores_em_dinheiro.append({
                    "DATA": data_inscricao,
                    "NOME": encontreiro.get("NOME COMPLETO", ""),
                    "TIPO": "ENCONTREIRO",
                    "VALOR PAGO": valor_pago,
                    "DETALHES DO PAGAMENTO": observacao
                })
                continue
            
            conciliado = False
            for extrato in self.extratos_nao_conciliados:
                data_extrato = datetime.strptime(extrato.dt_lancamento, '%d/%m/%Y')
                
                if data_pgto.year != data_extrato.year or data_pgto.month != data_extrato.month or data_pgto.day != data_extrato.day:
                    continue
                
                if self._nomes_sao_similares(extrato.nome, nome_pagador) and float(extrato.valor) == valor_pago:
                    self.encontreiros_conciliados.append({
                        "DT INSCRIÇÃO": data_inscricao,
                        "DT EXTRATO": extrato.dt_lancamento,
                        "NOME COMPLETO": encontreiro.get("NOME COMPLETO", ""),
                        "NOME DO PAGADOR": nome_pagador,
                        "VALOR PAGO": valor_pago,
                        "DETALHES DO PAGAMENTO": encontreiro.get("DETALHES DO PAGAMENTO", "")
                    })
                    if(extrato.valor == 30):
                        extrato.valor_a_conciliar = extrato.valor_a_conciliar - 30 # Pagamento de inscrição somente com a Blusa
                    else:
                        extrato.valor_a_conciliar = extrato.valor_a_conciliar - 90

                    # Remover dos não conciliados
                    if encontreiro in self.encontreiros_nao_conciliados:
                        self.encontreiros_nao_conciliados.remove(encontreiro)
                    if extrato in self.extratos_nao_conciliados:
                        if extrato.valor_a_conciliar == 0:
                            self.extratos_conciliados.append(extrato)
                            self.extratos_nao_conciliados.remove(extrato)
                        else:
                            print('Deve conciliar mais vezes ...')
                            print(extrato)
                    conciliado = True
                    break
            
            if conciliado is False: 
                print('Não foi possivel conciliar o encontreiro!!')
                print('#########################')
                print(encontreiro)

        print('---------------- FINALIZANDO CONCILIAÇÃO ------------')

    def conciliar_encontrista(self):
        encontristas = self.encontrista_nao_conciliado.copy()
        
        for encontrista in encontristas:
            data_pgto = datetime.strptime(encontrista.dt_lancamento, '%d/%m/%Y')
            
            data_corte = datetime.strptime('02/05/2025', '%d/%m/%Y')
            if data_pgto > data_corte:
                self.encontrista_nao_conciliado.remove(encontrista)
                continue
            
            if encontrista.tipo == 'DINHEIRO':
                self.encontrista_nao_conciliado.remove(encontrista)
                self.valores_em_dinheiro.append({
                    "DATA": encontrista.dt_lancamento,
                    "NOME": encontrista.pagador,
                    "TIPO": "ENCONTRISTA",
                    "VALOR PAGO": encontrista.valor,
                    "DETALHES DO PAGAMENTO": encontrista.observacao
                })
                continue
            
            conciliado = False
            for extrato in self.extratos_nao_conciliados:
                data_extrato = datetime.strptime(extrato.dt_lancamento, '%d/%m/%Y')
                
                if data_pgto.year != data_extrato.year or data_pgto.month != data_extrato.month or data_pgto.day != data_extrato.day:
                    continue
                
                if self._nomes_sao_similares(extrato.nome, encontrista.pagador) and extrato.valor == encontrista.valor:
                    self.encontristas_conciliados.append({
                        "ID FICHA": encontrista.id,
                        "DT INSCRIÇÃO": encontrista.dt_lancamento,
                        "DT EXTRATO": extrato.dt_lancamento,
                        "NOME COMPLETO": extrato.nome,
                        "VALOR PAGO": encontrista.valor
                    })
                    extrato.valor_a_conciliar = extrato.valor_a_conciliar - encontrista.valor

                    # Remover dos não conciliados
                    if encontrista in self.encontrista_nao_conciliado:
                        self.encontrista_nao_conciliado.remove(encontrista)
                        
                    if extrato in self.extratos_nao_conciliados:
                        if extrato.valor_a_conciliar == 0:
                            self.extratos_conciliados.append(extrato)
                            self.extratos_nao_conciliados.remove(extrato)
                        else:
                            print('Deve conciliar mais vezes ...')
                            print(extrato)
                    conciliado = True
                    break
            
            if conciliado is False: 
                print('Não foi possivel conciliar o encontrista!!')
                print('#########################')
                print(encontrista)
        
        print('---------------- FINALIZANDO CONCILIAÇÃO ------------')

    def conciliar_despesas(self):
        despesas = self.despesas_nao_conciliados.copy()
        
        for despesa in despesas:
            data_pgto = datetime.strptime(despesa.data, '%d/%m/%Y')
            
            data_corte = datetime.strptime('02/05/2025', '%d/%m/%Y')
            if data_pgto > data_corte:
                self.despesas_nao_conciliados.remove(despesa)
                continue
            
            if despesa.tipo == 'DINHEIRO':
                self.despesas_nao_conciliados.remove(despesa)
                self.valores_em_dinheiro.append({
                    "DATA": despesa.data,
                    "NOME": despesa.descricao,
                    "TIPO": "DESPESA",
                    "VALOR PAGO": despesa.valor,
                    "DETALHES DO PAGAMENTO": despesa.observacao
                })
                continue
            
            conciliado = False
            for extrato in self.extratos_nao_conciliados:
                data_extrato = datetime.strptime(extrato.dt_lancamento, '%d/%m/%Y')
                
                if data_pgto.year != data_extrato.year or data_pgto.month != data_extrato.month or data_pgto.day != data_extrato.day:
                    continue
                
                if self._nomes_sao_similares(extrato.nome, despesa.descricao) and (float(extrato.valor) * -1) == despesa.valor:
                    self.despesas_conciliados.append({
                        "ID FICHA": despesa.id,
                        "DT INSCRIÇÃO": despesa.data,
                        "DT EXTRATO": extrato.dt_lancamento,
                        "NOME COMPLETO": extrato.nome,
                        "VALOR PAGO": despesa.valor
                    })
                    extrato.valor_a_conciliar = extrato.valor_a_conciliar + despesa.valor

                    # Remover dos não conciliados
                    if despesa in self.despesas_nao_conciliados:
                        self.despesas_nao_conciliados.remove(despesa)
                        
                    if extrato in self.extratos_nao_conciliados:
                        if extrato.valor_a_conciliar == 0:
                            self.extratos_conciliados.append(extrato)
                            self.extratos_nao_conciliados.remove(extrato)
                        else:
                            print('Deve conciliar mais vezes ...')
                            print(extrato)
                    conciliado = True
                    break
            
            if conciliado is False: 
                print('Não foi possivel conciliar o encontrista!!')
                print('#########################')
                print(despesa)
        
        print('---------------- FINALIZANDO CONCILIAÇÃO ------------')

# #######################################################################################################
# #######################################################################################################
# #######################################################################################################
    def get_encontreiros_conciliados(self):
        return self.encontreiros_conciliados

    def get_encontreiros_nao_conciliados(self):
        return self.encontreiros_nao_conciliados
    
    def get_encontrista_conciliados(self):
        return self.encontristas_conciliados

    def get_encontrista_nao_conciliados(self):
        return self.encontrista_nao_conciliado
    
    def get_extratos_nao_conciliados(self):
        return self.extratos_nao_conciliados
    
    def get_extratos_conciliados(self):
        return self.extratos_conciliados
    
    def get_despesas_conciliados(self):
        return self.despesas_conciliados
    
    def get_despesas_nao_conciliados(self):
        return self.despesas_nao_conciliados
    
    def get_valores_em_dinheiro(self):
        return self.valores_em_dinheiro

    # self.despesas_conciliados = []
    #     self.despesas_nao_conciliados = despesas.copy()
    
    def _nomes_sao_similares(self, nome_extrato: str, nome_pagador: str) -> bool:
        partes_extrato = self._normalizar(nome_extrato).split()
        partes_pagador = self._normalizar(nome_pagador).split()

        # if len(partes_extrato) > 0 and partes_extrato[0] == 'esdras' and partes_pagador[0] == 'esdras':
        #     print('Esdras ....')

        if not partes_extrato or not partes_pagador:
            return False

        nome_principal_igual = partes_extrato[0] == partes_pagador[0]
        sobrenome_em_comum = any(sobrenome in partes_pagador[1:] for sobrenome in partes_extrato[1:])

        return nome_principal_igual and sobrenome_em_comum
    
    def _normalizar(self, texto: str) -> str:
        texto = texto.lower().strip()
        texto = unicodedata.normalize('NFKD', texto)
        return ''.join(c for c in texto if not unicodedata.combining(c))

    def _extrair_nomes_de_detalhes(self, detalhes: str) -> list[str]:
        """
        Extrai nomes de encontristas do campo 'DETALHES DO PAGAMENTO'.
        Espera o padrão: 'Encontreiro X: Nome Completo'
        """
        nomes = []
        linhas = detalhes.split("\n")
        for linha in linhas:
            if ":" in linha:
                partes = linha.split(":")
                if len(partes) > 1:
                    nome = partes[1].strip()
                    if nome:
                        nomes.append(nome)
        return nomes
    