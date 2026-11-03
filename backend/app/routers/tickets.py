from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Client, Ticket
from ..schemas import TicketCreate, TicketRead, TicketUpdate

router = APIRouter(prefix="/api/tickets", tags=["Chamados"])

@router.get("", response_model=list[TicketRead])
def list_tickets(db: Session = Depends(get_db)):
    return db.scalars(select(Ticket).order_by(Ticket.id.desc()).limit(200)).all()

@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket(data: TicketCreate, db: Session = Depends(get_db)):
    if db.get(Client, data.client_id) is None:
        raise HTTPException(404, "Cliente não encontrado")
    ticket = Ticket(**data.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

@router.patch("/{ticket_id}", response_model=TicketRead)
def update_ticket(ticket_id: int, data: TicketUpdate, db: Session = Depends(get_db)):
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(404, "Chamado não encontrado")
    ticket.status = data.status
    db.commit()
    db.refresh(ticket)
    return ticket
