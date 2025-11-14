# modelo/veiculo.py
from abc import ABC, abstractmethod

class Veiculo(ABC):
    """
    Classe base abstrata para veículos.
    Equivalente à classe Veiculo do Java:
    - placa
    - marca
    - modelo
    - ano
    """

    def __init__(self, placa: str, marca: str, modelo: str, ano: int):
        self._set_placa(placa)
        self._set_marca(marca)
        self._set_modelo(modelo)
        self._set_ano(ano)

    # --- propriedades (encapsulamento) ---

    @property
    def placa(self) -> str:
        return self._placa

    def _set_placa(self, placa: str) -> None:
        if not placa or not placa.strip():
            raise ValueError("Placa é obrigatória.")
        self._placa = placa.strip().upper()

    @property
    def marca(self) -> str:
        return self._marca

    def _set_marca(self, marca: str) -> None:
        if not marca or not marca.strip():
            raise ValueError("Marca é obrigatória.")
        self._marca = marca.strip()

    @property
    def modelo(self) -> str:
        return self._modelo

    def _set_modelo(self, modelo: str) -> None:
        if not modelo or not modelo.strip():
            raise ValueError("Modelo é obrigatório.")
        self._modelo = modelo.strip()

    @property
    def ano(self) -> int:
        return self._ano

    def _set_ano(self, ano: int) -> None:
        if ano < 1900:
            raise ValueError("Ano inválido.")
        self._ano = ano

    # --- método abstrato (polimorfismo) ---
    @abstractmethod
    def exibir_info(self) -> str:
        """Deve ser implementado por subclasses como Moto, Carro, etc."""
        pass

    def __repr__(self) -> str:
        return f"Veiculo(placa={self.placa}, marca={self.marca}, modelo={self.modelo}, ano={self.ano})"
