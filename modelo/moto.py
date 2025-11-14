# modelo/moto.py
from .veiculo import Veiculo

class Moto(Veiculo):
    """
    Representa uma moto cadastrada na oficina.
    Equivalente à classe Moto do Java.
    """

    def __init__(self, placa: str, marca: str, modelo: str, ano: int, cilindradas: int):
        super().__init__(placa, marca, modelo, ano)
        self._set_cilindradas(cilindradas)

    @property
    def cilindradas(self) -> int:
        return self._cilindradas

    def _set_cilindradas(self, cilindradas: int) -> None:
        if cilindradas <= 0:
            raise ValueError("Cilindrada inválida.")
        self._cilindradas = cilindradas

    def exibir_info(self) -> str:
        return (
            f"MOTO - Placa: {self.placa} | Marca: {self.marca} | "
            f"Modelo: {self.modelo} | Ano: {self.ano} | "
            f"Cilindradas: {self.cilindradas}cc"
        )
