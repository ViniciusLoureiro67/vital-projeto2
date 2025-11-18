# api/schemas.py
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from modelo.categoria_moto import CategoriaMoto
from modelo.checklist_item import StatusItem


class MotoCreate(BaseModel):
    """Schema para criação de moto."""
    placa: str = Field(..., min_length=6, max_length=8, description="Placa da moto")
    marca: str = Field(..., min_length=1, description="Marca da moto")
    modelo: str = Field(..., min_length=1, description="Modelo da moto")
    ano: int = Field(..., ge=1900, le=2100, description="Ano da moto")
    cilindradas: int = Field(..., gt=0, description="Cilindradas em cc")
    categoria: str = Field(..., description="Categoria da moto")

    @validator('categoria')
    def validate_categoria(cls, v):
        try:
            return CategoriaMoto[v].value
        except KeyError:
            try:
                # Tenta pelo value
                for cat in CategoriaMoto:
                    if cat.value.lower() == v.lower():
                        return cat.value
                raise ValueError(f"Categoria inválida. Opções: {[c.name for c in CategoriaMoto]}")
            except:
                raise ValueError(f"Categoria inválida. Opções: {[c.name for c in CategoriaMoto]}")


class MotoUpdate(BaseModel):
    """Schema para atualização de moto (todos os campos opcionais)."""
    marca: Optional[str] = Field(None, min_length=1)
    modelo: Optional[str] = Field(None, min_length=1)
    ano: Optional[int] = Field(None, ge=1900, le=2100)
    cilindradas: Optional[int] = Field(None, gt=0)
    categoria: Optional[str] = None

    @validator('categoria')
    def validate_categoria(cls, v):
        if v is None:
            return v
        try:
            return CategoriaMoto[v].value
        except KeyError:
            try:
                for cat in CategoriaMoto:
                    if cat.value.lower() == v.lower():
                        return cat.value
                raise ValueError(f"Categoria inválida")
            except:
                raise ValueError(f"Categoria inválida")


class MotoResponse(BaseModel):
    """Schema de resposta para moto."""
    id: Optional[int] = None
    placa: str
    marca: str
    modelo: str
    ano: int
    cilindradas: int
    categoria: str
    categoria_enum: str

    class Config:
        from_attributes = True


class ChecklistItemCreate(BaseModel):
    """Schema para criação de item de checklist."""
    nome: str = Field(..., min_length=1)
    categoria: str = Field(default="Geral", min_length=1)
    status: Optional[str] = Field(default="pendente")
    custo_estimado: Optional[float] = Field(default=0.0, ge=0.0)

    @validator('status')
    def validate_status(cls, v):
        if v is None:
            return "pendente"
        try:
            # Tenta pelo nome do enum
            return StatusItem[v.upper()].value
        except KeyError:
            try:
                # Tenta pelo value
                for s in StatusItem:
                    if s.value.lower() == v.lower():
                        return s.value
                # Se não encontrou, retorna pendente como padrão
                return "pendente"
            except:
                return "pendente"


class ChecklistItemUpdate(BaseModel):
    """Schema para atualização de item de checklist."""
    nome: Optional[str] = Field(None, min_length=1)
    categoria: Optional[str] = Field(None, min_length=1)
    status: Optional[str] = None
    custo_estimado: Optional[float] = Field(None, ge=0.0)

    @validator('status')
    def validate_status(cls, v):
        if v is None:
            return v
        try:
            return StatusItem[v.upper()].value
        except KeyError:
            try:
                for s in StatusItem:
                    if s.value.lower() == v.lower():
                        return s.value
                raise ValueError(f"Status inválido")
            except:
                raise ValueError(f"Status inválido")


class ChecklistItemResponse(BaseModel):
    """Schema de resposta para item de checklist."""
    id: Optional[int] = None
    nome: str
    categoria: str
    status: str
    status_enum: str
    custo_estimado: float

    class Config:
        from_attributes = True


class ChecklistCreate(BaseModel):
    """Schema para criação de checklist."""
    placa_moto: str = Field(..., min_length=6, max_length=8)
    km_atual: int = Field(..., ge=0)
    data_revisao: Optional[date] = None
    itens: Optional[List[ChecklistItemCreate]] = None


class ChecklistUpdate(BaseModel):
    """Schema para atualização de checklist."""
    km_atual: Optional[int] = Field(None, ge=0)
    data_revisao: Optional[date] = None


class ChecklistResponse(BaseModel):
    """Schema de resposta para checklist."""
    id: Optional[int] = None
    moto: MotoResponse
    km_atual: int
    data_revisao: str
    data_formatada: str
    finalizado: bool = False
    pago: bool = False
    custo_real: Optional[float] = None
    itens: List[ChecklistItemResponse]
    total_concluido: int
    total_pendente: int
    total_necessita_troca: int
    total_ignorado: int = 0
    custo_total_estimado: float

    class Config:
        from_attributes = True


class AnalyticsResponse(BaseModel):
    """Schema de resposta para analytics."""
    resumo_custos: dict
    resumo_custos_reais: Optional[dict] = None
    distribuicao_status: dict
    modelo_regressao: Optional[dict] = None
    previsao_custo_km: Optional[float] = None
    dados_historicos: Optional[dict] = None

