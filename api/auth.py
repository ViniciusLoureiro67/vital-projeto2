# api/auth.py
"""
Endpoints de autenticação.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from database import get_db
from db.repository import UsuarioRepository
from auth.security import verify_password, get_password_hash, create_access_token
from auth.dependencies import get_current_user, get_current_active_user
from db.models import UsuarioDB

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class UserCreate(BaseModel):
    """Schema para criação de usuário."""
    username: str
    email: EmailStr
    password: str
    is_admin: bool = False


class UserResponse(BaseModel):
    """Schema de resposta para usuário."""
    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema de resposta para token."""
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Registra um novo usuário."""
    # Verifica se username já existe
    if UsuarioRepository.buscar_por_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username já está em uso"
        )
    
    # Verifica se email já existe
    if UsuarioRepository.buscar_por_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já está em uso"
        )
    
    # Cria usuário
    hashed_password = get_password_hash(user_data.password)
    usuario = UsuarioRepository.criar(
        db,
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_admin=user_data.is_admin
    )
    
    return usuario


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Endpoint de login. Retorna token JWT.
    """
    user = UsuarioRepository.buscar_por_username(db, form_data.username)
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.is_active != "true":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: UsuarioDB = Depends(get_current_active_user)):
    """Retorna informações do usuário atual."""
    return current_user

