# api/main.py
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import date

from controle.oficina_controller import OficinaController
from controle.excecoes import (
    MotoNaoEncontradaError,
    ChecklistNaoEncontradoError,
    ItemChecklistNaoEncontradoError,
    ValidacaoError
)
from controle.validadores import normalizar_placa, validar_placa_brasileira
from analytics.oficina_analytics import OficinaAnalytics
from modelo.moto import Moto
from modelo.categoria_moto import CategoriaMoto
from modelo.checklist import Checklist
from modelo.checklist_item import ChecklistItem, StatusItem
from modelo.checklist_templates import criar_checklist_padrao, criar_checklist_adaptativo
from api.schemas import (
    MotoCreate, MotoUpdate, MotoResponse,
    ChecklistCreate, ChecklistUpdate, ChecklistResponse,
    ChecklistItemCreate, ChecklistItemResponse,
    AnalyticsResponse
)

app = FastAPI(
    title="Oficina Vital API",
    description="API REST para gerenciamento de oficina de motos",
    version="1.0.0"
)

# Configurar CORS para permitir requisições do React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instâncias globais (em produção, usar injeção de dependência)
controller = OficinaController()
analytics = OficinaAnalytics(controller)


# ==================== ENDPOINTS DE MOTOS ====================

@app.get("/api/motos", response_model=List[MotoResponse], tags=["Motos"])
def listar_motos(
    skip: int = 0,
    limit: Optional[int] = None,
    ordenar_por: Optional[str] = None
):
    """
    Lista todas as motos cadastradas com paginação e ordenação.
    - skip: Número de registros para pular (padrão: 0)
    - limit: Número máximo de registros a retornar (padrão: todos)
    - ordenar_por: Campo para ordenação (placa, modelo, ano, marca)
    """
    motos = controller.listar_motos()
    
    # Ordenação
    if ordenar_por:
        ordenar_por = ordenar_por.lower()
        if ordenar_por == "placa":
            motos = sorted(motos, key=lambda m: m.placa)
        elif ordenar_por == "modelo":
            motos = sorted(motos, key=lambda m: m.modelo)
        elif ordenar_por == "ano":
            motos = sorted(motos, key=lambda m: m.ano, reverse=True)
        elif ordenar_por == "marca":
            motos = sorted(motos, key=lambda m: m.marca)
    
    # Paginação
    if limit:
        motos = motos[skip:skip + limit]
    else:
        motos = motos[skip:]
    
    return [m.to_dict() for m in motos]


@app.get("/api/motos/{placa}", response_model=MotoResponse, tags=["Motos"])
def buscar_moto_por_placa(placa: str):
    """Busca uma moto pela placa."""
    try:
        moto = controller.buscar_moto_por_placa(placa)
        return moto.to_dict()
    except MotoNaoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Moto com placa {placa} não encontrada."
        )


@app.get("/api/motos/buscar/modelo", response_model=List[MotoResponse], tags=["Motos"])
def buscar_motos_por_modelo(termo: str):
    """Busca motos por modelo (busca parcial, case-insensitive)."""
    motos = controller.buscar_motos_por_modelo(termo)
    return [m.to_dict() for m in motos]


@app.post("/api/motos", response_model=MotoResponse, status_code=status.HTTP_201_CREATED, tags=["Motos"])
def cadastrar_moto(moto_data: MotoCreate):
    """Cadastra uma nova moto."""
    try:
        # Valida placa
        valida, msg_erro = validar_placa_brasileira(moto_data.placa)
        if not valida:
            raise ValidacaoError(msg_erro)
        
        # Converte categoria string para enum
        categoria_enum = None
        for cat in CategoriaMoto:
            if cat.value == moto_data.categoria or cat.name == moto_data.categoria:
                categoria_enum = cat
                break
        
        if categoria_enum is None:
            categoria_enum = CategoriaMoto.OUTROS

        moto = Moto(
            placa=moto_data.placa,
            marca=moto_data.marca,
            modelo=moto_data.modelo,
            ano=moto_data.ano,
            cilindradas=moto_data.cilindradas,
            categoria=categoria_enum
        )
        
        controller.cadastrar_moto(moto)
        return moto.to_dict()
    except (ValueError, ValidacaoError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.put("/api/motos/{placa}", response_model=MotoResponse, tags=["Motos"])
def atualizar_moto(placa: str, moto_data: MotoUpdate):
    """Atualiza os dados de uma moto existente."""
    try:
        moto = controller.buscar_moto_por_placa(placa)
        
        # Atualiza apenas os campos fornecidos
        if moto_data.marca is not None:
            moto._set_marca(moto_data.marca)
        if moto_data.modelo is not None:
            moto._set_modelo(moto_data.modelo)
        if moto_data.ano is not None:
            moto._set_ano(moto_data.ano)
        if moto_data.cilindradas is not None:
            moto._set_cilindradas(moto_data.cilindradas)
        if moto_data.categoria is not None:
            for cat in CategoriaMoto:
                if cat.value == moto_data.categoria or cat.name == moto_data.categoria:
                    moto._categoria = cat
                    break
        
        return moto.to_dict()
    except MotoNaoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Moto com placa {placa} não encontrada."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.delete("/api/motos/{placa}", status_code=status.HTTP_204_NO_CONTENT, tags=["Motos"])
def deletar_moto(placa: str):
    """Remove uma moto do sistema."""
    sucesso = controller.deletar_moto(placa)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Moto com placa {placa} não encontrada."
        )
    return None


# ==================== ENDPOINTS DE CHECKLISTS ====================

@app.get("/api/checklists", response_model=List[ChecklistResponse], tags=["Checklists"])
def listar_checklists(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    status_item: Optional[str] = None,
    placa: Optional[str] = None,
    skip: int = 0,
    limit: Optional[int] = None,
    ordenar_por: Optional[str] = None
):
    """
    Lista checklists com filtros opcionais, paginação e ordenação.
    - data_inicio: Filtrar checklists a partir desta data
    - data_fim: Filtrar checklists até esta data
    - status_item: Filtrar por status de item (concluido, pendente, necessita_troca)
    - placa: Filtrar por placa da moto
    - skip: Número de registros para pular (padrão: 0)
    - limit: Número máximo de registros a retornar (padrão: todos)
    - ordenar_por: Campo para ordenação (data, km, custo)
    """
    if placa:
        checklists = controller.get_checklists_por_moto(placa)
    elif data_inicio or data_fim:
        checklists = controller.buscar_checklists_por_periodo(data_inicio, data_fim)
    elif status_item:
        status_enum = None
        for s in StatusItem:
            if s.value == status_item.lower() or s.name == status_item.upper():
                status_enum = s
                break
        if status_enum is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Status inválido: {status_item}"
            )
        checklists = controller.buscar_checklists_por_status_item(status_enum)
    else:
        checklists = controller.listar_checklists()
    
    # Ordenação
    if ordenar_por:
        ordenar_por = ordenar_por.lower()
        if ordenar_por == "data":
            checklists = sorted(checklists, key=lambda c: c.data_revisao, reverse=True)
        elif ordenar_por == "km":
            checklists = sorted(checklists, key=lambda c: c.km_atual, reverse=True)
        elif ordenar_por == "custo":
            checklists = sorted(checklists, key=lambda c: c.custo_total_estimado(), reverse=True)
    
    # Paginação
    if limit:
        checklists = checklists[skip:skip + limit]
    else:
        checklists = checklists[skip:]
    
    return [ch.to_dict() for ch in checklists]


@app.get("/api/checklists/moto/{placa}", response_model=List[ChecklistResponse], tags=["Checklists"])
def listar_checklists_por_moto(placa: str):
    """Lista todos os checklists de uma moto específica."""
    try:
        controller.buscar_moto_por_placa(placa)  # Verifica se a moto existe
        checklists = controller.get_checklists_por_moto(placa)
        return [ch.to_dict() for ch in checklists]
    except MotoNaoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Moto com placa {placa} não encontrada."
        )


@app.post("/api/checklists", response_model=ChecklistResponse, status_code=status.HTTP_201_CREATED, tags=["Checklists"])
def criar_checklist(checklist_data: ChecklistCreate):
    """Cria um novo checklist de revisão."""
    try:
        # Busca ou cadastra a moto
        moto = controller.get_moto_por_placa(checklist_data.placa_moto)
        if moto is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Moto com placa {checklist_data.placa_moto} não encontrada. Cadastre a moto primeiro."
            )

        # Cria o checklist adaptativo (com itens por KM)
        checklist = criar_checklist_adaptativo(
            moto=moto,
            km_atual=checklist_data.km_atual,
            data_revisao=checklist_data.data_revisao
        )

        # Se itens foram fornecidos, substitui os itens padrão
        if checklist_data.itens:
            checklist._itens = []
            for item_data in checklist_data.itens:
                # Converte status string para enum
                status_enum = StatusItem.PENDENTE
                for s in StatusItem:
                    if s.value == item_data.status or s.name == item_data.status.upper():
                        status_enum = s
                        break

                item = ChecklistItem(
                    nome=item_data.nome,
                    categoria=item_data.categoria,
                    status=status_enum,
                    custo_estimado=item_data.custo_estimado
                )
                checklist.adicionar_item(item)

        controller.registrar_checklist(checklist)
        return checklist.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/api/checklists/{checklist_id}", response_model=ChecklistResponse, tags=["Checklists"])
def buscar_checklist_por_id(checklist_id: int):
    """Busca um checklist pelo ID único."""
    try:
        checklist = controller.buscar_checklist_por_id(checklist_id)
        if not checklist:
            raise ChecklistNaoEncontradoError(checklist_id)
        return checklist.to_dict()
    except ChecklistNaoEncontradoError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.put("/api/checklists/{checklist_id}", response_model=ChecklistResponse, tags=["Checklists"])
def atualizar_checklist(checklist_id: int, checklist_data: ChecklistUpdate):
    """Atualiza um checklist existente."""
    checklist = controller.buscar_checklist_por_id(checklist_id)
    if not checklist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checklist com ID {checklist_id} não encontrado."
        )
    
    if checklist_data.km_atual is not None:
        if checklist_data.km_atual < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quilometragem não pode ser negativa."
            )
        checklist._km_atual = checklist_data.km_atual
    
    if checklist_data.data_revisao is not None:
        checklist._data_revisao = checklist_data.data_revisao
    
    return checklist.to_dict()


@app.put("/api/checklists/{checklist_id}/itens/{item_index}", response_model=ChecklistResponse, tags=["Checklists"])
def atualizar_item_checklist(
    checklist_id: int, 
    item_index: int,
    status: Optional[str] = None,
    custo_estimado: Optional[float] = None
):
    """Atualiza um item específico de um checklist."""
    # Converte status string para enum
    status_enum = None
    if status:
        for s in StatusItem:
            if s.value == status or s.name == status.upper():
                status_enum = s
                break
        if status_enum is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Status inválido: {status}"
            )
    
    sucesso = controller.atualizar_item_checklist(
        checklist_id, item_index, status_enum, custo_estimado
    )
    
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checklist ou item não encontrado."
        )
    
    checklist = controller.buscar_checklist_por_id(checklist_id)
    return checklist.to_dict()


@app.delete("/api/checklists/{checklist_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Checklists"])
def deletar_checklist(checklist_id: int):
    """Remove um checklist do sistema."""
    sucesso = controller.deletar_checklist_por_id(checklist_id)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checklist com ID {checklist_id} não encontrado."
        )
    return None


# ==================== ENDPOINTS DE ANALYTICS ====================

@app.get("/api/analytics", response_model=AnalyticsResponse, tags=["Analytics"])
def obter_analytics(
    km_futuro: Optional[int] = None,
    placa: Optional[str] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None
):
    """
    Retorna análises estatísticas dos dados da oficina.
    - km_futuro: Quilometragem para previsão de custo
    - placa: Filtrar analytics por moto específica
    - data_inicio: Filtrar por período (data início)
    - data_fim: Filtrar por período (data fim)
    """
    # Se há filtros, criar analytics temporário com dados filtrados
    if placa or data_inicio or data_fim:
        from analytics.oficina_analytics import OficinaAnalytics
        from controle.oficina_controller import OficinaController
        
        # Cria controller temporário com dados filtrados
        temp_controller = OficinaController()
        
        # Obtém checklists filtrados
        if placa:
            checklists_filtrados = controller.get_checklists_por_moto(placa)
        elif data_inicio or data_fim:
            checklists_filtrados = controller.buscar_checklists_por_periodo(data_inicio, data_fim)
        else:
            checklists_filtrados = controller.listar_checklists()
        
        # Adiciona checklists filtrados ao controller temporário
        for ch in checklists_filtrados:
            temp_controller._checklists.append(ch)
        
        temp_analytics = OficinaAnalytics(temp_controller)
        resumo = temp_analytics.resumo_custos()
        distribuicao = temp_analytics.distribuicao_status_itens()
        modelo = temp_analytics.estimar_custo_por_km()
    else:
        resumo = analytics.resumo_custos()
        distribuicao = analytics.distribuicao_status_itens()
        modelo = analytics.estimar_custo_por_km()
    
    previsao = None
    if km_futuro is not None and modelo is not None:
        if placa or data_inicio or data_fim:
            previsao = temp_analytics.prever_custo_para_km(km_futuro)
        else:
            previsao = analytics.prever_custo_para_km(km_futuro)
    
    return {
        "resumo_custos": resumo,
        "distribuicao_status": distribuicao,
        "modelo_regressao": modelo,
        "previsao_custo_km": previsao
    }


@app.get("/api/analytics/previsao/{km}", tags=["Analytics"])
def prever_custo_por_km(km: int, placa: Optional[str] = None):
    """Prevê o custo estimado para uma quilometragem futura."""
    if placa:
        # Analytics apenas para a moto específica
        from analytics.oficina_analytics import OficinaAnalytics
        from controle.oficina_controller import OficinaController
        
        temp_controller = OficinaController()
        checklists_filtrados = controller.get_checklists_por_moto(placa)
        for ch in checklists_filtrados:
            temp_controller._checklists.append(ch)
        
        temp_analytics = OficinaAnalytics(temp_controller)
        previsao = temp_analytics.prever_custo_para_km(km)
    else:
        previsao = analytics.prever_custo_para_km(km)
    
    if previsao is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dados insuficientes para fazer previsão. É necessário pelo menos 2 checklists."
        )
    return {"km": km, "custo_previsto": previsao}


@app.get("/api/analytics/categoria", tags=["Analytics"])
def obter_analytics_por_categoria():
    """Retorna estatísticas agrupadas por categoria de moto."""
    from modelo.categoria_moto import CategoriaMoto
    from analytics.oficina_analytics import OficinaAnalytics
    from controle.oficina_controller import OficinaController
    
    resultado = {}
    
    for categoria in CategoriaMoto:
        # Filtra motos por categoria
        motos_categoria = [m for m in controller.listar_motos() if m.categoria == categoria]
        
        if not motos_categoria:
            resultado[categoria.value] = {
                "total_motos": 0,
                "resumo_custos": {"soma": 0.0, "media": 0.0, "max": 0.0, "min": 0.0},
                "total_checklists": 0
            }
            continue
        
        # Obtém checklists dessas motos
        temp_controller = OficinaController()
        placas_categoria = {m.placa for m in motos_categoria}
        
        for ch in controller.listar_checklists():
            if normalizar_placa(ch.moto.placa) in {normalizar_placa(p) for p in placas_categoria}:
                temp_controller._checklists.append(ch)
        
        temp_analytics = OficinaAnalytics(temp_controller)
        resumo = temp_analytics.resumo_custos()
        
        resultado[categoria.value] = {
            "total_motos": len(motos_categoria),
            "resumo_custos": resumo,
            "total_checklists": len(temp_controller.listar_checklists())
        }
    
    return resultado


# ==================== HEALTH CHECK ====================

@app.get("/", tags=["Health"])
def root():
    """Endpoint raiz - health check."""
    return {
        "message": "Oficina Vital API",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/health", tags=["Health"])
def health():
    """Health check endpoint."""
    return {"status": "healthy"}

