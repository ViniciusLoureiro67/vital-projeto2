# tests/test_motos.py
"""
Testes para endpoints de motos.
"""
import pytest
from fastapi.testclient import TestClient

from api.main_db import app
from auth.security import get_password_hash
from db.repository import UsuarioRepository
from database import SessionLocal

client = TestClient(app)


@pytest.fixture
def auth_token():
    """Cria um token de autenticação para testes."""
    db = SessionLocal()
    try:
        # Cria usuário de teste se não existir
        user = UsuarioRepository.buscar_por_username(db, "testuser")
        if not user:
            hashed_password = get_password_hash("testpassword")
            UsuarioRepository.criar(
                db,
                username="testuser",
                email="test@example.com",
                hashed_password=hashed_password
            )
        
        # Faz login
        response = client.post(
            "/api/auth/login",
            data={
                "username": "testuser",
                "password": "testpassword"
            }
        )
        return response.json()["access_token"]
    finally:
        db.close()


def test_listar_motos_sem_auth():
    """Testa que listar motos requer autenticação."""
    response = client.get("/api/motos")
    assert response.status_code == 401


def test_listar_motos_com_auth(auth_token):
    """Testa listagem de motos com autenticação."""
    response = client.get(
        "/api/motos",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_cadastrar_moto(auth_token):
    """Testa cadastro de nova moto."""
    response = client.post(
        "/api/motos",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "placa": "ABC1234",
            "marca": "Yamaha",
            "modelo": "MT-07",
            "ano": 2022,
            "cilindradas": 689,
            "categoria": "NAKED"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["placa"] == "ABC1234"
    assert data["modelo"] == "MT-07"


def test_cadastrar_moto_placa_invalida(auth_token):
    """Testa cadastro com placa inválida."""
    response = client.post(
        "/api/motos",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "placa": "INVALID",
            "marca": "Yamaha",
            "modelo": "MT-07",
            "ano": 2022,
            "cilindradas": 689,
            "categoria": "NAKED"
        }
    )
    assert response.status_code == 400


def test_buscar_moto_por_placa(auth_token):
    """Testa busca de moto por placa."""
    # Primeiro cadastra uma moto
    client.post(
        "/api/motos",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "placa": "XYZ9876",
            "marca": "Honda",
            "modelo": "CB600F",
            "ano": 2021,
            "cilindradas": 600,
            "categoria": "NAKED"
        }
    )
    
    # Depois busca
    response = client.get(
        "/api/motos/XYZ9876",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["placa"] == "XYZ9876"

