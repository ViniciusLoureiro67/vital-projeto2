#!/usr/bin/env python
"""
Script simples para iniciar a API local.
Execute: python iniciar_api.py
"""
import uvicorn

if __name__ == "__main__":
    print("=" * 50)
    print("  Iniciando Oficina Vital API - Modo Local")
    print("=" * 50)
    print("\nAcesse:")
    print("  - Swagger UI: http://127.0.0.1:8000/docs")
    print("  - ReDoc: http://127.0.0.1:8000/redoc")
    print("  - Health: http://127.0.0.1:8000/health")
    print("\nPressione Ctrl+C para parar\n")
    print("=" * 50)
    print()
    
    try:
        uvicorn.run(
            "api.main_local:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\nServidor encerrado.")
    except Exception as e:
        print(f"\n[ERRO] Nao foi possivel iniciar o servidor:")
        print(f"  {e}")
        print("\nVerifique se todas as dependencias estao instaladas:")
        print("  pip install -r requirements.txt")

