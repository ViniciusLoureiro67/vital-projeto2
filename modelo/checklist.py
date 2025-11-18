# modelo/checklist.py
from datetime import date
from typing import List

from .moto import Moto
from .checklist_item import ChecklistItem, StatusItem


class Checklist:
    """
    Representa um checklist de revisão de uma moto em uma data específica.
    """

    def __init__(self, moto: Moto, km_atual: int, data_revisao: date | None = None, id: int | None = None, finalizado: bool = False, pago: bool = False, custo_real: float | None = None):
        if km_atual < 0:
            raise ValueError("Quilometragem não pode ser negativa.")

        self._id = id
        self._moto = moto
        self._km_atual = km_atual
        self._data_revisao = data_revisao or date.today()
        self._itens: List[ChecklistItem] = []
        self._finalizado = finalizado
        self._pago = pago
        self._custo_real = custo_real
    
    @property
    def id(self) -> int | None:
        return self._id

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
    
    @property
    def finalizado(self) -> bool:
        return self._finalizado
    
    @finalizado.setter
    def finalizado(self, valor: bool) -> None:
        self._finalizado = valor
    
    @property
    def pago(self) -> bool:
        return self._pago
    
    @pago.setter
    def pago(self, valor: bool) -> None:
        self._pago = valor
    
    @property
    def custo_real(self) -> float | None:
        return self._custo_real
    
    @custo_real.setter
    def custo_real(self, valor: float | None) -> None:
        if valor is not None and valor < 0:
            raise ValueError("Custo real não pode ser negativo.")
        self._custo_real = valor

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

    def total_ignorado(self) -> int:
        return self.contar_por_status(StatusItem.IGNORADO)

    def custo_total_estimado(self) -> float:
        """
        Soma somente o custo dos itens marcados como NECESSITA_TROCA.
        """
        return sum(item.custo_estimado for item in self._itens if item.status == StatusItem.NECESSITA_TROCA)

    def to_dict(self) -> dict:
        """Converte o checklist para dicionário (serialização JSON)."""
        return {
            "id": self._id,
            "moto": self.moto.to_dict() if hasattr(self.moto, 'to_dict') else {
                "placa": self.moto.placa,
                "marca": self.moto.marca,
                "modelo": self.moto.modelo,
                "ano": self.moto.ano
            },
            "km_atual": self.km_atual,
            "data_revisao": self.data_revisao.isoformat(),
            "data_formatada": self.data_formatada,
            "finalizado": self._finalizado,
            "pago": self._pago,
            "custo_real": self._custo_real,
            "itens": [item.to_dict() if hasattr(item, 'to_dict') else {
                "nome": item.nome,
                "categoria": item.categoria,
                "status": item.status.value,
                "custo_estimado": item.custo_estimado
            } for item in self._itens],
            "total_concluido": self.total_concluido(),
            "total_pendente": self.total_pendente(),
            "total_necessita_troca": self.total_necessita_troca(),
            "total_ignorado": self.total_ignorado(),
            "custo_total_estimado": self.custo_total_estimado()
        }
    
    def __repr__(self) -> str:
        return (
            f"[CHECKLIST]\n"
            f"Moto: {self.moto.modelo} ({self.moto.placa}) - {self.moto.ano}\n"
            f"Data: {self.data_formatada}\n"
            f"KM: {self.km_atual}\n"
            f"Itens: {len(self._itens)}\n"
        )


