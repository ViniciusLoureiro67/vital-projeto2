# analytics/oficina_analytics.py
from typing import List, Dict

import numpy as np

from controle.oficina_controller import OficinaController
from modelo.checklist import Checklist
from modelo.checklist_item import StatusItem


class OficinaAnalytics:
    """
    Classe responsável por gerar análises numéricas usando NumPy
    a partir dos dados da oficina (checklists, custos, status, km, etc.).
    """

    def __init__(self, controller: OficinaController):
        self._controller = controller

    def _obter_checklists(self) -> List[Checklist]:
        """
        Retorna todos os checklists registrados no controller.
        """
        return self._controller.listar_checklists()

    # ---------------------- MÉTRICAS BÁSICAS ----------------------

    def custos_totais_array(self) -> np.ndarray:
        """
        Retorna um array NumPy com o custo total estimado das trocas
        de cada checklist (valor em R$).
        """
        checklists = self._obter_checklists()
        custos = [c.custo_total_estimado() for c in checklists]
        return np.array(custos, dtype=float)

    def km_array(self) -> np.ndarray:
        """
        Retorna um array NumPy com as quilometragens dos checklists.
        """
        checklists = self._obter_checklists()
        kms = [c.km_atual for c in checklists]
        return np.array(kms, dtype=int)

    def resumo_custos(self) -> Dict[str, float]:
        """
        Retorna um dicionário com estatísticas básicas dos custos:
        - soma, média, máximo, mínimo
        """
        custos = self.custos_totais_array()
        if custos.size == 0:
            return {
                "soma": 0.0,
                "media": 0.0,
                "max": 0.0,
                "min": 0.0,
            }

        return {
            "soma": float(np.sum(custos)),
            "media": float(np.mean(custos)),
            "max": float(np.max(custos)),
            "min": float(np.min(custos)),
        }

    def distribuicao_status_itens(self) -> Dict[str, int]:
        """
        Conta quantos itens no total (em todos os checklists) estão:
        - concluídos
        - pendentes
        - necessitando troca
        """
        checklists = self._obter_checklists()
        total_concluido = 0
        total_pendente = 0
        total_troca = 0

        for c in checklists:
            total_concluido += c.total_concluido()
            total_pendente += c.total_pendente()
            total_troca += c.total_necessita_troca()

        return {
            "concluido": total_concluido,
            "pendente": total_pendente,
            "necessita_troca": total_troca,
        }

    # ---------------------- EXEMPLO "MLzinho" ----------------------

    def estimar_custo_por_km(self) -> Dict[str, float] | None:
        """
        Usa uma regressão linear simples (NumPy polyfit) para estimar
        custo de revisão em função da quilometragem.

        Retorna:
        - coef_angular (a)
        - coef_linear (b)
        Ou None se não houver dados suficientes.
        """
        kms = self.km_array()
        custos = self.custos_totais_array()

        # Precisamos de pelo menos 2 pontos para ajustar uma reta
        if kms.size < 2 or custos.size < 2:
            return None

        # polyfit de grau 1 -> y = a*x + b
        a, b = np.polyfit(kms, custos, 1)
        return {"coef_angular": float(a), "coef_linear": float(b)}

    def prever_custo_para_km(self, km_futuro: int) -> float | None:
        """
        Usa o modelo linear para prever um custo aproximado
        para uma futura revisão na quilometragem informada.
        """
        modelo = self.estimar_custo_por_km()
        if modelo is None:
            return None

        a = modelo["coef_angular"]
        b = modelo["coef_linear"]
        custo_previsto = a * km_futuro + b
        return float(custo_previsto)
