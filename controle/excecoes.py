# controle/excecoes.py

class OficinaError(Exception):
    """Erro genérico da Oficina Vital."""
    pass


class MotoNaoEncontradaError(OficinaError):
    """Lançada quando uma moto não é encontrada pela placa."""

    def __init__(self, placa: str):
        super().__init__(f"Moto com placa {placa} não encontrada.")
        self.placa = placa
