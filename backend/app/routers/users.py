"""Administração de contas: apenas administradores podem criar ou desativar usuários."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import UserAccount, UserSession
from .auth import hash_password, require_roles

router = APIRouter(prefix="/api/users", tags=["Usuários"], dependencies=[Depends(require_roles("admin"))])
ROLES = {"admin", "supervisor", "technician"}

class CreateUser(BaseModel):
    username: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9._-]+$")
    password: str = Field(min_length=12, max_length=256)
    role: str = "technician"

class UpdateUser(BaseModel):
    role: str | None = None
    active: bool | None = None

def present(user: UserAccount):
    return {"id": user.id, "username": user.username, "role": user.role, "active": bool(user.active)}

@router.get("")
def list_users(db: Session = Depends(get_db)):
    return [present(u) for u in db.scalars(select(UserAccount).order_by(UserAccount.id).limit(200)).all()]

@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(data: CreateUser, db: Session = Depends(get_db)):
    if data.role not in ROLES:
        raise HTTPException(422, "Perfil inválido")
    user = UserAccount(username=data.username.lower(), password_hash=hash_password(data.password), role=data.role)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Usuário já cadastrado")
    db.refresh(user)
    return present(user)

@router.patch("/{user_id}")
def update_user(user_id: int, data: UpdateUser, db: Session = Depends(get_db), actor: UserAccount = Depends(require_roles("admin"))):
    user = db.get(UserAccount, user_id)
    if user is None:
        raise HTTPException(404, "Usuário não encontrado")
    if data.role is not None and data.role not in ROLES:
        raise HTTPException(422, "Perfil inválido")
    if actor.id == user.id and (data.active is False or (data.role is not None and data.role != "admin")):
        raise HTTPException(409, "Não é permitido remover seu próprio acesso administrativo")
    if data.role is not None:
        user.role = data.role
    if data.active is not None:
        user.active = int(data.active)
    if not user.active:
        for session in db.scalars(select(UserSession).where(UserSession.user_id == user.id)).all():
            db.delete(session)
    db.commit()
    db.refresh(user)
    return present(user)
