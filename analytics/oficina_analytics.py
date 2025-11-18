# analytics/oficina_analytics.py
from typing import List, Dict, Optional
from datetime import date, timedelta

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
    
    def custos_reais_array(self) -> np.ndarray:
        """
        Retorna um array NumPy com os custos reais das revisões.
        Filtra apenas checklists que têm custo_real informado.
        """
        checklists = self._obter_checklists()
        custos = [c.custo_real for c in checklists if c.custo_real is not None]
        return np.array(custos, dtype=float) if custos else np.array([], dtype=float)
    
    def resumo_custos_reais(self) -> Dict[str, float]:
        """
        Retorna estatísticas dos custos reais (quando informados).
        """
        custos = self.custos_reais_array()
        if custos.size == 0:
            return {
                "soma": 0.0,
                "media": 0.0,
                "max": 0.0,
                "min": 0.0,
                "total_com_custo_real": 0
            }
        
        return {
            "soma": float(np.sum(custos)),
            "media": float(np.mean(custos)),
            "max": float(np.max(custos)),
            "min": float(np.min(custos)),
            "total_com_custo_real": int(custos.size)
        }
    
    def dados_historicos_graficos(self) -> Dict:
        """
        Retorna dados formatados para visualização em gráficos.
        Inclui custos estimados, custos reais, KM e datas.
        """
        checklists = self._obter_checklists()
        dados = []
        
        for c in checklists:
            dados.append({
                "data": c.data_revisao.isoformat(),
                "data_formatada": c.data_formatada,
                "km": c.km_atual,
                "custo_estimado": c.custo_total_estimado(),
                "custo_real": c.custo_real if c.custo_real is not None else None,
                "moto": f"{c.moto.modelo} - {c.moto.placa}",
                "finalizado": c.finalizado,
                "pago": c.pago
            })
        
        # Ordena por data
        dados.sort(key=lambda x: x["data"])
        
        return {
            "dados": dados,
            "total": len(dados)
        }
    
    # ---------------------- MÉTRICAS FINANCEIRAS ----------------------
    
    def relatorio_financeiro(
        self,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None
    ) -> Dict:
        """
        Gera relatório financeiro para um período específico.
        
        Retorna:
        - receitas: Total do valor da revisão (custo_total_estimado) de checklists pagos (dinheiro que entrou)
        - custos: Total do custo real das peças/produtos (custo_real) de todos os checklists (dinheiro que saiu)
        - lucro: Receitas - Custos
        - quantidade_motos: Número de motos únicas atendidas no período
        - quantidade_servicos: Número total de checklists/serviços realizados
        - checklists_pagos: Número de checklists pagos
        - checklists_nao_pagos: Número de checklists não pagos
        - ticket_medio: Receitas / quantidade_servicos (se houver serviços)
        """
        # Obtém checklists do período
        if hasattr(self._controller, 'buscar_checklists_por_periodo'):
            checklists = self._controller.buscar_checklists_por_periodo(
                data_inicio=data_inicio,
                data_fim=data_fim
            )
        else:
            # Fallback para controller em memória
            checklists = self._obter_checklists()
            if data_inicio:
                checklists = [c for c in checklists if c.data_revisao >= data_inicio]
            if data_fim:
                checklists = [c for c in checklists if c.data_revisao <= data_fim]
        
        # Calcula métricas
        receitas = 0.0  # Valor da Revisão (custo_total_estimado) de checklists PAGOS
        custos = 0.0    # Custo Real das Peças/Produtos (custo_real) de TODOS os checklists
        motos_unicas = set()
        checklists_pagos = 0
        checklists_nao_pagos = 0
        
        for checklist in checklists:
            # Conta motos únicas
            motos_unicas.add(checklist.moto.placa)
            
            # Soma custos reais das peças/produtos (se informado)
            if checklist.custo_real is not None:
                custos += checklist.custo_real
            
            # Se está pago, conta o valor da revisão como receita
            if checklist.pago:
                receitas += checklist.custo_total_estimado()
                checklists_pagos += 1
            else:
                checklists_nao_pagos += 1
        
        quantidade_servicos = len(checklists)
        quantidade_motos = len(motos_unicas)
        lucro = receitas - custos
        ticket_medio = receitas / quantidade_servicos if quantidade_servicos > 0 else 0.0
        
        return {
            "receitas": float(receitas),
            "custos": float(custos),
            "lucro": float(lucro),
            "quantidade_motos": quantidade_motos,
            "quantidade_servicos": quantidade_servicos,
            "checklists_pagos": checklists_pagos,
            "checklists_nao_pagos": checklists_nao_pagos,
            "ticket_medio": float(ticket_medio),
            "periodo": {
                "data_inicio": data_inicio.isoformat() if data_inicio else None,
                "data_fim": data_fim.isoformat() if data_fim else None,
            }
        }
    
    def relatorio_financeiro_por_periodo(
        self,
        tipo_periodo: str,  # 'dia', 'semana', 'mes', 'ano'
        data_referencia: Optional[date] = None
    ) -> Dict:
        """
        Gera relatório financeiro para um período específico (dia, semana, mês ou ano).
        
        Args:
            tipo_periodo: 'dia', 'semana', 'mes' ou 'ano'
            data_referencia: Data de referência (padrão: hoje)
        
        Returns:
            Dicionário com relatório financeiro do período
        """
        if data_referencia is None:
            data_referencia = date.today()
        
        data_inicio = None
        data_fim = None
        
        if tipo_periodo == 'dia':
            data_inicio = data_referencia
            data_fim = data_referencia
        elif tipo_periodo == 'semana':
            # Segunda-feira da semana
            dias_para_segunda = (data_referencia.weekday()) % 7
            data_inicio = data_referencia - timedelta(days=dias_para_segunda)
            data_fim = data_inicio + timedelta(days=6)
        elif tipo_periodo == 'mes':
            data_inicio = date(data_referencia.year, data_referencia.month, 1)
            # Último dia do mês
            if data_referencia.month == 12:
                data_fim = date(data_referencia.year + 1, 1, 1) - timedelta(days=1)
            else:
                data_fim = date(data_referencia.year, data_referencia.month + 1, 1) - timedelta(days=1)
        elif tipo_periodo == 'ano':
            data_inicio = date(data_referencia.year, 1, 1)
            data_fim = date(data_referencia.year, 12, 31)
        else:
            raise ValueError(f"Tipo de período inválido: {tipo_periodo}")
        
        return self.relatorio_financeiro(data_inicio=data_inicio, data_fim=data_fim)