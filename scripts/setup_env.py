# scripts/setup_env.py
"""
Script para criar arquivo .env e testar conexão com banco.
"""
import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

def criar_env():
    """Cria arquivo .env se não existir."""
    env_path = Path(".env")
    
    if env_path.exists():
        print("[OK] Arquivo .env ja existe.")
        return
    
    # Valores padrão
    env_content = """# Database Configuration
# Ajuste as credenciais conforme seu PostgreSQL
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/oficina_vital

# JWT Configuration
# IMPORTANTE: Altere esta chave em producao!
SECRET_KEY=oficina-vital-secret-key-change-in-production-2024
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
"""
    
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(env_content)
    
    print("[OK] Arquivo .env criado com sucesso!")
    print("     Ajuste DATABASE_URL com suas credenciais do PostgreSQL")


def testar_conexao():
    """Testa conexão com o banco de dados."""
    try:
        from config import settings
        from sqlalchemy import create_engine, text
        
        db_info = settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'banco configurado'
        print(f"\n[TESTE] Testando conexao com: {db_info}...")
        
        # Tenta criar engine
        database_url = settings.DATABASE_URL
        if database_url.startswith("postgresql://") and "psycopg" not in database_url:
            try:
                import psycopg
                database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
            except ImportError:
                pass
        
        engine = create_engine(database_url, pool_pre_ping=True)
        
        # Tenta conectar
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"[OK] Conexao bem-sucedida!")
            print(f"     PostgreSQL: {version.split(',')[0]}")
            return True
            
    except Exception as e:
        print(f"[ERRO] Erro ao conectar: {e}")
        print("\n[DICAS]")
        print("    1. Verifique se o PostgreSQL esta instalado e rodando")
        print("    2. Verifique se o banco 'oficina_vital' existe")
        print("    3. Ajuste DATABASE_URL no arquivo .env")
        print("    4. Credenciais padrao: postgres/postgres")
        return False


if __name__ == "__main__":
    print("[SETUP] Configurando ambiente...\n")
    
    # Cria .env
    criar_env()
    
    # Testa conexão
    print()
    testar_conexao()

