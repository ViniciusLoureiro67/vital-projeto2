# api/main_db.py
"""
API FastAPI com suporte a PostgreSQL, autenticação e logging.
"""
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session

from database import get_db, init_db
from controle.oficina_controller_db import OficinaControllerDB
from controle.excecoes import (
    MotoNaoEncontradaError,
    ChecklistNaoEncontradoError,
    ValidacaoError
)
from controle.validadores import normalizar_placa, validar_placa_brasileira
from analytics.oficina_analytics import OficinaAnalytics
from modelo.moto import Moto
from modelo.categoria_moto import CategoriaMoto
from modelo.checklist import Checklist
from modelo.checklist_item import StatusItem
from modelo.checklist_templates import criar_checklist_padrao, criar_checklist_adaptativo
from api.schemas import (
    MotoCreate, MotoUpdate, MotoResponse,
    ChecklistCreate, ChecklistUpdate, ChecklistResponse,
    ChecklistItemCreate, ChecklistItemResponse,
    AnalyticsResponse
)
from api.auth import router as auth_router
from auth.dependencies import get_current_active_user, get_current_admin_user
from db.models import UsuarioDB
from utils.logger import logger

# Inicializa banco de dados
init_db()

app = FastAPI(
    title="Oficina Vital API",
    description="API REST para gerenciamento de oficina de motos com PostgreSQL",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui rotas de autenticação
app.include_router(auth_router)


# Dependency para obter controller com sessão do banco
def get_controller(db: Session = Depends(get_db)) -> OficinaControllerDB:
    """Retorna uma instância do controller com sessão do banco."""
    return OficinaControllerDB(db)


# Dependency para analytics
def get_analytics(controller: OficinaControllerDB = Depends(get_controller)) -> OficinaAnalytics:
    """Retorna instância de analytics."""
    return OficinaAnalytics(controller)


# ==================== ENDPOINTS DE MOTOS ====================

@app.get("/api/motos", response_model=List[MotoResponse], tags=["Motos"])
def listar_motos(
    skip: int = 0,
    limit: Optional[int] = None,
    ordenar_por: Optional[str] = None,
    controller: OficinaControllerDB = Depends(get_controller),
    current_user: UsuarioDB = Depends(get_current_active_user)
):
    """Lista todas as motos cadastradas com paginação e ordenação."""
    logger.info(f"Listando motos - usuário: {current_user.username}")
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
def buscar_moto_por_placa(
    placa: str,
    controller: OficinaControllerDB = Depends(get_controller),
    current_user: UsuarioDB = Depends(get_current_active_user)
):
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
def buscar_motos_por_modelo(
    termo: str,
    controller: OficinaControllerDB = Depends(get_controller),
    current_user: UsuarioDB = Depends(get_current_active_user)
):
    """Busca motos por modelo (busca parcial, case-insensitive)."""
    motos = controller.buscar_motos_por_modelo(termo)
    return [m.to_dict() for m in motos]


@app.post("/api/motos", response_model=MotoResponse, status_code=status.HTTP_201_CREATED, tags=["Motos"])
def cadastrar_moto(
    moto_data: MotoCreate,
    controller: OficinaControllerDB = Depends(get_controller),
    current_user: UsuarioDB = Depends(get_current_active_user)
):
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
        logger.info(f"Moto cadastrada: {moto.placa} - usuário: {current_user.username}")
        return moto.to_dict()
    except (ValueError, ValidacaoError) as e:
        logger.error(f"Erro ao cadastrar moto: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.put("/api/motos/{placa}", response_model=MotoResponse, tags=["Motos"])
def atualizar_moto(
    placa: str,
    moto_data: MotoUpdate,
    controller: OficinaControllerDB = Depends(get_controller),
    current_user: UsuarioDB = Depends(get_current_active_user)
):
    """Atualiza os dados de uma moto existente."""
    try:
        moto_atualizada = controller.atualizar_moto(
            placa,
            marca=moto_data.marca,
            modelo=moto_data.modelo,
            ano=moto_data.ano,
            cilindradas=moto_data.cilindradas,
            categoria=moto_data.categoria
        )
        
        if moto_atualizada is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Moto com placa {placa} não encontrada."
            )
        
        logger.info(f"Moto atualizada: {placa} - usuário: {current_user.username}")
        return moto_atualizada.to_dict()
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
def deletar_moto(
    placa: str,
    controller: OficinaControllerDB = Depends(get_controller),
    current_user: UsuarioDB = Depends(get_current_admin_user)
):
    """Remove uma moto do sistema (apenas admin)."""
    sucesso = controller.deletar_moto(placa)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Moto com placa {placa} não encontrada."
        )
    logger.info(f"Moto deletada: {placa} - usuário: {current_user.username}")
    return None


# ==================== ENDPOINTS DE CHECKLISTS ====================

@app.get("/api/checklists", response_model=List[ChecklistResponse], tags=["Checklists"])
def listar_checklists(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    status_item: Optional[str] = None,
    placa: Optional[str] = None,
    finalizado: Optional[bool] = None,
    pago: Optional[bool] = None,
    skip: int = 0,
    limit: Optional[int] = None,
    ordenar_por: Optional[str] = None,
    controller: OficinaControllerDB = Depends(get_controller),
    current_user: UsuarioDB = Depends(get_current_active_user)
):
    """Lista checklists com filtros opcionais, paginação e ordenação."""
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
        checklists = controller.listar_checklists(finalizado=finalizado, pago=pago)
    
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
def listar_checklists_por_moto(
    placa: str,
    controller: OficinaControllerDB = Depends(get_controller),
    current_user: UsuarioDB = Depends(get_current_active_user)
):
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
def criar_checklist(
    checklist_data: ChecklistCreate,
    controller: OficinaControllerDB = Depends(get_controller),
    current_user: UsuarioDB = Depends(get_current_active_user)
):
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

        checklist_id = controller.registrar_checklist(checklist)
        logger.info(f"Checklist criado: ID {checklist_id} - usuário: {current_user.username}")
        return controller.buscar_checklist_por_id(checklist_id).to_dict()
    except ValueError as e:
        logger.error(f"Erro ao criar checklist: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/api/checklists/{checklist_id}", response_model=ChecklistResponse, tags=["Checklists"])
def buscar_checklist_por_id(
    checklist_id: int,
    controller: OficinaControllerDB = Depends(get_controller),
    current_user: UsuarioDB = Depends(get_current_active_user)
):
    """Busca um checklist pelo ID único."""
    checklist = controller.buscar_checklist_por_id(checklist_id)
    if not checklist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checklist com ID {checklist_id} não encontrado."
        )
    return checklist.to_dict()


@app.put("/api/checklists/{checklist_id}/status", response_model=ChecklistResponse, tags=["Checklists"])
def atualizar_status_checklist(
    checklist_id: int,
    finalizado: Optional[bool] = None,
    pago: Optional[bool] = None,
    custo_real: Optional[float] = None,
    controller: OficinaControllerDB = Depends(get_controller),
    current_user: UsuarioDB = Depends(get_current_active_user)
):
    """Atualiza o status de finalização, pagamento e/ou custo real de um checklist."""
    # Converte string "true"/"false" para boolean se necessário
    if isinstance(finalizado, str):
        finalizado = finalizado.lower() == 'true'
    if isinstance(pago, str):
        pago = pago.lower() == 'true'
    if isinstance(custo_real, str):
        try:
            custo_real = float(custo_real) if custo_real else None
        except ValueError:
            custo_real = None
    
    checklist = controller.atualizar_status_checklist(
        checklist_id=checklist_id,
        finalizado=finalizado,
        pago=pago,
        custo_real=custo_real
    )
    if not checklist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checklist com ID {checklist_id} não encontrado."
        )
    return checklist.to_dict()


@app.put("/api/checklists/{checklist_id}/itens/{item_index}", response_model=ChecklistResponse, tags=["Checklists"])
def atualizar_item_checklist(
    checklist_id: int,
    item_index: int,
    status: Optional[str] = None,
    custo_estimado: Optional[float] = None,
    controller: OficinaControllerDB = Depends(get_controller),
    current_user: UsuarioDB = Depends(get_current_active_user)
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
def deletar_checklist(
    checklist_id: int,
    controller: OficinaControllerDB = Depends(get_controller),
    current_user: UsuarioDB = Depends(get_current_admin_user)
):
    """Remove um checklist do sistema (apenas admin)."""
    sucesso = controller.deletar_checklist_por_id(checklist_id)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checklist com ID {checklist_id} não encontrado."
        )
    logger.info(f"Checklist deletado: ID {checklist_id} - usuário: {current_user.username}")
    return None


# ==================== ENDPOINTS DE ANALYTICS ====================

@app.get("/api/analytics", response_model=AnalyticsResponse, tags=["Analytics"])
def obter_analytics(
    km_futuro: Optional[int] = None,
    placa: Optional[str] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    analytics: OficinaAnalytics = Depends(get_analytics),
    current_user: UsuarioDB = Depends(get_current_active_user)
):
    """Retorna análises estatísticas dos dados da oficina."""
    # Analytics já usa o controller que filtra do banco
    resumo = analytics.resumo_custos()
    distribuicao = analytics.distribuicao_status_itens()
    modelo = analytics.estimar_custo_por_km()
    
    previsao = None
    if km_futuro is not None and modelo is not None:
        previsao = analytics.prever_custo_para_km(km_futuro)
    
    resumo_custos_reais = analytics.resumo_custos_reais()
    dados_historicos = analytics.dados_historicos_graficos()
    
    return {
        "resumo_custos": resumo,
        "resumo_custos_reais": resumo_custos_reais,
        "distribuicao_status": distribuicao,
        "modelo_regressao": modelo,
        "previsao_custo_km": previsao,
        "dados_historicos": dados_historicos
    }


@app.get("/api/analytics/categoria", tags=["Analytics"])
def obter_analytics_por_categoria(
    controller: OficinaControllerDB = Depends(get_controller),
    current_user: UsuarioDB = Depends(get_current_active_user)
):
    """Retorna estatísticas agrupadas por categoria de moto."""
    from modelo.categoria_moto import CategoriaMoto
    from analytics.oficina_analytics import OficinaAnalytics
    
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
        temp_controller = controller  # Reutiliza o mesmo controller
        placas_categoria = {m.placa for m in motos_categoria}
        
        checklists_categoria = []
        for placa in placas_categoria:
            checklists_categoria.extend(controller.get_checklists_por_moto(placa))
        
        # Cria analytics temporário usando controller em memória
        from controle.oficina_controller import OficinaController
        temp_controller_mem = OficinaController()
        # Adiciona checklists ao controller temporário
        for ch in checklists_categoria:
            temp_controller_mem._checklists.append(ch)
            # Atribui IDs temporários se necessário
            if ch.id is None:
                ch._id = len(temp_controller_mem._checklists)
        
        temp_analytics = OficinaAnalytics(temp_controller_mem)
        resumo = temp_analytics.resumo_custos()
        
        resultado[categoria.value] = {
            "total_motos": len(motos_categoria),
            "resumo_custos": resumo,
            "total_checklists": len(checklists_categoria)
        }
    
    return resultado


@app.get("/api/financeiro", tags=["Financeiro"])
def obter_relatorio_financeiro(
    tipo_periodo: Optional[str] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    data_referencia: Optional[date] = None,
    analytics: OficinaAnalytics = Depends(get_analytics),
    current_user: UsuarioDB = Depends(get_current_active_user)
):
    """
    Retorna relatório financeiro para um período específico.
    
    Parâmetros:
    - tipo_periodo: 'dia', 'semana', 'mes' ou 'ano' (opcional)
    - data_inicio: Data inicial (opcional, se tipo_periodo não for informado)
    - data_fim: Data final (opcional, se tipo_periodo não for informado)
    - data_referencia: Data de referência para tipo_periodo (padrão: hoje)
    """
    if tipo_periodo:
        if data_referencia is None:
            data_referencia = date.today()
        relatorio = analytics.relatorio_financeiro_por_periodo(
            tipo_periodo=tipo_periodo,
            data_referencia=data_referencia
        )
    else:
        relatorio = analytics.relatorio_financeiro(
            data_inicio=data_inicio,
            data_fim=data_fim
        )
    
    logger.info(f"Relatório financeiro gerado - usuário: {current_user.username}")
    return relatorio


# ==================== HEALTH CHECK ====================

@app.get("/", tags=["Health"])
def root():
    """Endpoint raiz - health check."""
    return {
        "message": "Oficina Vital API",
        "version": "2.0.0",
        "status": "online",
        "database": "PostgreSQL"
    }


@app.get("/health", tags=["Health"])
def health(db: Session = Depends(get_db)):
    """Health check endpoint com verificação de banco."""
    try:
        # Testa conexão com banco
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Erro de conexão com banco: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )

