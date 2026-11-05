from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class ClientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=40)
    document: str | None = Field(default=None, max_length=32)

class ClientRead(ClientCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

class TicketCreate(BaseModel):
    client_id: int
    title: str = Field(min_length=3, max_length=180)
    description: str = ""
    priority: Literal["baixa", "media", "alta", "critica"] = "media"

class TicketUpdate(BaseModel):
    status: Literal["aberto", "em_andamento", "resolvido", "fechado"]

class TicketRead(TicketCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    created_at: datetime

class WorkOrderItemCreate(BaseModel):
    stock_item_id: int | None = None
    description: str = Field(min_length=1, max_length=180)
    quantity: int = Field(default=1, ge=1)
    unit_price: float = Field(default=0.0, ge=0.0)

class WorkOrderItemRead(WorkOrderItemCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    work_order_id: int
    total_price: float

class WorkOrderCreate(BaseModel):
    client_id: int
    ticket_id: int | None = None
    technician_id: int | None = None
    scheduled_at: datetime | None = None
    estimated_duration_hours: float = Field(default=2.0, gt=0, le=24)
    title: str = Field(min_length=3, max_length=180)
    description: str = ""
    labor_cost: float = Field(default=0.0, ge=0.0)
    items: list[WorkOrderItemCreate] = []

class WorkOrderUpdate(BaseModel):
    status: Literal["pendente", "em_execucao", "concluida", "cancelada"] | None = None
    description: str | None = None
    labor_cost: float | None = Field(default=None, ge=0.0)
    technician_id: int | None = None
    scheduled_at: datetime | None = None
    estimated_duration_hours: float | None = Field(default=None, gt=0, le=24)

class WorkOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    client_id: int
    ticket_id: int | None
    technician_id: int | None
    scheduled_at: datetime | None
    estimated_duration_hours: float
    title: str
    description: str
    status: str
    labor_cost: float
    parts_cost: float
    total_cost: float
    created_at: datetime
    items: list[WorkOrderItemRead] = []

class AssetCreate(BaseModel):
    client_id: int
    name: str = Field(min_length=2, max_length=160)
    category: Literal["switch", "roteador", "access_point", "camera", "dvr_nvr", "servidor", "outro"] = "outro"
    serial_number: str | None = Field(default=None, max_length=100)
    ip_address: str | None = Field(default=None, max_length=45)
    location: str | None = Field(default=None, max_length=160)

class AssetUpdate(BaseModel):
    status: Literal["ativo", "manutencao", "inativo"] | None = None
    location: str | None = Field(default=None, max_length=160)

class AssetRead(AssetCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    created_at: datetime

class StockItemCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    sku: str | None = Field(default=None, max_length=80)
    unit: Literal["un", "m", "cx", "pct"] = "un"
    min_quantity: int = Field(default=0, ge=0)

class StockItemRead(StockItemCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    quantity: int
    created_at: datetime

class StockMovementCreate(BaseModel):
    item_id: int
    work_order_id: int | None = None
    type: Literal["entrada", "saida"]
    quantity: int = Field(gt=0)
    note: str = Field(default="", max_length=255)

class StockMovementRead(StockMovementCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

class TicketNoteCreate(BaseModel):
    author: str = Field(min_length=2, max_length=100)
    content: str = Field(min_length=3, max_length=4000)

class TicketNoteRead(TicketNoteCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ticket_id: int
    created_at: datetime

class TechnicianCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    email: str | None = Field(default=None, max_length=254)
    specialty: str | None = Field(default=None, max_length=100)

class TechnicianRead(TechnicianCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    active: int
    created_at: datetime

class TicketAssignmentCreate(BaseModel):
    technician_id: int

class TicketAssignmentRead(BaseModel):
    ticket_id: int
    technician_id: int
    assigned_at: datetime
