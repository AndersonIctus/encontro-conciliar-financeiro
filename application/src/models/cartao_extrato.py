# Data da liberação;Forma de pagamento;Qtd. de vendas;Código de recebimento;Valor bruto;Descontos;Valor líquido
class CartaoExtrato:
    def __init__(self, cod_recebimento: str, data_liberacao: str, valor_bruto: float, desconto: float, valor_liquido: float):
        self.cod_recebimento = cod_recebimento
        self.data_liberacao = data_liberacao
        self.valor_bruto = valor_bruto
        self.desconto = desconto
        self.valor_liquido = valor_liquido
        self.valor_a_conciliar = valor_bruto

    def __repr__(self):
        return (
            f"CartaoExtrato(cod_recebimento = '{self.cod_recebimento}', data_liberacao = '{self.data_liberacao}', "
            f"valor_bruto = '{self.valor_bruto}', desconto = '{self.desconto}', valor_liquido = '{self.valor_liquido}', "
            f"valor_a_conciliar = '{self.valor_a_conciliar}')"
        )

    def __eq__(self, other):
        if not isinstance(other, CartaoExtrato):
            return False
        return self.cod_recebimento == other.cod_recebimento and self.data_liberacao == other.data_liberacao and self.valor_bruto == other.valor_bruto

    def __hash__(self):
        return hash((self.cod_recebimento, self.data_liberacao, self.valor_bruto))
