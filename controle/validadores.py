# controle/validadores.py
"""
Utilitários de validação para o sistema da oficina.
"""
import re
from typing import Optional


def validar_placa_brasileira(placa: str) -> tuple[bool, Optional[str]]:
    """
    Valida se a placa está no formato brasileiro (antigo ou Mercosul).
    
    Formatos aceitos:
    - Antigo: ABC-1234 (3 letras, hífen, 4 dígitos)
    - Mercosul: ABC1D23 (3 letras, 1 dígito, 1 letra, 2 dígitos)
    - Alternativo: ABC321 (mínimo 6 caracteres alfanuméricos)
    
    Retorna: (é_válida, mensagem_erro)
    """
    if not placa:
        return False, "Placa não pode ser vazia."
    
    # Remove espaços e hífens para normalizar
    placa_limpa = placa.strip().upper().replace("-", "").replace(" ", "")
    
    # Verifica tamanho mínimo
    if len(placa_limpa) < 6:
        return False, "Placa deve ter no mínimo 6 caracteres."
    
    if len(placa_limpa) > 8:
        return False, "Placa deve ter no máximo 8 caracteres."
    
    # Formato antigo: ABC1234 (7 caracteres)
    padrao_antigo = re.compile(r'^[A-Z]{3}\d{4}$')
    
    # Formato Mercosul: ABC1D23 (7 caracteres)
    padrao_mercosul = re.compile(r'^[A-Z]{3}\d[A-Z]\d{2}$')
    
    # Formato alternativo: mínimo 6 caracteres alfanuméricos
    padrao_alternativo = re.compile(r'^[A-Z0-9]{6,8}$')
    
    if padrao_antigo.match(placa_limpa):
        return True, None
    elif padrao_mercosul.match(placa_limpa):
        return True, None
    elif padrao_alternativo.match(placa_limpa):
        return True, None
    else:
        return False, (
            "Placa inválida. Use o formato antigo (ABC-1234), "
            "Mercosul (ABC1D23) ou formato alternativo (mínimo 6 caracteres alfanuméricos)."
        )


def normalizar_placa(placa: str) -> str:
    """
    Normaliza a placa removendo espaços e hífens, deixando em maiúsculas.
    """
    if not placa:
        return ""
    return placa.strip().upper().replace("-", "").replace(" ", "")

