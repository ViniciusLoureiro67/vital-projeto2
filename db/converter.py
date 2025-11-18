# db/converter.py
"""
Conversores entre modelos de domínio e modelos de banco de dados.
"""
from modelo.moto import Moto
from modelo.categoria_moto import CategoriaMoto
from modelo.checklist import Checklist
from modelo.checklist_item import ChecklistItem, StatusItem
from db.models import MotoDB, ChecklistDB, ChecklistItemDB


def moto_db_para_dominio(moto_db: MotoDB) -> Moto:
    """Converte MotoDB para Moto (modelo de domínio)."""
    categoria_enum = CategoriaMoto.OUTROS
    for cat in CategoriaMoto:
        if cat.value == moto_db.categoria:
            categoria_enum = cat
            break
    
    return Moto(
        placa=moto_db.placa,
        marca=moto_db.marca,
        modelo=moto_db.modelo,
        ano=moto_db.ano,
        cilindradas=moto_db.cilindradas,
        categoria=categoria_enum
    )


def checklist_db_para_dominio(checklist_db: ChecklistDB) -> Checklist:
    """Converte ChecklistDB para Checklist (modelo de domínio)."""
    moto = moto_db_para_dominio(checklist_db.moto)
    
    checklist = Checklist(
        moto=moto,
        km_atual=checklist_db.km_atual,
        data_revisao=checklist_db.data_revisao,
        id=checklist_db.id,
        finalizado=getattr(checklist_db, 'finalizado', False),
        pago=getattr(checklist_db, 'pago', False),
        custo_real=getattr(checklist_db, 'custo_real', None)
    )
    
    # Adiciona itens
    for item_db in checklist_db.itens:
        status_enum = StatusItem.PENDENTE
        for s in StatusItem:
            if s.value == item_db.status:
                status_enum = s
                break
        
        item = ChecklistItem(
            nome=item_db.nome,
            categoria=item_db.categoria,
            status=status_enum,
            custo_estimado=item_db.custo_estimado,
            id=item_db.id
        )
        checklist._itens.append(item)
    
    return checklist

