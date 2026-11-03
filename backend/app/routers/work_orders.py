from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Client, Ticket, WorkOrder
from ..schemas import WorkOrderCreate, WorkOrderRead, WorkOrderUpdate

router = APIRouter(prefix="/api/work-orders", tags=["Ordens de serviço"])

@router.get("", response_model=list[WorkOrderRead])
def list_work_orders(db: Session = Depends(get_db)):
    return db.scalars(select(WorkOrder).order_by(WorkOrder.id.desc()).limit(200)).all()

@router.post("", response_model=WorkOrderRead, status_code=status.HTTP_201_CREATED)
def create_work_order(data: WorkOrderCreate, db: Session = Depends(get_db)):
    if db.get(Client, data.client_id) is None:
        raise HTTPException(404, "Cliente não encontrado")
    if data.ticket_id is not None:
        ticket = db.get(Ticket, data.ticket_id)
        if ticket is None or ticket.client_id != data.client_id:
            raise HTTPException(422, "Chamado não pertence ao cliente informado")
    order = WorkOrder(**data.model_dump())
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@router.get("/{order_id}", response_model=WorkOrderRead)
def get_work_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(WorkOrder, order_id)
    if order is None:
        raise HTTPException(404, "OS não encontrada")
    return order

@router.patch("/{order_id}", response_model=WorkOrderRead)
def update_work_order(order_id: int, data: WorkOrderUpdate, db: Session = Depends(get_db)):
    order = db.get(WorkOrder, order_id)
    if order is None:
        raise HTTPException(404, "OS não encontrada")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(order, field, value)
    db.commit()
    db.refresh(order)
    return order
