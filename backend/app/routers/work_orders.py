from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Client, StockItem, Ticket, WorkOrder, WorkOrderItem
from ..schemas import (
    WorkOrderCreate,
    WorkOrderItemCreate,
    WorkOrderItemRead,
    WorkOrderRead,
    WorkOrderUpdate,
)

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

    items_data = data.items
    payload = data.model_dump(exclude={"items"})
    order = WorkOrder(**payload)

    parts_cost = 0.0
    for it in items_data:
        if it.stock_item_id is not None:
            stock = db.get(StockItem, it.stock_item_id)
            if stock is None:
                raise HTTPException(404, f"Item de estoque {it.stock_item_id} não encontrado")
        t_price = round(it.quantity * it.unit_price, 2)
        parts_cost += t_price
        order.items.append(WorkOrderItem(
            stock_item_id=it.stock_item_id,
            description=it.description,
            quantity=it.quantity,
            unit_price=it.unit_price,
            total_price=t_price,
        ))

    order.parts_cost = round(parts_cost, 2)
    order.total_cost = round(order.labor_cost + order.parts_cost, 2)

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
    for field, value in data.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(order, field, value)
    if data.labor_cost is not None:
        order.total_cost = round(order.labor_cost + order.parts_cost, 2)
    db.commit()
    db.refresh(order)
    return order

@router.post("/{order_id}/items", response_model=WorkOrderItemRead, status_code=status.HTTP_201_CREATED)
def add_work_order_item(order_id: int, data: WorkOrderItemCreate, db: Session = Depends(get_db)):
    order = db.get(WorkOrder, order_id)
    if order is None:
        raise HTTPException(404, "OS não encontrada")
    if data.stock_item_id is not None:
        stock = db.get(StockItem, data.stock_item_id)
        if stock is None:
            raise HTTPException(404, f"Item de estoque {data.stock_item_id} não encontrado")

    total_price = round(data.quantity * data.unit_price, 2)
    item = WorkOrderItem(
        work_order_id=order.id,
        stock_item_id=data.stock_item_id,
        description=data.description,
        quantity=data.quantity,
        unit_price=data.unit_price,
        total_price=total_price,
    )
    db.add(item)
    order.parts_cost = round(order.parts_cost + total_price, 2)
    order.total_cost = round(order.labor_cost + order.parts_cost, 2)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{order_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_work_order_item(order_id: int, item_id: int, db: Session = Depends(get_db)):
    order = db.get(WorkOrder, order_id)
    if order is None:
        raise HTTPException(404, "OS não encontrada")
    item = db.get(WorkOrderItem, item_id)
    if item is None or item.work_order_id != order.id:
        raise HTTPException(404, "Item de OS não encontrado")

    order.parts_cost = max(0.0, round(order.parts_cost - item.total_price, 2))
    order.total_cost = max(0.0, round(order.labor_cost + order.parts_cost, 2))
    db.delete(item)
    db.commit()
