from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Technician, WorkOrder
from ..schemas import WorkOrderRead

router = APIRouter(prefix="/api/schedule", tags=["Agenda e escala"])


def _utc_aware(value: datetime) -> datetime:
    """Normalize database timestamps (including SQLite's naive values) to UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _validate_assignment(
    db: Session,
    technician_id: int | None,
    scheduled_at: datetime | None,
    duration_hours: float,
    exclude_order_id: int | None = None,
) -> None:
    if technician_id is None:
        return
    technician = db.get(Technician, technician_id)
    if technician is None or not technician.active:
        raise HTTPException(404, "Técnico ativo não encontrado")
    if scheduled_at is None:
        return

    start = _utc_aware(scheduled_at)
    end = start + timedelta(hours=duration_hours)
    query = select(WorkOrder).where(
        WorkOrder.technician_id == technician_id,
        WorkOrder.scheduled_at.is_not(None),
        WorkOrder.status.notin_(["concluida", "cancelada"]),
    )
    if exclude_order_id is not None:
        query = query.where(WorkOrder.id != exclude_order_id)

    for existing in db.scalars(query).all():
        existing_start = _utc_aware(existing.scheduled_at)
        existing_end = existing_start + timedelta(hours=existing.estimated_duration_hours)
        if start < existing_end and existing_start < end:
            raise HTTPException(409, "Conflito de agenda: o técnico já possui uma OS nesse horário")


@router.get("", response_model=list[WorkOrderRead])
def list_schedule(
    start: datetime = Query(..., description="Início do período (ISO 8601)"),
    end: datetime = Query(..., description="Fim do período (ISO 8601)"),
    technician_id: int | None = None,
    db: Session = Depends(get_db),
):
    start_utc = _utc_aware(start)
    end_utc = _utc_aware(end)
    if end_utc <= start_utc:
        raise HTTPException(422, "O fim do período deve ser posterior ao início")

    query = select(WorkOrder).where(
        WorkOrder.scheduled_at >= start_utc,
        WorkOrder.scheduled_at < end_utc,
    )
    if technician_id is not None:
        query = query.where(WorkOrder.technician_id == technician_id)
    return db.scalars(query.order_by(WorkOrder.scheduled_at, WorkOrder.id).limit(500)).all()


@router.get("/technicians/{technician_id}", response_model=list[WorkOrderRead])
def technician_schedule(
    technician_id: int,
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: Session = Depends(get_db),
):
    technician = db.get(Technician, technician_id)
    if technician is None:
        raise HTTPException(404, "Técnico não encontrado")
    return list_schedule(start, end, technician_id, db)


def validate_assignment(db, technician_id, scheduled_at, duration_hours, exclude_order_id=None):
    """Public helper reused by work-order create/update routes."""
    _validate_assignment(db, technician_id, scheduled_at, duration_hours, exclude_order_id)
