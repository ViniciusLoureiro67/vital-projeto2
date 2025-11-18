# db/models.py
"""
Modelos de banco de dados usando SQLAlchemy ORM.
"""
from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import date
import enum

from database import Base
from modelo.categoria_moto import CategoriaMoto
from modelo.checklist_item import StatusItem


class MotoDB(Base):
    """Modelo de banco de dados para Moto."""
    __tablename__ = "motos"
    
    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String(8), unique=True, index=True, nullable=False)
    marca = Column(String(100), nullable=False)
    modelo = Column(String(100), nullable=False)
    ano = Column(Integer, nullable=False)
    cilindradas = Column(Integer, nullable=False)
    categoria = Column(String(50), nullable=False)  # Armazena o value do enum
    
    # Relacionamento com checklists
    checklists = relationship("ChecklistDB", back_populates="moto", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MotoDB(id={self.id}, placa={self.placa}, modelo={self.modelo})>"


class ChecklistDB(Base):
    """Modelo de banco de dados para Checklist."""
    __tablename__ = "checklists"
    
    id = Column(Integer, primary_key=True, index=True)
    moto_id = Column(Integer, ForeignKey("motos.id"), nullable=False)
    km_atual = Column(Integer, nullable=False)
    data_revisao = Column(Date, nullable=False, default=date.today)
    finalizado = Column(Boolean, default=False, nullable=False)
    pago = Column(Boolean, default=False, nullable=False)
    custo_real = Column(Float, nullable=True)  # Custo real da revisão (opcional)
    
    # Relacionamentos
    moto = relationship("MotoDB", back_populates="checklists")
    itens = relationship("ChecklistItemDB", back_populates="checklist", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChecklistDB(id={self.id}, moto_id={self.moto_id}, km={self.km_atual})>"


class ChecklistItemDB(Base):
    """Modelo de banco de dados para ChecklistItem."""
    __tablename__ = "checklist_itens"
    
    id = Column(Integer, primary_key=True, index=True)
    checklist_id = Column(Integer, ForeignKey("checklists.id"), nullable=False)
    nome = Column(String(200), nullable=False)
    categoria = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)  # Armazena o value do enum
    custo_estimado = Column(Float, default=0.0, nullable=False)
    
    # Relacionamento
    checklist = relationship("ChecklistDB", back_populates="itens")
    
    def __repr__(self):
        return f"<ChecklistItemDB(id={self.id}, nome={self.nome}, status={self.status})>"


class UsuarioDB(Base):
    """Modelo de banco de dados para Usuário (autenticação)."""
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(String(10), default="true", nullable=False)
    is_admin = Column(String(10), default="false", nullable=False)
    
    def __repr__(self):
        return f"<UsuarioDB(id={self.id}, username={self.username})>"

