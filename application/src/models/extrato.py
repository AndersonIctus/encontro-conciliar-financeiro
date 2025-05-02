# Data Lançamento;Histórico;Descrição;Valor;Saldo
class Extrato:
    def __init__(self, dt_lancamento: str, nome: str,  tipo: str, valor: float):
        self.dt_lancamento = dt_lancamento
        self.nome = nome
        self.tipo = tipo
        self.valor = valor
        self.valor_conciliado = valor

    def __repr__(self):
        return (
            f"Extrato(dt_lancamento ='{self.dt_lancamento}', nome='{self.nome}', "
            f"tipo='{self.tipo}', valor={self.valor})"
        )

    def __eq__(self, other):
        if not isinstance(other, Extrato):
            return False
        return self.nome == other.nome and self.valor == other.valor and self.dt_lancamento == other.dt_lancamento

    def __hash__(self):
        return hash((self.nome, self.valor))
