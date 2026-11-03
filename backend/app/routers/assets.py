from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Asset, Client
from ..schemas import AssetCreate, AssetRead, AssetUpdate

router = APIRouter(prefix="/api/assets", tags=["Ativos de infraestrutura"])

@router.get("", response_model=list[AssetRead])
def list_assets(client_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(Asset)
    if client_id is not None:
        stmt = stmt.where(Asset.client_id == client_id)
    return db.scalars(stmt.order_by(Asset.id.desc()).limit(200)).all()

@router.post("", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def create_asset(data: AssetCreate, db: Session = Depends(get_db)):
    if db.get(Client, data.client_id) is None:
        raise HTTPException(404, "Cliente não encontrado")
    asset = Asset(**data.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset

@router.patch("/{asset_id}", response_model=AssetRead)
def update_asset(asset_id: int, data: AssetUpdate, db: Session = Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(404, "Ativo não encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(asset, field, value)
    db.commit()
    db.refresh(asset)
    return asset

@router.get("/{asset_id}", response_model=AssetRead)
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(404, "Ativo não encontrado")
    return asset
