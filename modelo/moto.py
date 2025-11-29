# modelo/moto.py
from .veiculo import Veiculo
from .categoria_moto import CategoriaMoto  # <-- NOVO IMPORT

class Moto(Veiculo):
    """
    Representa uma moto cadastrada na oficina.
    Equivalente à classe Moto do Java.
    """

    def __init__(
        self,
        placa: str,
        marca: str,
        modelo: str,
        ano: int,
        cilindradas: int,
        categoria: CategoriaMoto = CategoriaMoto.OUTROS,  # <-- NOVO PARÂMETRO
    ):
        super().__init__(placa, marca, modelo, ano)
        self._set_cilindradas(cilindradas)
        self._categoria = categoria  # simples, sem setter chato

    @property
    def cilindradas(self) -> int:
        return self._cilindradas

    def _set_cilindradas(self, cilindradas: int) -> None:
        if cilindradas <= 0:
            raise ValueError("Cilindrada inválida.")
        self._cilindradas = cilindradas

    @property
    def categoria(self) -> CategoriaMoto:
        return self._categoria

    def exibir_info(self) -> str:
        # Agora já usamos categoria no texto
        return (
            f"MOTO [{self.categoria.value}] - Placa: {self.placa} | "
            f"Marca: {self.marca} | Modelo: {self.modelo} | "
            f"Ano: {self.ano} | Cilindradas: {self.cilindradas}cc"
        )
    
    def to_dict(self) -> dict:
        """Converte a moto para dicionário (serialização JSON)."""
        return {
            "placa": self.placa,
            "marca": self.marca,
            "modelo": self.modelo,
            "ano": self.ano,
            "cilindradas": self.cilindradas,
            "categoria": self.categoria.value,
            "categoria_enum": self.categoria.name
        }