# utils/logger.py
"""
Configuração de logging estruturado.
"""
import logging
import sys
from pythonjsonlogger import jsonlogger
from config import settings


def setup_logger():
    """
    Configura o logger da aplicação com formato JSON.
    """
    logger = logging.getLogger("oficina_vital")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    
    # Handler para console
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    
    # Formato JSON
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# Logger global
logger = setup_logger()

