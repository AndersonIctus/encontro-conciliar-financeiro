from typing import List

from application.src.models.extrato import Extrato
from application.src.planilha_utils import PlanilhaUtils


class Conciliador:
    def __init__(self, planilha_utils: PlanilhaUtils, extratos: List[Extrato]):
        self.planilha_utils = planilha_utils
        self.extratos = extratos
        self.conciliados_encontreiro = []
        self.nao_conciliados_encontreiro = []
        self.nao_conciliados_extrato = []

    def conciliar_encontreiro(self):
        linhas_planilha = self.planilha_utils.carregar_dados_planilha_google()
        nomes_conciliados = set()
        extratos_utilizados = set()

        for linha in linhas_planilha:
            nome_pagador = str(linha.get("NOME DO PAGADOR:", "")).strip().lower()
            valor_pago_str = str(linha.get("VALOR PAGO:", "")).replace(".", "").replace(",", ".").strip()

            try:
                valor_pago = float(valor_pago_str)
            except ValueError:
                continue  # pula se o valor não for válido
            
            nome_completo = linha.get("NOME COMPLETO", "").strip()
            instagram = linha.get("@ DO INSTAGRAM", "").strip()
            identificador = (nome_completo.lower(), instagram.lower())

            conciliado = False

            for idx, extrato in enumerate(self.extratos):
                if idx in extratos_utilizados:
                    continue  # já foi usado
                
                nome_extrato = extrato.nome.lower()
                valor_extrato = extrato.valor

                if self._nomes_sao_similares(nome_extrato, nome_pagador) and abs(valor_extrato - valor_pago) < 0.01:
                    if identificador not in nomes_conciliados:
                        self.conciliados_encontreiro.append({
                            "NOME COMPLETO": nome_completo,
                            "@ DO INSTAGRAM": instagram,
                            "NOME DO PAGADOR": nome_pagador,
                            "VALOR PAGO": valor_pago,
                            "DETALHES DO PAGAMENTO": linha.get("DETALHES DO PAGAMENTO", "")
                        })
                        nomes_conciliados.add(identificador)
                        extratos_utilizados.add(idx)
                        conciliado = True
                        break

            if not conciliado:
                self.nao_conciliados_encontreiro.append({
                    "NOME COMPLETO": nome_completo,
                    "@ DO INSTAGRAM": instagram,
                    "NOME DO PAGADOR": nome_pagador,
                    "VALOR PAGO": valor_pago,
                    "DETALHES DO PAGAMENTO": linha.get("DETALHES DO PAGAMENTO", "")
                })

        # adicionar os extratos não conciliados a uma nova lista
        for idx, extrato in enumerate(self.extratos):
            if idx not in extratos_utilizados:
                self.nao_conciliados_extrato.append({
                    "NOME": extrato.nome,
                    "VALOR": extrato.valor
                })

    def get_conciliados_encontreiro(self):
        return self.conciliados_encontreiro

    def get_nao_conciliados_encontreiro(self):
        return self.nao_conciliados_encontreiro
    
    def get_nao_conciliados_extrato(self):
        return self.nao_conciliados_extrato
    
    @staticmethod
    def _nomes_sao_similares(nome_extrato: str, nome_pagador: str) -> bool:
        partes_extrato = nome_extrato.lower().split()
        partes_pagador = nome_pagador.lower().split()

        if not partes_extrato or not partes_pagador:
            return False

        nome_principal_igual = partes_extrato[0] == partes_pagador[0]
        sobrenome_em_comum = any(sobrenome in partes_pagador[1:] for sobrenome in partes_extrato[1:])

        return nome_principal_igual and sobrenome_em_comum
