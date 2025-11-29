# controle/excecoes.py

class OficinaError(Exception):
    """Erro genérico da Oficina Vital."""
    pass


class MotoNaoEncontradaError(OficinaError):
    """Lançada quando uma moto não é encontrada pela placa."""

    def __init__(self, placa: str):
        super().__init__(f"Moto com placa {placa} não encontrada.")
        self.placa = placa


class ChecklistNaoEncontradoError(OficinaError):
    """Lançada quando um checklist não é encontrado pelo ID."""

    def __init__(self, checklist_id: int):
        super().__init__(f"Checklist com ID {checklist_id} não encontrado.")
        self.checklist_id = checklist_id


class ValidacaoError(OficinaError):
    """Lançada quando ocorre um erro de validação de dados."""

    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem