from typing import List

from application.src.models.extrato import Extrato
from application.src.planilha_utils import PlanilhaUtils


class Conciliador:
    def __init__(self, planilha_utils: PlanilhaUtils, extratos: List[Extrato]):
        self.planilha_utils = planilha_utils
        self.extratos = extratos
        self.conciliados = []
        self.nao_conciliados = []

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

            conciliado = False

            for idx, extrato in enumerate(self.extratos):
                if idx in extratos_utilizados:
                    continue  # já foi usado

                if extrato.nome.lower() in nome_pagador and round(extrato.valor, 2) == round(valor_pago, 2):
                    nome_completo = linha.get("NOME COMPLETO", "")
                    instagram = linha.get("@ DO INSTAGRAM", "")
                    identificador = (nome_completo.lower(), instagram.lower())

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
                    "NOME COMPLETO": linha.get("NOME COMPLETO", ""),
                    "@ DO INSTAGRAM": linha.get("@ DO INSTAGRAM", ""),
                    "NOME DO PAGADOR": nome_pagador,
                    "VALOR PAGO": valor_pago
                })

        # adicionar os extratos não conciliados a uma nova lista
        for idx, extrato in enumerate(self.extratos):
            if idx not in extratos_utilizados:
                self.nao_conciliados_extrato.append({
                    "NOME": extrato.nome,
                    "VALOR": extrato.valor
                })


    def get_conciliados(self):
        return self.conciliados

    def get_nao_conciliados(self):
        return self.nao_conciliados
