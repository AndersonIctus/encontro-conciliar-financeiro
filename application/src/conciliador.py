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
        
        # self.dados_conciliados: list[DadoConciliado] = []
        
        self.data_limite = "24/05/2025"
        

    def conciliar_encontreiro(self):
        linhas_planilha_encontreiro = self.planilha_utils.carregar_dados_planilha_google()
        self.encontreiros_nao_conciliados = linhas_planilha_encontreiro.copy()

        for encontreiro in linhas_planilha_encontreiro:
            nome_pagador = str(encontreiro.get("NOME DO PAGADOR:", "")).strip()
            
            if nome_pagador == 'CANCELADO':
                self.encontreiros_nao_conciliados.remove(encontreiro)
                continue
            
            
                
            valor_pago_att = float(str(encontreiro.get("VALOR PAGO:", "")).replace(",", ".").replace('R$', '').strip())
            if valor_pago_att == 0:
                valor_pago = 0
            else:
                valor_pago = valor_pago_att/100
            observacao = str(encontreiro.get("DETALHES DO PAGAMENTO", "")).strip()
            data_inscricao = str(encontreiro.get("Carimbo de data/hora", "")).strip()
            data_pgto = datetime.strptime(str(encontreiro.get("DATA DO PAGAMENTO", "")).strip(), '%d/%m/%Y')
            
            data_corte = datetime.strptime(self.data_limite, '%d/%m/%Y')
            if data_pgto > data_corte:
                self.encontreiros_nao_conciliados.remove(encontreiro)
                continue
            
            if 'serviços do encontro' in nome_pagador.lower():
                self.encontreiros_nao_conciliados.remove(encontreiro)
                dado_conciliado = DadoConciliado(
                    data_pgto, encontreiro.get("NOME COMPLETO", ""), 'ENTRADA', 'SERVIÇO', 'ENCONTREIRO', valor_pago,
                    { "observacao": observacao, "nome_pagador": nome_pagador,  "data_incricao": data_inscricao }
                )
                self.encontreiros_conciliados.append(dado_conciliado)
                continue
            
            if "dinheiro" in observacao.lower():
                self.encontreiros_nao_conciliados.remove(encontreiro)
                dado_conciliado = DadoConciliado(
                    data_pgto, encontreiro.get("NOME COMPLETO", ""), 'ENTRADA', 'DINHEIRO', 'ENCONTREIRO', valor_pago,
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
                    valor_pago_ficha = 0
                    if(extrato.valor < 90):
                        if "metade" in observacao.lower():
                            valor_pago_ficha = extrato.valor/2 # pagamentos menores, só com metade
                        else:
                            valor_pago_ficha = extrato.valor # Outros pagamentos menores com desconto em inscrição
                    else:
                        if "metade" in observacao.lower():
                            valor_pago_ficha = extrato.valor/2 # pagamentos menores, só com metade
                        else:
                            valor_pago_ficha = 90
                            
                    extrato.valor_a_conciliar = extrato.valor_a_conciliar - valor_pago_ficha
                    
                    dado_conciliado = DadoConciliado(
                        data_pgto, encontreiro.get("NOME COMPLETO", ""), 'ENTRADA', 'PIX', 'ENCONTREIRO', valor_pago_ficha,
                        { "data_incricao": data_inscricao, "nome_pagador": nome_pagador, 
                         "valor_extrato": extrato.valor, "observacao": observacao }
                    )
                    self.encontreiros_conciliados.append(dado_conciliado)

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
                dado_conciliado = DadoConciliado(
                    encontrista.dt_lancamento + ' 00:00:00', encontrista.pagador, 'ENTRADA', 'DINHEIRO', 'ENCONTRISTA', encontrista.valor,
                    { "observacao": encontrista.observacao }
                )
                self.valores_em_dinheiro.append(dado_conciliado)
                continue
            
            if encontrista.tipo == 'CARTAO':
                self.encontrista_nao_conciliado.remove(encontrista)
                self.cartao_nao_conciliado.append({
                    "DATA": encontrista.dt_lancamento + ' 00:00:00',
                    "DATA PGTO": encontrista.dt_lancamento,
                    "NOME": encontrista.pagador,
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
                    extrato.valor_a_conciliar = extrato.valor_a_conciliar - encontrista.valor
                    
                    dado_conciliado = DadoConciliado(
                        data_pgto, extrato.nome, 'ENTRADA', 'PIX', 'ENCONTRISTA', encontrista.valor,
                        { "data_incricao": encontrista.dt_lancamento, "id ficha": encontrista.id, 
                         "valor_extrato": extrato.valor, "observacao": encontrista.observacao }
                    )
                    self.encontristas_conciliados.append(dado_conciliado)

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
                    if tipo == 'ENCONTREIRO':
                        valor_a_conciliar = 90
                        if valor_pago < 90:
                            valor_a_conciliar = valor_pago
                        extrato.valor_a_conciliar = extrato.valor_a_conciliar - valor_a_conciliar
                    else:
                        valor_a_conciliar = valor_pago
                        extrato.valor_a_conciliar = extrato.valor_a_conciliar - valor_pago
                        
                    dado_conciliado = DadoConciliado(
                        data_pgto, nome_pagador, 'ENTRADA', 'CARTAO', tipo, valor_a_conciliar,
                        { "data_incricao": data_pgto, "id cartao": extrato.cod_recebimento, 
                         "valor_pago": valor_pago, "desconto": extrato.desconto, 
                         "valor_liquido": extrato.valor_liquido, "observacao": observacao }
                    )
                    self.cartao_conciliado.append(dado_conciliado)

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
                dado_conciliado = DadoConciliado(
                    despesa.data + ' 00:00:00', despesa.descricao, 'SAIDA', 'DINHEIRO', 'OUTRO', despesa.valor,
                    { "observacao": despesa.observacao }
                )
                self.valores_em_dinheiro.append(dado_conciliado)
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
                    extrato.valor_a_conciliar = extrato.valor_a_conciliar + despesa.valor
                    
                    dado_conciliado = DadoConciliado(
                        data_pgto, extrato.nome, 'SAIDA', despesa.tipo, 'OUTRO', despesa.valor,
                        { "data_incricao": data_pgto, "id despesa": despesa.id, "observacao": despesa.observacao }
                    )
                    self.despesas_conciliados.append(dado_conciliado)

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
            
            if outro_valor.forma_pgto == 'DINHEIRO':
                self.outros_nao_conciliado.remove(outro_valor)
                dado_conciliado = DadoConciliado(
                    outro_valor.data + ' 00:00:00', outro_valor.nome, 'ENTRADA', 'DINHEIRO', 
                    outro_valor.tipo, outro_valor.valor,
                    { "observacao": outro_valor.observacao }
                )
                self.valores_em_dinheiro.append(dado_conciliado)
                continue
            
            conciliado = False
            for extrato in self.extratos_nao_conciliados:
                data_extrato = datetime.strptime(extrato.dt_lancamento, '%d/%m/%Y')
                
                if data_pgto.year != data_extrato.year or data_pgto.month != data_extrato.month or data_pgto.day != data_extrato.day:
                    continue
                
                if self._nomes_sao_similares(extrato.nome, outro_valor.nome) and float(extrato.valor) == outro_valor.valor:
                    extrato.valor_a_conciliar = extrato.valor_a_conciliar - outro_valor.valor
                    
                    dado_conciliado = DadoConciliado(
                        outro_valor.data + ' 00:00:00', outro_valor.nome, 'ENTRADA', outro_valor.forma_pgto, 
                        outro_valor.tipo, outro_valor.valor,
                        { "observacao": outro_valor.observacao }
                    )
                    self.outros_conciliados.append(dado_conciliado)

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
    