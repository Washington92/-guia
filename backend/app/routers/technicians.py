from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Technician, Ticket, TicketAssignment, TicketEvent
from ..schemas import TechnicianCreate, TechnicianRead, TicketAssignmentCreate, TicketAssignmentRead

router = APIRouter(prefix="/api/technicians", tags=["Técnicos"])

@router.get("", response_model=list[TechnicianRead])
def list_technicians(db: Session = Depends(get_db)):
    return db.scalars(select(Technician).order_by(Technician.name).limit(200)).all()

@router.post("", response_model=TechnicianRead, status_code=status.HTTP_201_CREATED)
def create_technician(data: TechnicianCreate, db: Session = Depends(get_db)):
    technician = Technician(**data.model_dump())
    db.add(technician)
    db.commit()
    db.refresh(technician)
    return technician

assignments = APIRouter(prefix="/api/tickets", tags=["Responsáveis"])

@assignments.get("/assignments", response_model=list[TicketAssignmentRead])
def list_assignments(db: Session = Depends(get_db)):
    return db.scalars(select(TicketAssignment).order_by(TicketAssignment.ticket_id).limit(200)).all()

@assignments.put("/{ticket_id}/assignment", response_model=TicketAssignmentRead)
def assign_ticket(ticket_id: int, data: TicketAssignmentCreate, db: Session = Depends(get_db)):
    if db.get(Ticket, ticket_id) is None:
        raise HTTPException(404, "Chamado não encontrado")
    technician = db.get(Technician, data.technician_id)
    if technician is None or not technician.active:
        raise HTTPException(404, "Técnico ativo não encontrado")
    assignment = db.scalar(select(TicketAssignment).where(TicketAssignment.ticket_id == ticket_id))
    old_id = assignment.technician_id if assignment else None
    if assignment is None:
        assignment = TicketAssignment(ticket_id=ticket_id, technician_id=data.technician_id)
        db.add(assignment)
    elif assignment.technician_id != data.technician_id:
        assignment.technician_id = data.technician_id
    if old_id != data.technician_id:
        db.add(TicketEvent(ticket_id=ticket_id, event_type="assignment", previous_value=str(old_id) if old_id else None, new_value=str(data.technician_id)))
    db.commit()
    db.refresh(assignment)
    return assignment
