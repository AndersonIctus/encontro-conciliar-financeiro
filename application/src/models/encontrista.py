# ID;Data Lançamento;Pagador;Tipo;Valor
class Encontrista:
    def __init__(self, id: int, dt_lancamento: str, pagador: str,  tipo: str, valor: float, observacao: str):
        self.id = id
        self.dt_lancamento = dt_lancamento
        self.pagador = pagador
        self.tipo = tipo
        self.valor = valor
        self.observacao = observacao

    def __repr__(self):
        return (
            f"Encontrista(id='{self.id}', dt_lancamento ='{self.dt_lancamento}', nome='{self.pagador}', "
            f"tipo='{self.tipo}', valor={self.valor}, observacao={self.observacao})"
        )

    def __eq__(self, other):
        if not isinstance(other, Encontrista):
            return False
        return self.id == other.id and self.pagador == other.pagador and self.valor == other.valor and self.dt_lancamento == other.dt_lancamento

    def __hash__(self):
        return hash((self.id, self.dt_lancamento, self.pagador, self.valor))
