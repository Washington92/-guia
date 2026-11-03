from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Client, Ticket, WorkOrder, Asset, StockItem

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    return {
        "clients": db.scalar(select(func.count(Client.id))) or 0,
        "tickets": db.scalar(select(func.count(Ticket.id))) or 0,
        "tickets_open": db.scalar(select(func.count(Ticket.id)).where(Ticket.status == "aberto")) or 0,
        "tickets_in_progress": db.scalar(select(func.count(Ticket.id)).where(Ticket.status == "em_andamento")) or 0,
        "stock_items": db.scalar(select(func.count(StockItem.id))) or 0,
        "low_stock_items": db.scalar(select(func.count(StockItem.id)).where(StockItem.quantity <= StockItem.min_quantity)) or 0,
        "assets": db.scalar(select(func.count(Asset.id))) or 0,
        "work_orders": db.scalar(select(func.count(WorkOrder.id))) or 0,
        "work_orders_pending": db.scalar(select(func.count(WorkOrder.id)).where(WorkOrder.status == "pendente")) or 0,
    }
