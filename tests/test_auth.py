# tests/test_auth.py
"""
Testes para autenticação.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main_db import app
from database import get_db
from db.models import UsuarioDB
from db.repository import UsuarioRepository
from auth.security import get_password_hash

client = TestClient(app)


@pytest.fixture
def db_session():
    """Fixture para sessão de banco de dados de teste."""
    # Em produção, usar banco de teste separado
    from database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session: Session):
    """Cria um usuário de teste."""
    hashed_password = get_password_hash("testpassword")
    user = UsuarioRepository.criar(
        db_session,
        username="testuser",
        email="test@example.com",
        hashed_password=hashed_password
    )
    return user


def test_register_user():
    """Testa registro de novo usuário."""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword",
            "is_admin": False
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "password" not in data


def test_login_success(test_user):
    """Testa login bem-sucedido."""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "testpassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials():
    """Testa login com credenciais inválidas."""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "nonexistent",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401


def test_get_current_user(test_user):
    """Testa obtenção de informações do usuário atual."""
    # Primeiro faz login
    login_response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "testpassword"
        }
    )
    token = login_response.json()["access_token"]
    
    # Depois busca informações
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"

