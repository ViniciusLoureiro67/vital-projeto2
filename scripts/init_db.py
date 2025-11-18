# scripts/init_db.py
"""
Script para inicializar o banco de dados.
Cria as tabelas e um usuário administrador inicial.
"""
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import init_db, SessionLocal
from db.repository import UsuarioRepository
from auth.security import get_password_hash

def criar_admin_inicial():
    """Cria usuário administrador inicial."""
    db = SessionLocal()
    try:
        # Verifica se já existe admin
        admin = UsuarioRepository.buscar_por_username(db, "admin")
        if admin:
            print("Usuário 'admin' já existe. Pulando criação.")
            return
        
        # Cria admin
        hashed_password = get_password_hash("admin123")
        UsuarioRepository.criar(
            db,
            username="admin",
            email="admin@oficina.com",
            hashed_password=hashed_password,
            is_admin=True
        )
        print("[OK] Usuario administrador criado com sucesso!")
        print("     Username: admin")
        print("     Password: admin123")
        print("     [AVISO] ALTERE A SENHA APOS O PRIMEIRO LOGIN!")
    except Exception as e:
        print(f"[ERRO] Erro ao criar usuario admin: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    print("[INIT] Inicializando banco de dados...")
    
    # Cria tabelas
    try:
        init_db()
        print("[OK] Tabelas criadas com sucesso!")
    except Exception as e:
        print(f"[ERRO] Erro ao criar tabelas: {e}")
        print("\n[DICAS]")
        print("    1. Verifique se o PostgreSQL esta instalado e rodando")
        print("    2. Verifique se o banco 'oficina_vital' existe")
        print("    3. Ajuste DATABASE_URL no arquivo .env")
        sys.exit(1)
    
    # Cria usuário admin
    criar_admin_inicial()
    
    print("\n[OK] Banco de dados inicializado com sucesso!")

