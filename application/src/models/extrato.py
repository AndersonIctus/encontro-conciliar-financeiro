class Extrato:
    def __init__(self, nome: str, valor: float):
        self.nome = nome
        self.valor = valor

    def __repr__(self):
        return f"Extrato(nome='{self.nome}', valor={self.valor})"

    def __eq__(self, other):
        if not isinstance(other, Extrato):
            return False
        return self.nome == other.nome and self.valor == other.valor

    def __hash__(self):
        return hash((self.nome, self.valor))
