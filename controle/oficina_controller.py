# controle/oficina_controller.py
from .excecoes import MotoNaoEncontradaError
from typing import List, Optional

from modelo.moto import Moto
from modelo.checklist import Checklist


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
    def registrar_checklist(self, checklist: Checklist) -> None:
        """
        Registra um checklist de revisão.
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

        self._checklists.append(checklist)
        print(
            f"LOG: Checklist registrado para moto {checklist.moto.placa} "
            f"na data {checklist.data_formatada}."
        )

    def get_checklists_por_moto(self, placa: str) -> List[Checklist]:
        """
        Retorna todos os checklists de uma moto específica (histórico de revisões).
        """
        if not placa:
            return []

        placa = placa.strip().upper()
        return [c for c in self._checklists if c.moto.placa == placa]

    def listar_checklists(self) -> List[Checklist]:
        """
        Retorna todos os checklists registrados.
        """
        return list(self._checklists)
