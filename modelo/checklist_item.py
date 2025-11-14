# modelo/checklist_item.py
from enum import Enum


class StatusItem(Enum):
    CONCLUIDO = "concluido"
    PENDENTE = "pendente"
    NECESSITA_TROCA = "necessita_troca"


class ChecklistItem:
    """
    Representa um item do checklist de revisão da moto.
    Exemplo: 'Verificar nível do óleo do motor'
    """

    def __init__(self, nome: str, categoria: str, status: StatusItem = StatusItem.PENDENTE, custo_estimado: float = 0.0):
        if not nome or not nome.strip():
            raise ValueError("Nome do item é obrigatório.")

        self._nome = nome.strip()
        self._categoria = categoria.strip() if categoria else "Geral"
        self._status = status
        self._custo_estimado = max(custo_estimado, 0.0)

    @property
    def nome(self) -> str:
        return self._nome

    @property
    def categoria(self) -> str:
        return self._categoria

    @property
    def status(self) -> StatusItem:
        return self._status

    @status.setter
    def status(self, novo_status: StatusItem) -> None:
        if not isinstance(novo_status, StatusItem):
            raise ValueError("Status inválido.")
        self._status = novo_status

    @property
    def custo_estimado(self) -> float:
        return self._custo_estimado

    @custo_estimado.setter
    def custo_estimado(self, valor: float) -> None:
        if valor < 0:
            raise ValueError("Custo não pode ser negativo.")
        self._custo_estimado = valor

    def __repr__(self) -> str:
        return f"ChecklistItem(nome={self.nome}, categoria={self.categoria}, status={self.status.name}, custo={self.custo_estimado})"
