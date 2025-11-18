# controle/validadores_checklist.py
"""
Validações específicas para checklists e revisões.
"""
from typing import Optional, Tuple
from datetime import date, timedelta

from modelo.moto import Moto
from modelo.checklist import Checklist
from controle.excecoes import ValidacaoError


def validar_km_revisao(
    moto: Moto,
    km_novo: int,
    ultimo_checklist: Optional[Checklist] = None
) -> Tuple[bool, Optional[str]]:
    """
    Valida se a quilometragem da revisão está correta.
    
    Verifica:
    - Se KM não é negativo
    - Se KM está aumentando (não pode ser menor que última revisão)
    - Se diferença de KM não é muito grande (possível erro de digitação)
    
    Args:
        moto: Moto da revisão
        km_novo: Nova quilometragem a validar
        ultimo_checklist: Último checklist da moto (opcional, será buscado se None)
    
    Returns:
        Tuple[bool, Optional[str]]: (é_válida, mensagem_erro)
    """
    if km_novo < 0:
        return False, "Quilometragem não pode ser negativa."
    
    # Se não foi fornecido o último checklist, retorna OK
    # (a validação completa será feita quando o checklist for criado)
    if ultimo_checklist is None:
        return True, None
    
    km_anterior = ultimo_checklist.km_atual
    
    # Verifica se KM diminuiu
    if km_novo < km_anterior:
        return False, (
            f"⚠️ ATENÇÃO: Quilometragem menor que a última revisão!\n\n"
            f"Última revisão: {km_anterior:,} km\n"
            f"Nova revisão: {km_novo:,} km\n"
            f"Diferença: {km_anterior - km_novo:,} km\n\n"
            f"Verifique se digitou corretamente. Se a moto teve o hodômetro trocado, "
            f"isso é aceitável, mas confirme os dados."
        )
    
    # Verifica se diferença é muito grande (possível erro de digitação)
    diferenca = km_novo - km_anterior
    if diferenca > 50000:
        return False, (
            f"⚠️ ATENÇÃO: Diferença de quilometragem muito grande!\n\n"
            f"Última revisão: {km_anterior:,} km\n"
            f"Nova revisão: {km_novo:,} km\n"
            f"Diferença: {diferenca:,} km\n\n"
            f"Verifique se digitou corretamente. Se a diferença está correta, "
            f"confirme para continuar."
        )
    
    # Alerta se diferença é grande mas aceitável
    if diferenca > 20000:
        return True, (
            f"ℹ️ Diferença de {diferenca:,} km desde a última revisão. "
            f"Confirme se está correto."
        )
    
    return True, None


def validar_custo_total(
    custo_total: float,
    alerta_limite: float = 5000.0
) -> Tuple[bool, Optional[str]]:
    """
    Valida se o custo total está dentro de limites razoáveis.
    
    Args:
        custo_total: Custo total a validar
        alerta_limite: Limite para alerta (padrão: R$ 5.000)
    
    Returns:
        Tuple[bool, Optional[str]]: (é_válida, mensagem_alerta)
    """
    if custo_total < 0:
        return False, "Custo não pode ser negativo."
    
    if custo_total > alerta_limite:
        return True, (
            f"⚠️ ATENÇÃO: Custo total muito alto!\n\n"
            f"Custo: R$ {custo_total:,.2f}\n"
            f"Limite de alerta: R$ {alerta_limite:,.2f}\n\n"
            f"Confirme se todos os valores estão corretos."
        )
    
    return True, None


def validar_custo_item(
    custo_item: float,
    nome_item: str,
    limite_razoavel: float = 2000.0
) -> Tuple[bool, Optional[str]]:
    """
    Valida se o custo de um item individual está razoável.
    
    Args:
        custo_item: Custo do item
        nome_item: Nome do item para mensagem
        limite_razoavel: Limite considerado razoável (padrão: R$ 2.000)
    
    Returns:
        Tuple[bool, Optional[str]]: (é_válida, mensagem_alerta)
    """
    if custo_item < 0:
        return False, "Custo não pode ser negativo."
    
    if custo_item > limite_razoavel:
        return True, (
            f"⚠️ ATENÇÃO: Custo muito alto para '{nome_item}'\n\n"
            f"Custo: R$ {custo_item:,.2f}\n"
            f"Limite considerado razoável: R$ {limite_razoavel:,.2f}\n\n"
            f"Verifique se o valor está correto."
        )
    
    return True, None


def validar_data_revisao(
    data_revisao: date,
    permitir_futuro: bool = True,
    dias_futuro_max: int = 1
) -> Tuple[bool, Optional[str]]:
    """
    Valida se a data da revisão está dentro de limites aceitáveis.
    
    Args:
        data_revisao: Data da revisão
        permitir_futuro: Se permite data futura (padrão: True)
        dias_futuro_max: Máximo de dias no futuro permitidos (padrão: 1)
    
    Returns:
        Tuple[bool, Optional[str]]: (é_válida, mensagem_erro)
    """
    hoje = date.today()
    
    # Verifica se data é muito antiga (> 2 anos)
    dois_anos_atras = hoje - timedelta(days=730)
    if data_revisao < dois_anos_atras:
        return False, (
            f"⚠️ Data muito antiga!\n\n"
            f"Data informada: {data_revisao.strftime('%d/%m/%Y')}\n"
            f"Hoje: {hoje.strftime('%d/%m/%Y')}\n\n"
            f"Verifique se a data está correta."
        )
    
    # Verifica se data é muito futura
    if not permitir_futuro:
        if data_revisao > hoje:
            return False, "Data não pode ser futura."
    else:
        dias_futuro = (data_revisao - hoje).days
        if dias_futuro > dias_futuro_max:
            return False, (
                f"⚠️ Data muito futura!\n\n"
                f"Data informada: {data_revisao.strftime('%d/%m/%Y')}\n"
                f"Hoje: {hoje.strftime('%d/%m/%Y')}\n"
                f"Diferença: {dias_futuro} dias\n\n"
                f"Revisões não podem ser agendadas com mais de {dias_futuro_max} dia(s) de antecedência."
            )
    
    return True, None


def obter_ultimo_checklist(
    controller,
    placa_moto: str
) -> Optional[Checklist]:
    """
    Obtém o último checklist de uma moto.
    
    Args:
        controller: Controller da oficina (OficinaController ou OficinaControllerDB)
        placa_moto: Placa da moto
    
    Returns:
        Último checklist ou None se não houver
    """
    try:
        checklists = controller.get_checklists_por_moto(placa_moto)
        if not checklists:
            return None
        
        # Retorna o checklist mais recente (primeiro da lista ordenada)
        return checklists[0] if checklists else None
    except Exception:
        return None

