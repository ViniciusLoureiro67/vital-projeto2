# controle/oficina_controller_db.py
"""
Controller que usa banco de dados PostgreSQL.
Mantém a mesma interface do OficinaController para compatibilidade.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from .excecoes import MotoNaoEncontradaError
from .validadores import validar_placa_brasileira
from modelo.moto import Moto
from modelo.checklist import Checklist
from modelo.checklist_item import StatusItem
from db.repository import MotoRepository, ChecklistRepository
from db.converter import moto_db_para_dominio, checklist_db_para_dominio


class OficinaControllerDB:
    """
    Controlador principal da oficina usando banco de dados PostgreSQL.
    - Gerencia motos cadastradas
    - Gerencia checklists de revisão
    """
    
    def __init__(self, db: Session):
        """
        Inicializa o controller com uma sessão do banco de dados.
        
        Args:
            db: Sessão do SQLAlchemy
        """
        self._db = db
    
    # -------------------------
    # MOTO
    # -------------------------
    def cadastrar_moto(self, moto: Moto) -> None:
        """
        Cadastra uma moto no banco de dados.
        """
        if not isinstance(moto, Moto):
            raise ValueError("Objeto inválido, esperado Moto.")
        
        # Valida formato da placa
        valida, msg_erro = validar_placa_brasileira(moto.placa)
        if not valida:
            raise ValueError(msg_erro)
        
        # Verifica se já existe
        if MotoRepository.buscar_por_placa(self._db, moto.placa):
            raise ValueError(f"Moto com placa {moto.placa} já cadastrada.")
        
        MotoRepository.criar(self._db, moto)
    
    def get_moto_por_placa(self, placa: str) -> Optional[Moto]:
        """
        Busca moto pela placa. Retorna None se não encontrar.
        """
        moto_db = MotoRepository.buscar_por_placa(self._db, placa)
        if moto_db:
            return moto_db_para_dominio(moto_db)
        return None
    
    def buscar_moto_por_placa(self, placa: str) -> Moto:
        """
        Busca moto pela placa.
        - Se encontrar, retorna a Moto.
        - Se NÃO encontrar, lança MotoNaoEncontradaError.
        """
        moto = self.get_moto_por_placa(placa)
        if moto is None:
            raise MotoNaoEncontradaError(placa)
        return moto
    
    def listar_motos(self) -> List[Moto]:
        """
        Retorna a lista de motos cadastradas.
        """
        motos_db = MotoRepository.listar_todas(self._db)
        return [moto_db_para_dominio(m) for m in motos_db]
    
    def buscar_motos_por_modelo(self, termo_modelo: str) -> List[Moto]:
        """
        Busca motos pelo modelo (nome), ignorando maiúsculas/minúsculas
        e permitindo buscas parciais.
        """
        if not termo_modelo:
            return []
        
        motos_db = MotoRepository.buscar_por_modelo(self._db, termo_modelo)
        return [moto_db_para_dominio(m) for m in motos_db]
    
    def atualizar_moto(self, placa: str, **kwargs) -> Optional[Moto]:
        """
        Atualiza os dados de uma moto existente.
        Retorna a moto atualizada ou None se não encontrada.
        """
        moto_db = MotoRepository.buscar_por_placa(self._db, placa)
        if moto_db is None:
            return None
        
        # Prepara dados para atualização
        dados_atualizacao = {}
        if 'marca' in kwargs and kwargs['marca'] is not None:
            dados_atualizacao['marca'] = kwargs['marca'].strip().upper()
        if 'modelo' in kwargs and kwargs['modelo'] is not None:
            dados_atualizacao['modelo'] = kwargs['modelo'].strip().upper()
        if 'ano' in kwargs and kwargs['ano'] is not None:
            dados_atualizacao['ano'] = kwargs['ano']
        if 'cilindradas' in kwargs and kwargs['cilindradas'] is not None:
            dados_atualizacao['cilindradas'] = kwargs['cilindradas']
        if 'categoria' in kwargs and kwargs['categoria'] is not None:
            from modelo.categoria_moto import CategoriaMoto
            categoria = kwargs['categoria']
            if isinstance(categoria, str):
                for cat in CategoriaMoto:
                    if cat.value == categoria or cat.name == categoria:
                        dados_atualizacao['categoria'] = cat
                        break
            else:
                dados_atualizacao['categoria'] = categoria
        
        # Atualiza no banco
        MotoRepository.atualizar(self._db, moto_db, **dados_atualizacao)
        return moto_db_para_dominio(moto_db)
    
    def deletar_moto(self, placa: str) -> bool:
        """
        Remove uma moto do sistema e todos os seus checklists.
        Retorna True se a moto foi removida, False se não foi encontrada.
        """
        moto_db = MotoRepository.buscar_por_placa(self._db, placa)
        if moto_db is None:
            return False
        
        MotoRepository.deletar(self._db, moto_db)
        return True
    
    # -------------------------
    # CHECKLISTS
    # -------------------------
    def registrar_checklist(self, checklist: Checklist) -> int:
        """
        Registra um checklist de revisão no banco de dados.
        Garante que a moto do checklist está cadastrada.
        Valida KM e custos antes de registrar.
        Retorna o ID único do checklist.
        """
        if not isinstance(checklist, Checklist):
            raise ValueError("Checklist inválido.")
        
        # Validações
        from .validadores_checklist import (
            validar_km_revisao,
            validar_custo_total,
            obter_ultimo_checklist
        )
        
        # Valida KM
        ultimo_checklist = obter_ultimo_checklist(self, checklist.moto.placa)
        km_valido, msg_km = validar_km_revisao(checklist.moto, checklist.km_atual, ultimo_checklist)
        if not km_valido:
            raise ValueError(msg_km)
        
        # Valida custo total
        custo_total = checklist.custo_total_estimado()
        custo_valido, msg_custo = validar_custo_total(custo_total)
        if not custo_valido:
            raise ValueError(msg_custo)
        
        # Se há alerta de KM (mas é válido), loga mas continua
        if msg_km:
            from utils.logger import logger
            logger.warning(f"Alerta KM para {checklist.moto.placa}: {msg_km}")
        
        # Se há alerta de custo (mas é válido), loga mas continua
        if msg_custo:
            from utils.logger import logger
            logger.warning(f"Alerta custo para {checklist.moto.placa}: {msg_custo}")
        
        # Garante que a moto do checklist está cadastrada
        moto_db = MotoRepository.buscar_por_placa(self._db, checklist.moto.placa)
        if moto_db is None:
            # Cadastra a moto automaticamente
            self.cadastrar_moto(checklist.moto)
            moto_db = MotoRepository.buscar_por_placa(self._db, checklist.moto.placa)
        
        checklist_db = ChecklistRepository.criar(self._db, checklist, moto_db)
        return checklist_db.id
    
    def buscar_checklist_por_id(self, checklist_id: int) -> Optional[Checklist]:
        """Busca um checklist pelo ID único."""
        checklist_db = ChecklistRepository.buscar_por_id(self._db, checklist_id)
        if checklist_db:
            return checklist_db_para_dominio(checklist_db)
        return None
    
    def get_checklists_por_moto(self, placa: str) -> List[Checklist]:
        """
        Retorna todos os checklists de uma moto específica (histórico de revisões).
        """
        if not placa:
            return []
        
        checklists_db = ChecklistRepository.buscar_por_moto(self._db, placa)
        return [checklist_db_para_dominio(c) for c in checklists_db]
    
    def listar_checklists(self, finalizado: Optional[bool] = None, pago: Optional[bool] = None) -> List[Checklist]:
        """
        Retorna todos os checklists registrados.
        """
        checklists_db = ChecklistRepository.listar_todos(self._db, finalizado=finalizado, pago=pago)
        return [checklist_db_para_dominio(c) for c in checklists_db]
    
    def atualizar_status_checklist(
        self,
        checklist_id: int,
        finalizado: Optional[bool] = None,
        pago: Optional[bool] = None,
        custo_real: Optional[float] = None
    ) -> Optional[Checklist]:
        """
        Atualiza o status de finalização, pagamento e/ou custo real de um checklist.
        """
        checklist_db = ChecklistRepository.buscar_por_id(self._db, checklist_id)
        if not checklist_db:
            return None
        
        if finalizado is not None:
            checklist_db.finalizado = finalizado
        if pago is not None:
            checklist_db.pago = pago
        if custo_real is not None:
            if custo_real < 0:
                raise ValueError("Custo real não pode ser negativo.")
            checklist_db.custo_real = custo_real
        
        self._db.commit()
        self._db.refresh(checklist_db)
        return checklist_db_para_dominio(checklist_db)
    
    def deletar_checklist(self, checklist: Checklist) -> bool:
        """
        Remove um checklist do sistema.
        Retorna True se foi removido, False se não foi encontrado.
        """
        if checklist.id is None:
            return False
        
        checklist_db = ChecklistRepository.buscar_por_id(self._db, checklist.id)
        if checklist_db:
            ChecklistRepository.deletar(self._db, checklist_db)
            return True
        return False
    
    def deletar_checklist_por_id(self, checklist_id: int) -> bool:
        """Remove um checklist pelo ID."""
        checklist_db = ChecklistRepository.buscar_por_id(self._db, checklist_id)
        if checklist_db:
            ChecklistRepository.deletar(self._db, checklist_db)
            return True
        return False
    
    def buscar_checklists_por_periodo(
        self,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None
    ) -> List[Checklist]:
        """Busca checklists por período de datas."""
        checklists_db = ChecklistRepository.listar_todos(
            self._db,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        return [checklist_db_para_dominio(c) for c in checklists_db]
    
    def buscar_checklists_por_status_item(self, status: StatusItem) -> List[Checklist]:
        """Busca checklists que possuem pelo menos um item com o status especificado."""
        # Usa query otimizada do repository
        checklists_db = ChecklistRepository.buscar_por_status_item(self._db, status)
        return [checklist_db_para_dominio(c) for c in checklists_db]
    
    def atualizar_item_checklist(
        self,
        checklist_id: int,
        item_index: int,
        status: Optional[StatusItem] = None,
        custo_estimado: Optional[float] = None
    ) -> bool:
        """
        Atualiza um item específico de um checklist.
        Retorna True se atualizado com sucesso.
        """
        return ChecklistRepository.atualizar_item(
            self._db, checklist_id, item_index, status, custo_estimado
        )

