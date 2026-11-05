from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Client, Ticket, TicketNote, TicketEvent
from ..schemas import TicketCreate, TicketRead, TicketUpdate, TicketNoteCreate, TicketNoteRead

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
    if ticket.status != data.status:
        db.add(TicketEvent(ticket_id=ticket.id, event_type='status', previous_value=ticket.status, new_value=data.status))
        ticket.status = data.status
    db.commit()
    db.refresh(ticket)
    return ticket

@router.get("/{ticket_id}/notes", response_model=list[TicketNoteRead])
def list_ticket_notes(ticket_id: int, db: Session = Depends(get_db)):
    if db.get(Ticket, ticket_id) is None:
        raise HTTPException(404, "Chamado não encontrado")
    return db.scalars(select(TicketNote).where(TicketNote.ticket_id == ticket_id).order_by(TicketNote.id.desc()).limit(200)).all()

@router.post("/{ticket_id}/notes", response_model=TicketNoteRead, status_code=status.HTTP_201_CREATED)
def add_ticket_note(ticket_id: int, data: TicketNoteCreate, db: Session = Depends(get_db)):
    if db.get(Ticket, ticket_id) is None:
        raise HTTPException(404, "Chamado não encontrado")
    note = TicketNote(ticket_id=ticket_id, **data.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note

@router.get("/{ticket_id}/events")
def list_ticket_events(ticket_id: int, db: Session = Depends(get_db)):
    if db.get(Ticket, ticket_id) is None:
        raise HTTPException(404, "Chamado não encontrado")
    events = db.scalars(select(TicketEvent).where(TicketEvent.ticket_id == ticket_id).order_by(TicketEvent.id.desc()).limit(200)).all()
    return [{"id": e.id, "ticket_id": e.ticket_id, "event_type": e.event_type, "previous_value": e.previous_value, "new_value": e.new_value, "created_at": e.created_at} for e in events]
