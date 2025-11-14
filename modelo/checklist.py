# modelo/checklist.py
from datetime import date
from typing import List

from .moto import Moto
from .checklist_item import ChecklistItem, StatusItem


class Checklist:
    """
    Representa um checklist de revisão de uma moto em uma data específica.
    """

    def __init__(self, moto: Moto, km_atual: int, data_revisao: date | None = None):
        if km_atual < 0:
            raise ValueError("Quilometragem não pode ser negativa.")

        self._moto = moto
        self._km_atual = km_atual
        self._data_revisao = data_revisao or date.today()
        self._itens: List[ChecklistItem] = []

    @property
    def moto(self) -> Moto:
        return self._moto

    @property
    def km_atual(self) -> int:
        return self._km_atual

    @property
    def data_revisao(self) -> date:
        return self._data_revisao

    @property
    def data_formatada(self) -> str:
        """
        Retorna a data da revisão no formato dd/mm/aaaa.
        """
        return self._data_revisao.strftime("%d/%m/%Y")
    
    @property
    def itens(self) -> List[ChecklistItem]:
        # retornamos uma cópia superficial para evitar modificações diretas
        return list(self._itens)

    def adicionar_item(self, item: ChecklistItem) -> None:
        if not isinstance(item, ChecklistItem):
            raise ValueError("Item inválido.")
        self._itens.append(item)
    
    
    

    # ---- MÉTRICAS ÚTEIS ----

    def contar_por_status(self, status: StatusItem) -> int:
        return sum(1 for item in self._itens if item.status == status)

    def total_concluido(self) -> int:
        return self.contar_por_status(StatusItem.CONCLUIDO)

    def total_pendente(self) -> int:
        return self.contar_por_status(StatusItem.PENDENTE)

    def total_necessita_troca(self) -> int:
        return self.contar_por_status(StatusItem.NECESSITA_TROCA)

    def custo_total_estimado(self) -> float:
        """
        Soma somente o custo dos itens marcados como NECESSITA_TROCA.
        """
        return sum(item.custo_estimado for item in self._itens if item.status == StatusItem.NECESSITA_TROCA)

    def __repr__(self) -> str:
        return (
            f"[CHECKLIST]\n"
            f"Moto: {self.moto.modelo} ({self.moto.placa}) - {self.moto.ano}\n"
            f"Data: {self.data_formatada}\n"
            f"KM: {self.km_atual}\n"
            f"Itens: {len(self._itens)}\n"
        )


