from typing import List

from application.src.models.extrato import Extrato
from application.src.planilha_utils import PlanilhaUtils


class Conciliador:
    def __init__(self, planilha_utils: PlanilhaUtils, extratos: List[Extrato]):
        self.planilha_utils = planilha_utils
        self.extratos = extratos
        self.conciliados = []
        self.nao_conciliados = []

    def conciliar(self):
        linhas_planilha = self.planilha_utils.carregar_dados_planilha_google()
        nomes_conciliados = set()

        for extrato in self.extratos:
            conciliado = False
            for linha in linhas_planilha:
                nome_pagador = str(linha.get("NOME DO PAGADOR:", "")).strip().lower()
                valor_pago = str(linha.get("VALOR PAGO:", "")).replace(",", ".").strip()

                if extrato.nome.lower() in nome_pagador and float(extrato.valor) == float(valor_pago):
                    nome_completo = linha.get("NOME COMPLETO", "")
                    instagram = linha.get("@ DO INSTAGRAM", "")
                    identificador = (nome_completo.lower(), instagram.lower())

                    if identificador not in nomes_conciliados:
                        self.conciliados.append({
                            "NOME COMPLETO": nome_completo,
                            "@ DO INSTAGRAM": instagram,
                            "NOME DO PAGADOR": nome_pagador,
                            "VALOR PAGO": valor_pago,
                            "DETALHES DO PAGAMENTO": linha.get("DETALHES DO PAGAMENTO", "")
                        })
                        nomes_conciliados.add(identificador)
                        conciliado = True
                        break

            if not conciliado:
                self.nao_conciliados.append({
                    "NOME": extrato.nome,
                    "VALOR": extrato.valor
                })

    def get_conciliados(self):
        return self.conciliados

    def get_nao_conciliados(self):
        return self.nao_conciliados
