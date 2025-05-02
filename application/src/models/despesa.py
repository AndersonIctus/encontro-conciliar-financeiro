# ID;Data Lançamento;Descrição;Tipo;Valor;Observacao
class Despesa:
    def __init__(self, id: int, data: str, descricao: str,  tipo: str, valor: float, observacao: str):
        self.id = id
        self.data = data
        self.descricao = descricao
        self.tipo = tipo
        self.valor = valor
        self.observacao = observacao

    def __repr__(self):
        return (
            f"Despesa(id='{self.id}', dt_lancamento ='{self.data}', nome='{self.descricao}', "
            f"tipo='{self.tipo}', valor={self.valor}, observacao={self.observacao})"
        )

    def __eq__(self, other):
        if not isinstance(other, Despesa):
            return False
        return self.id == other.id and self.descricao == other.descricao and self.valor == other.valor and self.data == other.data

    def __hash__(self):
        return hash((self.id, self.data, self.descricao, self.valor))
