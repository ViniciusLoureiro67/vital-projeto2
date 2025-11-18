# database.py
"""
Configuração do banco de dados com SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Cria engine do PostgreSQL
# Se usar psycopg3, a URL deve ser postgresql+psycopg://
# Se usar psycopg2, a URL deve ser postgresql:// ou postgresql+psycopg2://
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://") and "psycopg" not in database_url:
    # Tenta usar psycopg3 se disponível, senão usa psycopg2
    try:
        import psycopg
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    except ImportError:
        # Usa psycopg2 se psycopg3 não estiver disponível
        pass

engine = create_engine(
    database_url,
    pool_pre_ping=True,  # Verifica conexões antes de usar
    echo=settings.ENVIRONMENT == "development"  # Log SQL em desenvolvimento
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()


def get_db():
    """
    Dependency para obter sessão do banco de dados.
    Usado com FastAPI Depends.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Cria todas as tabelas no banco de dados."""
    Base.metadata.create_all(bind=engine)

