# db/repository.py
"""
Repositório para acesso ao banco de dados.
Separa a lógica de acesso aos dados da lógica de negócio.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import date

from db.models import MotoDB, ChecklistDB, ChecklistItemDB, UsuarioDB
from modelo.moto import Moto
from modelo.categoria_moto import CategoriaMoto
from modelo.checklist import Checklist
from modelo.checklist_item import ChecklistItem, StatusItem
from controle.validadores import normalizar_placa


class MotoRepository:
    """Repositório para operações com Motos."""
    
    @staticmethod
    def criar(db: Session, moto: Moto) -> MotoDB:
        """Cria uma nova moto no banco."""
        moto_db = MotoDB(
            placa=normalizar_placa(moto.placa),
            marca=moto.marca,
            modelo=moto.modelo,
            ano=moto.ano,
            cilindradas=moto.cilindradas,
            categoria=moto.categoria.value
        )
        db.add(moto_db)
        db.commit()
        db.refresh(moto_db)
        return moto_db
    
    @staticmethod
    def buscar_por_placa(db: Session, placa: str) -> Optional[MotoDB]:
        """Busca moto por placa."""
        placa_norm = normalizar_placa(placa)
        return db.query(MotoDB).filter(MotoDB.placa == placa_norm).first()
    
    @staticmethod
    def listar_todas(db: Session, skip: int = 0, limit: Optional[int] = None) -> List[MotoDB]:
        """Lista todas as motos."""
        query = db.query(MotoDB)
        if limit:
            return query.offset(skip).limit(limit).all()
        return query.offset(skip).all()
    
    @staticmethod
    def buscar_por_modelo(db: Session, termo: str) -> List[MotoDB]:
        """Busca motos por modelo (busca parcial)."""
        termo_lower = termo.lower()
        return db.query(MotoDB).filter(MotoDB.modelo.ilike(f"%{termo_lower}%")).all()
    
    @staticmethod
    def atualizar(db: Session, moto_db: MotoDB, **kwargs) -> MotoDB:
        """Atualiza uma moto."""
        for key, value in kwargs.items():
            if hasattr(moto_db, key) and value is not None:
                if key == "categoria" and isinstance(value, CategoriaMoto):
                    setattr(moto_db, key, value.value)
                else:
                    setattr(moto_db, key, value)
        db.commit()
        db.refresh(moto_db)
        return moto_db
    
    @staticmethod
    def deletar(db: Session, moto_db: MotoDB) -> bool:
        """Deleta uma moto."""
        db.delete(moto_db)
        db.commit()
        return True


class ChecklistRepository:
    """Repositório para operações com Checklists."""
    
    @staticmethod
    def criar(db: Session, checklist: Checklist, moto_db: MotoDB) -> ChecklistDB:
        """Cria um novo checklist no banco."""
        checklist_db = ChecklistDB(
            moto_id=moto_db.id,
            km_atual=checklist.km_atual,
            data_revisao=checklist.data_revisao,
            finalizado=checklist.finalizado,
            pago=checklist.pago,
            custo_real=checklist.custo_real
        )
        db.add(checklist_db)
        db.flush()  # Para obter o ID
        
        # Adiciona itens
        for item in checklist.itens:
            item_db = ChecklistItemDB(
                checklist_id=checklist_db.id,
                nome=item.nome,
                categoria=item.categoria,
                status=item.status.value,
                custo_estimado=item.custo_estimado
            )
            db.add(item_db)
        
        db.commit()
        db.refresh(checklist_db)
        return checklist_db
    
    @staticmethod
    def buscar_por_id(db: Session, checklist_id: int) -> Optional[ChecklistDB]:
        """Busca checklist por ID."""
        from sqlalchemy.orm import joinedload
        return db.query(ChecklistDB).options(joinedload(ChecklistDB.itens)).filter(ChecklistDB.id == checklist_id).first()
    
    @staticmethod
    def listar_todos(
        db: Session,
        skip: int = 0,
        limit: Optional[int] = None,
        placa: Optional[str] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
        finalizado: Optional[bool] = None,
        pago: Optional[bool] = None
    ) -> List[ChecklistDB]:
        """Lista checklists com filtros."""
        from sqlalchemy.orm import joinedload
        query = db.query(ChecklistDB).options(joinedload(ChecklistDB.itens))
        
        if placa:
            placa_norm = normalizar_placa(placa)
            query = query.join(MotoDB).filter(MotoDB.placa == placa_norm)
        
        if data_inicio:
            query = query.filter(ChecklistDB.data_revisao >= data_inicio)
        
        if data_fim:
            query = query.filter(ChecklistDB.data_revisao <= data_fim)
        
        if finalizado is not None:
            query = query.filter(ChecklistDB.finalizado == finalizado)
        
        if pago is not None:
            query = query.filter(ChecklistDB.pago == pago)
        
        query = query.order_by(ChecklistDB.data_revisao.desc())
        
        if limit:
            return query.offset(skip).limit(limit).all()
        return query.offset(skip).all()
    
    @staticmethod
    def buscar_por_moto(db: Session, placa: str) -> List[ChecklistDB]:
        """Busca checklists de uma moto."""
        from sqlalchemy.orm import joinedload
        placa_norm = normalizar_placa(placa)
        return (
            db.query(ChecklistDB)
            .options(joinedload(ChecklistDB.itens))
            .join(MotoDB)
            .filter(MotoDB.placa == placa_norm)
            .order_by(ChecklistDB.data_revisao.desc())
            .all()
        )
    
    @staticmethod
    def atualizar(db: Session, checklist_db: ChecklistDB, **kwargs) -> ChecklistDB:
        """Atualiza um checklist."""
        for key, value in kwargs.items():
            if hasattr(checklist_db, key) and value is not None:
                setattr(checklist_db, key, value)
        db.commit()
        db.refresh(checklist_db)
        return checklist_db
    
    @staticmethod
    def atualizar_item(
        db: Session,
        checklist_id: int,
        item_index: int,
        status: Optional[StatusItem] = None,
        custo_estimado: Optional[float] = None
    ) -> bool:
        """Atualiza um item específico de um checklist."""
        checklist_db = ChecklistRepository.buscar_por_id(db, checklist_id)
        if not checklist_db:
            return False
        
        itens = sorted(checklist_db.itens, key=lambda x: x.id)
        if item_index < 0 or item_index >= len(itens):
            return False
        
        item_db = itens[item_index]
        
        if status is not None:
            item_db.status = status.value
        
        if custo_estimado is not None:
            item_db.custo_estimado = custo_estimado
        
        db.commit()
        return True
    
    @staticmethod
    def deletar(db: Session, checklist_db: ChecklistDB) -> bool:
        """Deleta um checklist."""
        db.delete(checklist_db)
        db.commit()
        return True
    
    @staticmethod
    def buscar_por_status_item(db: Session, status: StatusItem) -> List[ChecklistDB]:
        """
        Busca checklists que possuem pelo menos um item com o status especificado.
        Query otimizada usando JOIN ao invés de filtrar em memória.
        """
        from sqlalchemy.orm import joinedload
        return (
            db.query(ChecklistDB)
            .options(joinedload(ChecklistDB.itens))
            .join(ChecklistItemDB)
            .filter(ChecklistItemDB.status == status.value)
            .distinct()
            .order_by(ChecklistDB.data_revisao.desc())
            .all()
        )


class UsuarioRepository:
    """Repositório para operações com Usuários."""
    
    @staticmethod
    def criar(db: Session, username: str, email: str, hashed_password: str, is_admin: bool = False) -> UsuarioDB:
        """Cria um novo usuário."""
        usuario_db = UsuarioDB(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_admin="true" if is_admin else "false"
        )
        db.add(usuario_db)
        db.commit()
        db.refresh(usuario_db)
        return usuario_db
    
    @staticmethod
    def buscar_por_username(db: Session, username: str) -> Optional[UsuarioDB]:
        """Busca usuário por username."""
        return db.query(UsuarioDB).filter(UsuarioDB.username == username).first()
    
    @staticmethod
    def buscar_por_email(db: Session, email: str) -> Optional[UsuarioDB]:
        """Busca usuário por email."""
        return db.query(UsuarioDB).filter(UsuarioDB.email == email).first()
    
    @staticmethod
    def buscar_por_id(db: Session, user_id: int) -> Optional[UsuarioDB]:
        """Busca usuário por ID."""
        return db.query(UsuarioDB).filter(UsuarioDB.id == user_id).first()

