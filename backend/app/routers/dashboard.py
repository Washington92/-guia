from datetime import date, datetime, time, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Client, Ticket, WorkOrder, Asset, StockItem, Technician, TicketAssignment

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


PRIORITIES = ("critica", "alta", "media", "baixa", "planejada")
TICKET_STATUSES = ("aberto", "em_andamento", "resolvido", "fechado")
ORDER_STATUSES = ("pendente", "em_execucao", "concluida", "cancelada")


@router.get("/analytics")
def analytics(
    client_id: int | None = Query(default=None, gt=0),
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    """Operational metrics from persisted records, not demo or estimated SLA values.

    Dates filter records by creation time (inclusive). Ticket workload counts only
    currently active tickets; assignments without a technician are reported separately.
    """
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must not exceed end_date")
    if client_id is not None and db.get(Client, client_id) is None:
        raise HTTPException(status_code=404, detail="Client not found")

    def apply_filters(statement, model):
        if client_id is not None:
            statement = statement.where(model.client_id == client_id)
        if start_date is not None:
            statement = statement.where(model.created_at >= datetime.combine(start_date, time.min, tzinfo=timezone.utc))
        if end_date is not None:
            statement = statement.where(model.created_at < datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc))
        return statement

    tickets = db.execute(apply_filters(select(Ticket.id, Ticket.status, Ticket.priority), Ticket)).all()
    orders = db.execute(apply_filters(select(WorkOrder.id, WorkOrder.status), WorkOrder)).all()
    assets = db.execute(apply_filters(select(Asset.id, Asset.status), Asset)).all()

    ticket_ids = {row.id for row in tickets}
    active_ids = {row.id for row in tickets if row.status in ("aberto", "em_andamento")}
    assignments = db.execute(select(TicketAssignment.ticket_id, TicketAssignment.technician_id).where(
        TicketAssignment.ticket_id.in_(active_ids)
    )).all() if active_ids else []
    tech_counts = {}
    for assignment in assignments:
        tech_counts[assignment.technician_id] = tech_counts.get(assignment.technician_id, 0) + 1
    technicians = db.execute(select(Technician.id, Technician.name, Technician.specialty)).all()
    completed_ids = {row.id for row in tickets if row.status in ("resolvido", "fechado")}
    completed_assignments = db.execute(
        select(TicketAssignment.ticket_id, TicketAssignment.technician_id).where(
            TicketAssignment.ticket_id.in_(completed_ids)
        )
    ).all() if completed_ids else []
    completed_counts = {}
    for assignment in completed_assignments:
        completed_counts[assignment.technician_id] = completed_counts.get(assignment.technician_id, 0) + 1
    best_total = max(completed_counts.values(), default=0)
    top_technicians = [
        {"id": tech.id, "name": tech.name, "specialty": tech.specialty, "completed_tickets": best_total}
        for tech in technicians if best_total > 0 and completed_counts.get(tech.id, 0) == best_total
    ]
    top_technicians.sort(key=lambda tech: (tech["name"].casefold(), tech["id"]))
    technician_ranking = sorted(
        [
            {"id": tech.id, "name": tech.name, "specialty": tech.specialty,
             "completed_tickets": completed_counts.get(tech.id, 0)}
            for tech in technicians if completed_counts.get(tech.id, 0) > 0
        ],
        key=lambda item: (-item["completed_tickets"], item["name"].casefold(), item["id"]),
    )[:5]


    return {
        "filters": {
            "client_id": client_id,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "date_field": "created_at",
            "timezone": "UTC",
        },
        "tickets": {
            "total": len(ticket_ids),
            "active": len(active_ids),
            "urgent_active": sum(1 for row in tickets if row.id in active_ids and row.priority in ("critica", "alta")),
            "by_priority": {priority: sum(1 for row in tickets if row.priority == priority) for priority in PRIORITIES},
            "by_status": {status: sum(1 for row in tickets if row.status == status) for status in TICKET_STATUSES},
            "unassigned_active": len(active_ids - {a.ticket_id for a in assignments}),
        },
        "work_orders": {
            "total": len(orders),
            "pending_or_running": sum(1 for row in orders if row.status in ("pendente", "em_execucao")),
            "by_status": {status: sum(1 for row in orders if row.status == status) for status in ORDER_STATUSES},
        },
        "assets": {
            "total": len(assets),
            "by_status": {status: sum(1 for row in assets if row.status == status) for status in ("ativo", "manutencao", "inativo")},
        },
        "technician_workload": [
            {
                "id": tech.id,
                "name": tech.name,
                "specialty": tech.specialty,
                "active_tickets": tech_counts.get(tech.id, 0),
                "completed_tickets": completed_counts.get(tech.id, 0),
            }
            for tech in technicians
        ],
        "top_technician": {
            "metric": "completed_tickets_by_current_assignee",
            "leaders": top_technicians,
            "ranking": technician_ranking,
            "completed_total": len(completed_ids),
            "completed_without_assignment": len(completed_ids - {a.ticket_id for a in completed_assignments}),
            "note": "Uses current assignment, not a verified completion author; ties are preserved",
        },
        "sla": {"configured": False, "message": "SLA metrics require persisted policies and deadlines"},
    }


@router.get("/report/pdf")
def export_sla_report_pdf(
    client_id: int | None = Query(default=None, gt=0),
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    """Export an operational report; this is not contractual SLA compliance."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must not exceed end_date")
    if client_id is not None and db.get(Client, client_id) is None:
        raise HTTPException(status_code=404, detail="Client not found")
    metrics = analytics(client_id=client_id, start_date=start_date, end_date=end_date, db=db)
    clients = {row.id: row.name for row in db.scalars(select(Client)).all()}
    sample_query = select(Ticket).order_by(Ticket.created_at.desc())
    if client_id is not None:
        sample_query = sample_query.where(Ticket.client_id == client_id)
    if start_date is not None:
        sample_query = sample_query.where(Ticket.created_at >= datetime.combine(start_date, time.min, tzinfo=timezone.utc))
    if end_date is not None:
        sample_query = sample_query.where(Ticket.created_at < datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc))
    sample = db.scalars(sample_query.limit(20)).all()
    from ..services.pdf_generator import generate_sla_report_pdf
    content = generate_sla_report_pdf(metrics, client_name=clients.get(client_id) if client_id else "Todas as unidades",
        start_date=start_date, end_date=end_date, sample_tickets=sample, client_names=clients)
    return Response(content=content, media_type="application/pdf", headers={
        "Content-Disposition": 'inline; filename="relatorio_operacional_sla.pdf"'
    })
