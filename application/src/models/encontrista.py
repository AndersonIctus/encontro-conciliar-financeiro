# ID;Data Lançamento;Pagador;Tipo;Valor
class Encontrista:
    def __init__(self, id: int, dt_lancamento: str, pagador: str,  tipo: str, valor: float):
        self.id = id
        self.dt_lancamento = dt_lancamento
        self.pagador = pagador
        self.tipo = tipo
        self.valor = valor
        self.valor_conciliado = valor

    def __repr__(self):
        return (
            f"Encontrista(id='{self.id}', dt_lancamento ='{self.dt_lancamento}', nome='{self.pagador}', "
            f"tipo='{self.tipo}', valor={self.valor})"
        )

    def __eq__(self, other):
        if not isinstance(other, Encontrista):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash((self.id, self.pagador, self.valor))
