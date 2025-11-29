#!/usr/bin/env python
"""Script para testar a API e identificar erros."""
import sys
from fastapi.testclient import TestClient
from api.main_local import app, controller
from main import popular_dados_exemplo

# Popula dados de exemplo
print("Populando dados de exemplo...")
popular_dados_exemplo(controller)

# Cria cliente de teste
client = TestClient(app)

# Testa o endpoint que está falhando
print("\nTestando GET /api/checklists?ordenar_por=data&limit=10")
try:
    response = client.get("/api/checklists?ordenar_por=data&limit=10")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Checklists retornados: {len(data)}")
        if data:
            print(f"Primeiro checklist: {list(data[0].keys())}")
    else:
        print(f"Erro: {response.text}")
except Exception as e:
    print(f"Exceção capturada: {e}")
    import traceback
    traceback.print_exc()

