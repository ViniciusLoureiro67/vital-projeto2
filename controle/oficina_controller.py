# controle/oficina_controller.py
from .excecoes import MotoNaoEncontradaError
from typing import List, Optional
from datetime import date

from modelo.moto import Moto
from modelo.checklist import Checklist
from modelo.checklist_item import ChecklistItem, StatusItem


class OficinaController:
    """
    Controlador principal da oficina.
    - Gerencia motos cadastradas
    - Gerencia checklists de revisão
    """

    def __init__(self):
        self._motos: List[Moto] = []
        self._checklists: List[Checklist] = []
        print("LOG: OficinaController inicializado.")

    # -------------------------
    # MOTO
    # -------------------------
    def cadastrar_moto(self, moto: Moto) -> None:
        """
        Cadastra uma moto, evitando duplicidade de placa.
        """
        if not isinstance(moto, Moto):
            raise ValueError("Objeto inválido, esperado Moto.")

        # Verifica se já existe moto com essa placa
        if self.get_moto_por_placa(moto.placa) is not None:
            print(f"LOG: Moto com placa {moto.placa} já cadastrada. Ignorando.")
            return

        self._motos.append(moto)
        print(f"LOG: Moto cadastrada: {moto.placa} - {moto.modelo}")

    def get_moto_por_placa(self, placa: str) -> Optional[Moto]:
        """
        Busca moto pela placa. Retorna None se não encontrar.
        """
        if not placa:
            return None

        placa = placa.strip().upper()
        for m in self._motos:
            if m.placa == placa:
                return m
        return None


    def buscar_moto_por_placa(self, placa: str) -> Moto:
        """
        Busca moto pela placa.
        - Se encontrar, retorna a Moto.
        - Se NÃO encontrar, lança MotoNaoEncontradaError.
        """
        moto = self.get_moto_por_placa(placa)
        if moto is None:
            # aqui entra nossa exceção personalizada
            raise MotoNaoEncontradaError(placa)
        return moto

    def listar_motos(self) -> List[Moto]:
        """
        Retorna a lista de motos cadastradas.
        """
        return list(self._motos)

    def buscar_motos_por_modelo(self, termo_modelo: str) -> List[Moto]:
        """
        Busca motos pelo modelo (nome), ignorando maiúsculas/minúsculas
        e permitindo buscas parciais.
        Exemplo: 'mt-07' ou 'mt' retorna todas as MT-07 cadastradas.
        """
        if not termo_modelo:
            return []

        termo = termo_modelo.strip().lower()
        return [m for m in self._motos if termo in m.modelo.lower()]


    # -------------------------
    # CHECKLISTS
    # -------------------------
    def registrar_checklist(self, checklist: Checklist) -> int:
        """
        Registra um checklist de revisão.
        Retorna o ID do checklist (índice na lista + 1).
        """
        if not isinstance(checklist, Checklist):
            raise ValueError("Checklist inválido.")

        # Garante que a moto do checklist está cadastrada
        moto = self.get_moto_por_placa(checklist.moto.placa)
        if moto is None:
            print(
                f"LOG: Moto {checklist.moto.placa} não estava cadastrada. "
                "Cadastrando automaticamente."
            )
            self.cadastrar_moto(checklist.moto)

        # Atribui um ID se não tiver
        if checklist.id is None:
            checklist._id = len(self._checklists) + 1
        
        self._checklists.append(checklist)
        print(
            f"LOG: Checklist registrado para moto {checklist.moto.placa} "
            f"na data {checklist.data_formatada}."
        )
        return checklist.id

    def get_checklists_por_moto(self, placa: str) -> List[Checklist]:
        """
        Retorna todos os checklists de uma moto específica (histórico de revisões).
        """
        if not placa:
            return []

        placa = placa.strip().upper()
        return [c for c in self._checklists if c.moto.placa == placa]

    def listar_checklists(self, finalizado: Optional[bool] = None, pago: Optional[bool] = None) -> List[Checklist]:
        """
        Retorna todos os checklists registrados, opcionalmente filtrados por status.
        
        Args:
            finalizado: Se True, retorna apenas finalizados. Se False, apenas não finalizados. Se None, todos.
            pago: Se True, retorna apenas pagos. Se False, apenas não pagos. Se None, todos.
        """
        checklists = list(self._checklists)
        
        # Aplica filtros se fornecidos
        if finalizado is not None:
            checklists = [c for c in checklists if c.finalizado == finalizado]
        
        if pago is not None:
            checklists = [c for c in checklists if c.pago == pago]
        
        return checklists
    
    def buscar_checklist_por_id(self, checklist_id: int) -> Optional[Checklist]:
        """Busca um checklist pelo ID único."""
        for checklist in self._checklists:
            if checklist.id == checklist_id:
                return checklist
        return None
    
    def deletar_checklist_por_id(self, checklist_id: int) -> bool:
        """Remove um checklist pelo ID."""
        for i, checklist in enumerate(self._checklists):
            if checklist.id == checklist_id:
                self._checklists.pop(i)
                return True
        return False
    
    def buscar_checklists_por_periodo(
        self,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None
    ) -> List[Checklist]:
        """Busca checklists por período de datas."""
        checklists = list(self._checklists)
        
        if data_inicio:
            checklists = [c for c in checklists if c.data_revisao >= data_inicio]
        
        if data_fim:
            checklists = [c for c in checklists if c.data_revisao <= data_fim]
        
        return checklists
    
    def buscar_checklists_por_status_item(self, status: StatusItem) -> List[Checklist]:
        """Busca checklists que possuem pelo menos um item com o status especificado."""
        resultado = []
        for checklist in self._checklists:
            for item in checklist.itens:
                if item.status == status:
                    resultado.append(checklist)
                    break
        return resultado
    
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
        checklist = self.buscar_checklist_por_id(checklist_id)
        if not checklist:
            return False
        
        if item_index < 0 or item_index >= len(checklist._itens):
            return False
        
        item = checklist._itens[item_index]
        
        if status is not None:
            item.status = status
        
        if custo_estimado is not None:
            item.custo_estimado = custo_estimado
        
        return True
    
    def adicionar_item_checklist(
        self,
        checklist_id: int,
        nome: str,
        categoria: str,
        status: StatusItem,
        custo_estimado: float = 0.0
    ) -> bool:
        """
        Adiciona um novo item customizado ao checklist.
        Retorna True se adicionado com sucesso.
        """
        checklist = self.buscar_checklist_por_id(checklist_id)
        if not checklist:
            return False
        
        item = ChecklistItem(nome=nome, categoria=categoria, status=status, custo_estimado=custo_estimado)
        checklist.adicionar_item(item)
        return True
    
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
        checklist = self.buscar_checklist_por_id(checklist_id)
        if not checklist:
            return None
        
        if finalizado is not None:
            checklist.finalizado = finalizado
        
        if pago is not None:
            checklist.pago = pago
        
        if custo_real is not None:
            if custo_real < 0:
                raise ValueError("Custo real não pode ser negativo.")
            checklist.custo_real = custo_real
        
        return checklist
    
    def deletar_moto(self, placa: str) -> bool:
        """
        Remove uma moto do sistema.
        Retorna True se foi removida, False se não foi encontrada.
        """
        moto = self.get_moto_por_placa(placa)
        if moto is None:
            return False
        
        # Remove checklists relacionados
        self._checklists = [c for c in self._checklists if c.moto.placa != placa]
        
        # Remove a moto
        self._motos = [m for m in self._motos if m.placa != placa]
        
        return True
