import hashlib
import json
from typing import Any

# Padrão de dado que deve estar na conciliação para serem gerados os relatórios!
class DadoConciliado:
    def __init__(self, data: str, nome: str, tipo: str, forma_pgto: str, categoria: str, valor: float, observacao: Any):
        self.id = self._gerar_uid_unico(data, nome, tipo, forma_pgto, categoria, valor)
        self.data = data
        self.nome = nome
        self.tipo = tipo
        self.forma_pgto = forma_pgto
        self.categoria = categoria
        self.valor = valor
        self.observacao = self._normalizar_observacao(observacao)

    def __repr__(self):
        return (
            f"DadoConciliado(id='{self.id}', dt_lancamento ='{self.data}', nome='{self.nome}', "
            f"tipo='{self.tipo}', forma pgto={self.forma_pgto}, categoria={self.categoria}, "
            f"valor={self.valor}, observacao={self.observacao})"
        )

    def __eq__(self, other):
        if not isinstance(other, DadoConciliado):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash((self.data, self.nome, self.valor))
    
    @staticmethod
    def _gerar_uid_unico(data: str, nome: str, tipo: str, forma_pgto: str, categoria: str, valor: float) -> str:
        base = f"{data}|{nome}|{tipo}|{forma_pgto}|{categoria}|{valor:.2f}"
        uid = hashlib.md5(base.encode()).hexdigest()  # 32 caracteres
        return uid
    
    @staticmethod
    def _normalizar_observacao(obs: Any) -> str:
        if isinstance(obs, str):
            return obs.strip()
        try:
            return json.dumps(obs, ensure_ascii=False)
        except Exception:
            return str(obs)