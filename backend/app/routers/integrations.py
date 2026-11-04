from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Client, Ticket, Technician, TicketAssignment, TicketEvent, WorkOrder
from .schedule import validate_assignment

router = APIRouter(prefix="/api/integrations", tags=["Integrações"])
SECTORS = [
    "Facial SPA", "Catracas", "Balcão", "Rack", "Câmeras", "Som",
    "Sala de ginástica", "Sala de bike", "TVs", "Antenas e Wi-Fi",
    "Ar-condicionado", "Iluminação"
]
Priority = Literal["baixa", "media", "alta", "critica"]

SMARTFIT_TEMPLATE_ITEMS = [
    {"sector": "Facial SPA", "item": "Validador biométrico / câmera facial", "standard_priority": "alta"},
    {"sector": "Catracas", "item": "Placa controladora e leitores de acesso", "standard_priority": "alta"},
    {"sector": "Balcão", "item": "Computadores de atendimento e impressoras", "standard_priority": "media"},
    {"sector": "Rack", "item": "Patch panel, nobreak e switches gigabit", "standard_priority": "critica"},
    {"sector": "Câmeras", "item": "CFTV e gravação NVR em nuvem/local", "standard_priority": "alta"},
    {"sector": "Som", "item": "Amplificador e zonas de áudio da musculação", "standard_priority": "media"},
    {"sector": "Sala de ginástica", "item": "Microfone sem fio e caixas ativas", "standard_priority": "media"},
    {"sector": "Sala de bike", "item": "Iluminação cênica e sonorização", "standard_priority": "media"},
    {"sector": "TVs", "item": "Receptores HDMI e telas do salão", "standard_priority": "baixa"},
    {"sector": "Antenas e Wi-Fi", "item": "Access points clientes e colaboradores", "standard_priority": "alta"},
    {"sector": "Ar-condicionado", "item": "Automação e termostatos de ambiente", "standard_priority": "media"},
    {"sector": "Iluminação", "item": "Painéis LED e contatores elétricos", "standard_priority": "media"}
]

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

class BatchChecklistItem(BaseModel):
    sector: str = Field(min_length=1, max_length=120)
    item: str = Field(min_length=1, max_length=180)
    observation: str = Field(default="", max_length=4000)
    priority: Priority = "media"
    photo_url: HttpUrl | None = None
    approved: bool = True
    create_work_order: bool = False
    technician_id: int | None = None
    scheduled_at: datetime | None = None
    estimated_duration_hours: float = Field(default=2.0, ge=0.25, le=24.0)

class BatchChecklistImport(BaseModel):
    client_id: int
    checklist_name: str = Field(min_length=2, max_length=160)
    unit_name: str = Field(min_length=2, max_length=160)
    inspector_name: str = Field(min_length=2, max_length=120)
    items: list[BatchChecklistItem] = Field(min_length=1, max_length=100)

@router.get("/sectors")
def list_sectors():
    return {"sectors": SECTORS}

@router.get("/template/smartfit")
def smartfit_template():
    return {
        "name": "Checklist Padrão Unidades",
        "description": "Template setorial de infraestrutura e TI para academias e unidades de rede",
        "sectors": SECTORS,
        "suggested_items": SMARTFIT_TEMPLATE_ITEMS
    }

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

@router.post("/checklist-batch", status_code=status.HTTP_201_CREATED)
def import_checklist_batch(data: BatchChecklistImport, db: Session = Depends(get_db)):
    client = db.get(Client, data.client_id)
    if client is None:
        raise HTTPException(404, "Cliente/unidade não encontrado")

    created_tickets = []
    created_orders = []
    discarded_items = []

    try:
        for item in data.items:
            if not item.approved:
                discarded_items.append({"sector": item.sector, "item": item.item, "reason": "Conforme ou rejeitado na triagem"})
                continue

            if item.technician_id is not None and db.get(Technician, item.technician_id) is None:
                raise HTTPException(404, f"Técnico ID {item.technician_id} não encontrado")

            desc_lines = [
                f"Vistoria: {data.checklist_name}",
                f"Unidade: {data.unit_name}",
                f"Setor: {item.sector}",
                f"Item: {item.item}",
                f"Inspetor: {data.inspector_name}"
            ]
            if item.observation:
                desc_lines.append(f"Observações: {item.observation}")
            if item.photo_url:
                desc_lines.append(f"Evidência fotográfica: {item.photo_url}")
            description = "\n".join(desc_lines)

            ticket = Ticket(
                client_id=data.client_id,
                title=f"{item.sector}: {item.item}"[:180],
                description=description,
                priority=item.priority
            )
            db.add(ticket)
            db.flush()

            if item.technician_id is not None:
                db.add(TicketAssignment(ticket_id=ticket.id, technician_id=item.technician_id))
                db.add(TicketEvent(ticket_id=ticket.id, event_type="assignment", previous_value=None, new_value=str(item.technician_id)))

            created_tickets.append(ticket)

            if item.create_work_order:
                validate_assignment(db, item.technician_id, item.scheduled_at, item.estimated_duration_hours)
                order = WorkOrder(
                    client_id=data.client_id,
                    ticket_id=ticket.id,
                    technician_id=item.technician_id,
                    scheduled_at=item.scheduled_at,
                    estimated_duration_hours=item.estimated_duration_hours,
                    title=f"OS Preventiva/Corretiva: {item.sector} - {item.item}"[:180],
                    description=description,
                    status="pendente",
                    labor_cost=0,
                    parts_cost=0,
                    total_cost=0
                )
                db.add(order)
                created_orders.append(order)

        db.commit()
        for t in created_tickets:
            db.refresh(t)
        for o in created_orders:
            db.refresh(o)

    except Exception:
        db.rollback()
        raise

    return {
        "summary": {
            "total_items": len(data.items),
            "approved_tickets": len(created_tickets),
            "created_work_orders": len(created_orders),
            "discarded_count": len(discarded_items)
        },
        "created_tickets": [{"id": t.id, "title": t.title, "priority": t.priority} for t in created_tickets],
        "created_work_orders": [{"id": o.id, "ticket_id": o.ticket_id, "title": o.title} for o in created_orders],
        "discarded_items": discarded_items
    }

@router.post("/inspection-approval/{ticket_id}", status_code=status.HTTP_201_CREATED)
def approve_inspection(ticket_id: int, db: Session = Depends(get_db)):
    """Approve a previously registered inspection issue and create its work order once."""
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(404, "Chamado de vistoria não encontrado")
    if not (ticket.description or "").startswith("Vistoria:"):
        raise HTTPException(400, "Este chamado não foi originado por uma vistoria")

    existing = db.query(WorkOrder).filter(WorkOrder.ticket_id == ticket.id).first()
    if existing is not None:
        return {"created": False, "work_order": {"id": existing.id, "ticket_id": ticket.id, "title": existing.title, "status": existing.status}}

    try:
        technician_assignment = db.query(TicketAssignment).filter(TicketAssignment.ticket_id == ticket.id).first()
        technician_id = technician_assignment.technician_id if technician_assignment else None
        validate_assignment(db, technician_id, None, 2.0)
        order = WorkOrder(
            client_id=ticket.client_id,
            ticket_id=ticket.id,
            technician_id=technician_id,
            title=f"Ação aprovada: {ticket.title}"[:180],
            description=ticket.description,
            status="pendente",
            estimated_duration_hours=2.0,
            labor_cost=0,
            parts_cost=0,
            total_cost=0,
        )
        db.add(order)
        db.commit()
        db.refresh(order)
    except Exception:
        db.rollback()
        raise

    return {"created": True, "work_order": {"id": order.id, "ticket_id": ticket.id, "title": order.title, "status": order.status}}
