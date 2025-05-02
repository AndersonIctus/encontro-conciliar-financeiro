# ID;Data Lançamento;Descrição;Tipo;Forma Pgto;Valor;Observacao
class OutroValor:
    def __init__(self, id: int, data: str, nome: str,  tipo: str, formaPgto: str, valor: float, observacao: str):
        self.id = id
        self.data = data
        self.nome = nome
        self.tipo = tipo
        self.formaPgto = formaPgto
        self.valor = valor
        self.observacao = observacao

    def __repr__(self):
        return (
            f"Despesa(id='{self.id}', dt_lancamento ='{self.data}', nome='{self.nome}', "
            f"tipo='{self.tipo}', forma pgto={self.formaPgto}, valor={self.valor}, observacao={self.observacao})"
        )

    def __eq__(self, other):
        if not isinstance(other, OutroValor):
            return False
        return self.id == other.id and self.nome == other.nome and self.valor == other.valor and self.data == other.data

    def __hash__(self):
        return hash((self.id, self.data, self.nome, self.valor))
