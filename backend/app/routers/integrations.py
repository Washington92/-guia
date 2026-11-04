from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Client, Ticket, Technician, TicketAssignment, TicketEvent, WorkOrder
from ..schemas import WorkOrderCreate
from .schedule import validate_assignment

router = APIRouter(prefix="/api/integrations", tags=["Integrações"])
SECTORS = ["Facial SPA", "Catracas", "Balcão", "Rack", "Câmeras", "Som", "Sala de ginástica", "Sala de bike", "TVs", "Antenas e Wi-Fi", "Ar-condicionado", "Iluminação"]
Priority = Literal["baixa", "media", "alta", "critica"]

class ChecklistIssue(BaseModel):
    sector: str = Field(min_length=1, max_length=120)
    item: str = Field(min_length=1, max_length=180)
    observation: str = Field(default="", max_length=4000)
    priority: Priority = "media"
    photo_url: HttpUrl | None = None

class ChecklistImport(BaseModel):
    client_id: int
    checklist_name: str = Field(min_length=2, max_length=160)
    unit_name: str = Field(min_length=2, max_length=160)
    inspector_name: str = Field(min_length=2, max_length=120)
    auto_create_work_orders: bool = False
    technician_id: int | None = None
    issues: list[ChecklistIssue] = Field(min_length=1, max_length=100)

@router.get("/sectors")
def list_sectors():
    return {"sectors": SECTORS}

@router.post("/checklist-import", status_code=status.HTTP_201_CREATED)
def import_checklist(data: ChecklistImport, db: Session = Depends(get_db)):
    client = db.get(Client, data.client_id)
    if client is None:
        raise HTTPException(404, "Cliente/unidade não encontrado")
    if data.technician_id is not None and db.get(Technician, data.technician_id) is None:
        raise HTTPException(404, "Técnico não encontrado")
    created = []
    orders = []
    try:
        for issue in data.issues:
            description = f"Vistoria: {data.checklist_name} | Unidade: {data.unit_name} | Setor: {issue.sector} | Item: {issue.item} | Inspetor: {data.inspector_name}\n{issue.observation}".strip()
            if issue.photo_url:
                description += f"\nEvidência: {issue.photo_url}"
            ticket = Ticket(client_id=data.client_id, title=f"{issue.sector}: {issue.item}"[:180], description=description, priority=issue.priority)
            db.add(ticket)
            db.flush()
            if data.technician_id is not None:
                db.add(TicketAssignment(ticket_id=ticket.id, technician_id=data.technician_id))
                db.add(TicketEvent(ticket_id=ticket.id, event_type="assignment", previous_value=None, new_value=str(data.technician_id)))
            created.append(ticket)
            if data.auto_create_work_orders:
                validate_assignment(db, data.technician_id, None, 2.0)
                order = WorkOrder(client_id=data.client_id, ticket_id=ticket.id, technician_id=data.technician_id, title=f"Ação: {issue.sector} - {issue.item}"[:180], description=description, status="pendente", estimated_duration_hours=2.0, labor_cost=0, parts_cost=0, total_cost=0)
                db.add(order)
                orders.append(order)
        db.commit()
        for row in created + orders:
            db.refresh(row)
    except Exception:
        db.rollback()
        raise
    return {"created_tickets": [{"id": t.id, "title": t.title, "priority": t.priority} for t in created], "created_work_orders": [{"id": o.id, "ticket_id": o.ticket_id, "title": o.title} for o in orders]}
