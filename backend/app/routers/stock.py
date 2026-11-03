from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import StockItem, StockMovement, WorkOrder
from ..schemas import StockItemCreate, StockItemRead, StockMovementCreate, StockMovementRead

router = APIRouter(prefix="/api/stock", tags=["Estoque"])

@router.get("/items", response_model=list[StockItemRead])
def list_items(db: Session = Depends(get_db)):
    return db.scalars(select(StockItem).order_by(StockItem.name).limit(500)).all()

@router.post("/items", response_model=StockItemRead, status_code=status.HTTP_201_CREATED)
def create_item(data: StockItemCreate, db: Session = Depends(get_db)):
    item = StockItem(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.get("/movements", response_model=list[StockMovementRead])
def list_movements(db: Session = Depends(get_db)):
    return db.scalars(select(StockMovement).order_by(StockMovement.id.desc()).limit(500)).all()

@router.post("/movements", response_model=StockMovementRead, status_code=status.HTTP_201_CREATED)
def move_stock(data: StockMovementCreate, db: Session = Depends(get_db)):
    item = db.get(StockItem, data.item_id)
    if item is None:
        raise HTTPException(404, "Material não encontrado")
    if data.work_order_id is not None and db.get(WorkOrder, data.work_order_id) is None:
        raise HTTPException(404, "OS não encontrada")
    delta = data.quantity if data.type == "entrada" else -data.quantity
    stmt = update(StockItem).where(StockItem.id == data.item_id)
    if delta < 0:
        stmt = stmt.where(StockItem.quantity >= data.quantity)
    result = db.execute(stmt.values(quantity=StockItem.quantity + delta))
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Estoque insuficiente")
    movement = StockMovement(**data.model_dump())
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement
