from operator import eq
from typing import List
import unicodedata

from application.src.models.extrato import Extrato
from application.src.planilha_utils import PlanilhaUtils


class Conciliador:
    def __init__(self, planilha_utils: PlanilhaUtils, extratos: List[Extrato]):
        self.planilha_utils = planilha_utils
        self.extratos = extratos
        self.extratos_conciliados = []
        self.encontreiros_conciliados = []
        self.encontreiros_nao_conciliados = []
        self.extratos_nao_conciliados = []

    def conciliar_encontreiro(self):
        linhas_planilha = self.planilha_utils.carregar_dados_planilha_google()
        extratos_nao_conciliados = self.extratos.copy()
        encontreiros_nao_conciliados = linhas_planilha.copy()

        for encontrista in linhas_planilha:
            nome_pagador = str(encontrista.get("NOME DO PAGADOR:", "")).strip()
            valor_pago = str(encontrista.get("VALOR PAGO:", "")).replace(",", ".").replace('R$', '').strip()
            conciliado = False
            
            for extrato in extratos_nao_conciliados:
                if self._nomes_sao_similares(extrato.nome, nome_pagador) and float(extrato.valor) == float(valor_pago):
                    self.encontreiros_conciliados.append({
                        "NOME COMPLETO": encontrista.get("NOME COMPLETO", ""),
                        "@ DO INSTAGRAM": encontrista.get("@ DO INSTAGRAM", ""),
                        "NOME DO PAGADOR": nome_pagador,
                        "VALOR PAGO": valor_pago,
                        "DETALHES DO PAGAMENTO": encontrista.get("DETALHES DO PAGAMENTO", "")
                    })
                    self.extratos_conciliados.append(extrato)
                    extrato.num_conciliado = extrato.num_conciliado + 1

                    # Remover dos não conciliados
                    if encontrista in encontreiros_nao_conciliados:
                        encontreiros_nao_conciliados.remove(encontrista)
                    if extrato in extratos_nao_conciliados:
                        vezes_a_conciliar = int(float(valor_pago) / 90)
                        if extrato.num_conciliado == vezes_a_conciliar:
                            extratos_nao_conciliados.remove(extrato)
                        else:
                            print('Deve conciliar mais vezes ...')
                            print(extrato)
                    conciliado = True
                    break
            
            if conciliado is False: 
                print('Não foi possivel conciliar o encontrista!!')
                print('#########################')
                print(encontrista)

        # Salvar os restantes
        self.encontreiros_nao_conciliados = encontreiros_nao_conciliados
        self.extratos_nao_conciliados = extratos_nao_conciliados


    def get_encontreiros_conciliados(self):
        return self.encontreiros_conciliados

    def get_encontreiros_nao_conciliados(self):
        return self.encontreiros_nao_conciliados
    
    def get_extratos_nao_conciliados(self):
        return self.extratos_nao_conciliados
    
    def _nomes_sao_similares(self, nome_extrato: str, nome_pagador: str) -> bool:
        partes_extrato = self._normalizar(nome_extrato).split()
        partes_pagador = self._normalizar(nome_pagador).split()

        if len(partes_extrato) > 0 and partes_extrato[0] == 'ana' and partes_pagador[0] == 'ana':
            print('Ana ....')

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
    