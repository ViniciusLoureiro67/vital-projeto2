# modelo/checklist_templates.py
from datetime import date
from typing import List, Tuple

from .checklist import Checklist
from .checklist_item import ChecklistItem, StatusItem
from .moto import Moto

# (categoria, nome do item)
CHECKLIST_REVISAO_PADRAO: List[Tuple[str, str]] = [
    # Motor e Lubrificação
    ("Motor", "Óleo do motor"),
    ("Motor", "Filtro de óleo"),
    ("Motor", "Filtro de ar"),
    ("Motor", "Velas de ignição"),
    ("Motor", "Verificar vazamentos de óleo/fluídos"),

    # Transmissão
    ("Transmissão", "Corrente (tensão e lubrificação)"),
    ("Transmissão", "Coroa e pinhão"),
    ("Transmissão", "Folga/desgaste da transmissão"),

    # Freios
    ("Freios", "Pastilhas de freio dianteiras"),
    ("Freios", "Pastilhas de freio traseiras"),
    ("Freios", "Fluido de freio"),
    ("Freios", "Discos de freio"),

    # Pneus e Rodas
    ("Pneus", "Pneu dianteiro"),
    ("Pneus", "Pneu traseiro"),
    ("Pneus", "Rodas/raios"),

    # Suspensão
    ("Suspensão", "Bengalas dianteiras (vazamento)"),
    ("Suspensão", "Amortecedor traseiro"),

    # Elétrica
    ("Elétrica", "Bateria"),
    ("Elétrica", "Farol alto/baixo"),
    ("Elétrica", "Setas"),
    ("Elétrica", "Luz de freio"),
    ("Elétrica", "Iluminação do painel"),

    # Segurança / Test ride
    ("Segurança", "Retrovisores"),
    ("Segurança", "Manetes e cabos"),
    ("Segurança", "Retorno do acelerador"),
    ("Segurança", "Ruídos anormais no teste"),
]


def obter_itens_por_km(km_atual: int) -> List[Tuple[str, str]]:
    """
    Retorna itens adicionais do checklist baseados na quilometragem.
    
    Args:
        km_atual: Quilometragem atual da moto
    
    Returns:
        Lista de tuplas (categoria, nome_item) adicionais
    """
    itens_adicional = []
    
    # A cada 5.000 km - revisão básica
    if km_atual >= 5000:
        pass  # Itens básicos já estão no padrão
    
    # A cada 10.000 km - revisão intermediária
    if km_atual >= 10000:
        itens_adicional.append(("Motor", "Verificar tensão da correia (se aplicável)"))
        itens_adicional.append(("Transmissão", "Verificar desgaste da corrente"))
    
    # A cada 15.000 km
    if km_atual >= 15000:
        itens_adicional.append(("Motor", "Verificar sistema de arrefecimento"))
        itens_adicional.append(("Elétrica", "Verificar sistema de carga"))
    
    # A cada 20.000 km - revisão maior
    if km_atual >= 20000:
        itens_adicional.append(("Motor", "Verificar válvulas"))
        itens_adicional.append(("Motor", "Verificar compressão do motor"))
        itens_adicional.append(("Suspensão", "Verificar rolamentos das rodas"))
    
    # A cada 25.000 km
    if km_atual >= 25000:
        itens_adicional.append(("Transmissão", "Verificar desgaste da coroa e pinhão"))
        itens_adicional.append(("Elétrica", "Verificar cabos e conexões"))
    
    # A cada 30.000 km - revisão completa
    if km_atual >= 30000:
        itens_adicional.append(("Transmissão", "Troca de correia/corrente (se aplicável)"))
        itens_adicional.append(("Motor", "Limpeza de bico injetor/carburador"))
        itens_adicional.append(("Suspensão", "Verificar amortecedores (vazamento)"))
    
    # A cada 40.000 km
    if km_atual >= 40000:
        itens_adicional.append(("Motor", "Verificar sistema de escape"))
        itens_adicional.append(("Elétrica", "Verificar alternador/regulador"))
    
    # A cada 50.000 km - revisão muito completa
    if km_atual >= 50000:
        itens_adicional.append(("Motor", "Verificar cabeçote e junta"))
        itens_adicional.append(("Transmissão", "Verificar caixa de câmbio"))
        itens_adicional.append(("Suspensão", "Revisão completa da suspensão"))
    
    # Remove duplicatas mantendo ordem
    itens_unicos = []
    itens_vistos = set()
    for item in itens_adicional:
        if item not in itens_vistos:
            itens_unicos.append(item)
            itens_vistos.add(item)
    
    return itens_unicos


def criar_checklist_padrao(
    moto: Moto,
    km_atual: int,
    data_revisao: date | None = None,
) -> Checklist:
    """
    Cria um Checklist padrão de revisão para a moto informada,
    com todos os itens começando como PENDENTE e custo 0.0.
    """
    if data_revisao is None:
        data_revisao = date.today()

    checklist = Checklist(
        moto=moto,
        km_atual=km_atual,
        data_revisao=data_revisao,
    )

    # Adiciona itens padrão
    for categoria, nome in CHECKLIST_REVISAO_PADRAO:
        item = ChecklistItem(
            nome=nome,
            categoria=categoria,
            status=StatusItem.PENDENTE,
            custo_estimado=0.0,
        )
        checklist.adicionar_item(item)

    return checklist


def criar_checklist_adaptativo(
    moto: Moto,
    km_atual: int,
    data_revisao: date | None = None,
) -> Checklist:
    """
    Cria um Checklist adaptativo de revisão baseado na quilometragem.
    
    Adiciona itens específicos conforme a KM da moto, seguindo
    recomendações de manutenção preventiva.
    
    Args:
        moto: Moto da revisão
        km_atual: Quilometragem atual
        data_revisao: Data da revisão (padrão: hoje)
    
    Returns:
        Checklist com itens padrão + itens específicos por KM
    """
    # Cria checklist padrão
    checklist = criar_checklist_padrao(moto, km_atual, data_revisao)
    
    # Adiciona itens específicos por KM
    itens_por_km = obter_itens_por_km(km_atual)
    for categoria, nome in itens_por_km:
        item = ChecklistItem(
            nome=nome,
            categoria=categoria,
            status=StatusItem.PENDENTE,
            custo_estimado=0.0,
        )
        checklist.adicionar_item(item)
    
    return checklist
