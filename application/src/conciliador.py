from operator import eq
from typing import List
import unicodedata

from decimal import Decimal, ROUND_HALF_UP

from application.src.models.cartao_extrato import CartaoExtrato
from application.src.models.extrato import Extrato
from application.src.models.encontrista import Encontrista
from application.src.models.despesa import Despesa
from application.src.models.outro_valor import OutroValor
from application.src.models.dado_conciliado import DadoConciliado
from application.src.planilha_utils import PlanilhaUtils
from datetime import datetime


class Conciliador:
    def __init__(self, 
                 planilha_utils: PlanilhaUtils, 
                 extratos: List[Extrato], 
                 cartao_extratos: List[CartaoExtrato], 
                 encontristas: list[Encontrista], 
                 despesas: list[Despesa], 
                 outros_valores: list[OutroValor]
                ):
        self.planilha_utils = planilha_utils
        self.extratos_conciliados = []
        self.extratos_nao_conciliados = extratos.copy()
        self.encontreiros_conciliados: list[DadoConciliado] = []
        self.encontreiros_nao_conciliados = []
        self.encontristas_conciliados: list[DadoConciliado] = []
        self.encontrista_nao_conciliado = encontristas.copy()
        
        self.cartao_conciliado: list[DadoConciliado] = []
        self.cartao_nao_conciliado = []
        self.cartao_extrato_conciliados = []
        self.cartao_extrato_nao_conciliados = cartao_extratos.copy()
        
        self.outros_conciliados: list[DadoConciliado] = []
        self.outros_nao_conciliado = outros_valores.copy()
        
        self.despesas_conciliados: list[DadoConciliado] = []
        self.despesas_nao_conciliados = despesas.copy()
        self.valores_em_dinheiro: list[DadoConciliado] = []
        
        self.data_limite = "16/05/2025"
        

    def conciliar_encontreiro(self):
        linhas_planilha_encontreiro = self.planilha_utils.carregar_dados_planilha_google()
        self.encontreiros_nao_conciliados = linhas_planilha_encontreiro.copy()

        for encontreiro in linhas_planilha_encontreiro:
            nome_pagador = str(encontreiro.get("NOME DO PAGADOR:", "")).strip()
            valor_pago = float(str(encontreiro.get("VALOR PAGO:", "")).replace(",", ".").replace('R$', '').strip())/100
            observacao = str(encontreiro.get("DETALHES DO PAGAMENTO", "")).strip()
            data_inscricao = str(encontreiro.get("Carimbo de data/hora", "")).strip()
            data_pgto = datetime.strptime(str(encontreiro.get("DATA DO PAGAMENTO", "")).strip(), '%d/%m/%Y')
            
            data_corte = datetime.strptime(self.data_limite, '%d/%m/%Y')
            if data_pgto > data_corte:
                self.encontreiros_nao_conciliados.remove(encontreiro)
                continue
            
            if "dinheiro" in observacao.lower():
                self.encontreiros_nao_conciliados.remove(encontreiro)
                dado_conciliado = DadoConciliado(
                    data_pgto, encontreiro.get("NOME COMPLETO", ""), 'ENTRADA', 'ENCONTREIRO', 'DINHEIRO', valor_pago,
                    { "observacao": observacao, "nome_pagador": nome_pagador,  "data_incricao": data_inscricao }
                )
                self.valores_em_dinheiro.append(dado_conciliado)
                continue
            
            if "cartão" in observacao.lower() or "cartao" in observacao.lower():
                self.encontreiros_nao_conciliados.remove(encontreiro)
                self.cartao_nao_conciliado.append({
                    "DATA": data_inscricao,
                    "DATA PGTO": data_pgto,
                    "NOME": encontreiro.get("NOME COMPLETO", ""),
                    "NOME PAGADOR": nome_pagador,
                    "TIPO": "ENCONTREIRO",
                    "VALOR PAGO": valor_pago,
                    "OBSERVACOES": observacao
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
                        "OBSERVACOES": observacao
                    })
                    if(extrato.valor < 90):
                        if "metade" in observacao.lower():
                            extrato.valor_a_conciliar = extrato.valor_a_conciliar - extrato.valor/2 # pagamentos menores, só com metade
                        else:
                            extrato.valor_a_conciliar = extrato.valor_a_conciliar - extrato.valor # Outros pagamentos menores com desconto em inscrição
                    else:
                        if "metade" in observacao.lower():
                            extrato.valor_a_conciliar = extrato.valor_a_conciliar - extrato.valor/2 # pagamentos menores, só com metade
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

        print('---------------- FINALIZANDO CONCILIAÇÃO - ENCONTREIRO ------------')

    def conciliar_encontrista(self):
        encontristas = self.encontrista_nao_conciliado.copy()
        
        for encontrista in encontristas:
            data_pgto = datetime.strptime(encontrista.dt_lancamento, '%d/%m/%Y')
            
            data_corte = datetime.strptime(self.data_limite, '%d/%m/%Y')
            if data_pgto > data_corte:
                self.encontrista_nao_conciliado.remove(encontrista)
                continue
            
            if encontrista.tipo == 'DINHEIRO':
                self.encontrista_nao_conciliado.remove(encontrista)
                self.valores_em_dinheiro.append({
                    "DATA": encontrista.dt_lancamento + ' 00:00:00',
                    "NOME": encontrista.pagador,
                    "TIPO": "ENCONTRISTA",
                    "VALOR PAGO": encontrista.valor,
                    "OBSERVACOES": encontrista.observacao
                })
                continue
            
            if encontrista.tipo == 'CARTAO':
                self.encontrista_nao_conciliado.remove(encontrista)
                self.cartao_nao_conciliado.append({
                    "DATA": encontrista.dt_lancamento + ' 00:00:00',
                    "NOME PAGADOR": encontrista.pagador,
                    "TIPO": "ENCONTRISTA",
                    "VALOR PAGO": encontrista.valor,
                    "OBSERVACOES": encontrista.observacao
                })
                continue
            
            conciliado = False
            for extrato in self.extratos_nao_conciliados:
                data_extrato = datetime.strptime(extrato.dt_lancamento, '%d/%m/%Y')
                
                if data_pgto.year != data_extrato.year or data_pgto.month != data_extrato.month or data_pgto.day != data_extrato.day:
                    continue
                
                if self._nomes_sao_similares(extrato.nome, encontrista.pagador) and (extrato.valor == encontrista.valor or extrato.valor_a_conciliar == encontrista.valor):
                    self.encontristas_conciliados.append({
                        "ID FICHA": encontrista.id,
                        "DT INSCRIÇÃO": encontrista.dt_lancamento,
                        "DT EXTRATO": extrato.dt_lancamento,
                        "NOME COMPLETO": extrato.nome,
                        "VALOR PAGO": encontrista.valor,
                        "OBSERVACOES": encontrista.observacao
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
        
        print('---------------- FINALIZANDO CONCILIAÇÃO - ENCONTRISTA ------------')

    def conciliar_cartao(self):
        cartao_para_conciliar = self.cartao_nao_conciliado.copy()
        
        for cartao in cartao_para_conciliar:
            nome_pagador = str(cartao["NOME PAGADOR"]).strip()
            valor_pago = float(str(cartao["VALOR PAGO"]).strip())
            observacao = str(cartao["OBSERVACOES"]).strip()
            tipo = str(cartao["TIPO"]).strip()
            data_pgto = datetime.strptime(str(cartao["DATA"]).strip(), '%d/%m/%Y %H:%M:%S')
            
            data_corte = datetime.strptime(self.data_limite, '%d/%m/%Y')
            if data_pgto > data_corte:
                self.cartao_nao_conciliado.remove(cartao)
                continue
            
            conciliado = False
            for extrato in self.cartao_extrato_nao_conciliados:
                data_extrato = datetime.strptime(extrato.data_liberacao, '%d/%m/%Y')
                
                if data_pgto.year != data_extrato.year or data_pgto.month != data_extrato.month or data_pgto.day != data_extrato.day:
                    continue
                
                if float(extrato.valor_bruto) == valor_pago:
                    self.cartao_conciliado.append({
                        "ID CARTAO": extrato.cod_recebimento,
                        "DT INSCRIÇÃO": data_pgto,
                        "DT EXTRATO": extrato.data_liberacao,
                        "NOME COMPLETO": nome_pagador,
                        "VALOR PAGO": valor_pago,
                        "OBSERVACOES": observacao
                    })
                    if tipo == 'ENCONTREIRO':
                        valor_a_conciliar = 90
                        if valor_pago < 90:
                            valor_a_conciliar = valor_pago
                        extrato.valor_a_conciliar = extrato.valor_a_conciliar - valor_a_conciliar
                    else:
                        extrato.valor_a_conciliar = extrato.valor_a_conciliar - valor_pago

                    # Remover dos não conciliados
                    if cartao in self.cartao_nao_conciliado:
                        self.cartao_nao_conciliado.remove(cartao)
                        
                    if extrato in self.cartao_extrato_nao_conciliados:
                        if extrato.valor_a_conciliar == 0:
                            self.cartao_extrato_conciliados.append(extrato)
                            self.cartao_extrato_nao_conciliados.remove(extrato)
                        else:
                            print('Deve conciliar mais vezes ...')
                            print(extrato)
                    conciliado = True
                    break
            
            if conciliado is False: 
                print('Não foi possivel conciliar o cartão!!')
                print('#########################')
                print(cartao)
        
        print('---------------- FINALIZANDO CONCILIAÇÃO - CARTÃO ------------')
        
    def conciliar_despesas(self):
        despesas = self.despesas_nao_conciliados.copy()
        
        for despesa in despesas:
            data_pgto = datetime.strptime(despesa.data, '%d/%m/%Y')
            
            data_corte = datetime.strptime(self.data_limite, '%d/%m/%Y')
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
                    "OBSERVACOES": despesa.observacao
                })
                continue
            
            conciliado = False
            for extrato in self.extratos_nao_conciliados:
                data_extrato = datetime.strptime(extrato.dt_lancamento, '%d/%m/%Y')
                
                if data_pgto.year != data_extrato.year or data_pgto.month != data_extrato.month or data_pgto.day != data_extrato.day:
                    continue
                
                decimal_value = Decimal(extrato.valor * -1).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                decimal_despesa = Decimal(despesa.valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                decimal_equal = decimal_value.compare(decimal_despesa)
                if (
                    self._nomes_sao_similares(extrato.nome, despesa.descricao) 
                    and decimal_equal == Decimal(0)
                ):
                    self.despesas_conciliados.append({
                        "ID DESPESA": despesa.id,
                        "DT INSCRIÇÃO": despesa.data,
                        "DT EXTRATO": extrato.dt_lancamento,
                        "NOME COMPLETO": extrato.nome,
                        "VALOR PAGO": despesa.valor,
                        "OBSERVACOES": despesa.observacao
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
                print('Não foi possivel conciliar a despesa!!')
                print('#########################')
                print(despesa)
        
        print('---------------- FINALIZANDO CONCILIAÇÃO - DESPESAS ------------')

    def conciliar_outros(self):
        outros_valores = self.outros_nao_conciliado.copy()
        
        for outro_valor in outros_valores:
            data_pgto = datetime.strptime(outro_valor.data, '%d/%m/%Y')
            
            data_corte = datetime.strptime(self.data_limite, '%d/%m/%Y')
            if data_pgto > data_corte:
                self.outros_nao_conciliado.remove(outro_valor)
                continue
            
            if outro_valor.tipo == 'DINHEIRO':
                self.outros_nao_conciliado.remove(outro_valor)
                self.valores_em_dinheiro.append({
                    "DATA": outro_valor.data,
                    "NOME": outro_valor.nome,
                    "TIPO": "OFERTA",
                    "VALOR PAGO": outro_valor.valor,
                    "OBSERVACOES": outro_valor.observacao
                })
                continue
            
            conciliado = False
            for extrato in self.extratos_nao_conciliados:
                data_extrato = datetime.strptime(extrato.dt_lancamento, '%d/%m/%Y')
                
                if data_pgto.year != data_extrato.year or data_pgto.month != data_extrato.month or data_pgto.day != data_extrato.day:
                    continue
                
                if self._nomes_sao_similares(extrato.nome, outro_valor.nome) and float(extrato.valor) == outro_valor.valor:
                    self.outros_conciliados.append({
                        "ID OUTRO": outro_valor.id,
                        "DT INSCRIÇÃO": outro_valor.data,
                        "DT EXTRATO": extrato.dt_lancamento,
                        "NOME COMPLETO": extrato.nome,
                        "VALOR PAGO": outro_valor.valor,
                        "OBSERVACOES": outro_valor.observacao
                    })
                    extrato.valor_a_conciliar = extrato.valor_a_conciliar - outro_valor.valor

                    # Remover dos não conciliados
                    if outro_valor in self.outros_nao_conciliado:
                        self.outros_nao_conciliado.remove(outro_valor)
                        
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
                print('Não foi possivel conciliar o outro valor!!')
                print('#########################')
                print(outro_valor)
        
        print('---------------- FINALIZANDO CONCILIAÇÃO - OUTROS VALORES ------------')
    
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
    
    def get_cartao_conciliado(self):
        return self.cartao_conciliado
    
    def get_cartao_nao_conciliado(self):
        return self.cartao_nao_conciliado
    
    def get_cartao_extrato_conciliado(self):
        return self.cartao_extrato_conciliados
    
    def get_cartao_extrato_nao_conciliado(self):
        return self.cartao_extrato_nao_conciliados
    
    def get_despesas_conciliados(self):
        return self.despesas_conciliados
    
    def get_despesas_nao_conciliados(self):
        return self.despesas_nao_conciliados
    
    def get_outros_conciliados(self):
        return self.outros_conciliados
    
    def get_outros_nao_conciliados(self):
        return self.outros_nao_conciliado
    
    
    def get_valores_em_dinheiro(self):
        return self.valores_em_dinheiro

    # self.despesas_conciliados = []
    #     self.despesas_nao_conciliados = despesas.copy()
    
    def _nomes_sao_similares(self, nome_extrato: str, nome_pagador: str) -> bool:
        partes_extrato = self._normalizar(nome_extrato).split()
        partes_pagador = self._normalizar(nome_pagador).split()
        
        if nome_extrato == '' and nome_pagador == '':
            return True

        # if len(partes_extrato) > 0 and partes_extrato[0] == 'esdras' and partes_pagador[0] == 'esdras':
        #     print('Esdras ....')

        if not partes_extrato or not partes_pagador:
            return False

        nome_principal_igual = partes_extrato[0] == partes_pagador[0]
        sobrenome_em_comum = True
        if len(partes_pagador) > 1:
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
    