"""Pydantic data schemas and validation models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import PriorityLevel, RequisitionStatus


# ---------------------------------------------------------
# Line Item Schemas
# ---------------------------------------------------------
class LineItemBase(BaseModel):
    item_description: str = Field(..., min_length=2, max_length=255)
    category: str = Field(..., min_length=2, max_length=64)
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0.0)
    supplier_name: str = Field(..., min_length=2, max_length=128)


class LineItemCreate(LineItemBase):
    pass


class LineItemResponse(LineItemBase):
    id: int
    requisition_id: int
    total_price: float

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Approval Schemas
# ---------------------------------------------------------
class ApprovalCreate(BaseModel):
    approver_name: str = Field(..., min_length=2, max_length=128)
    approver_role: str = Field(..., min_length=2, max_length=64)
    decision: str = Field(..., pattern="^(APPROVED|REJECTED)$")
    comments: str | None = None


class ApprovalResponse(BaseModel):
    id: int
    requisition_id: int
    approver_name: str
    approver_role: str
    decision: str
    comments: str | None
    decided_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Requisition Schemas
# ---------------------------------------------------------
class RequisitionBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str | None = None
    requester_name: str = Field(..., min_length=2, max_length=128)
    requester_email: EmailStr
    department: str = Field(..., min_length=2, max_length=64)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    priority: PriorityLevel = Field(default=PriorityLevel.MEDIUM)


class RequisitionCreate(RequisitionBase):
    line_items: list[LineItemCreate] = Field(..., min_length=1)


class RequisitionUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    department: str | None = None
    priority: PriorityLevel | None = None


class RequisitionResponse(RequisitionBase):
    id: int
    req_number: str
    total_amount: float
    status: RequisitionStatus
    created_at: datetime
    updated_at: datetime
    line_items: list[LineItemResponse] = []
    approvals: list[ApprovalResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Analytics Schemas
# ---------------------------------------------------------
class DepartmentSpend(BaseModel):
    department: str
    total_spend: float
    requisition_count: int


class SpendAnalyticsResponse(BaseModel):
    total_requisition_count: int
    total_spend_usd: float
    status_breakdown: dict[str, int]
    department_spend: list[DepartmentSpend]


# ---------------------------------------------------------
# Health & SRE Diagnostics Schemas
# ---------------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    version: str
    app_name: str
    environment: str


class DatabaseHealthDetail(BaseModel):
    connected: bool
    latency_ms: float
    message: str


class ReadinessResponse(BaseModel):
    ready: bool
    status: str
    database: DatabaseHealthDetail
    timestamp: datetime


# ---------------------------------------------------------
# Chaos Control Schemas
# ---------------------------------------------------------
class ChaosLatencyRequest(BaseModel):
    delay_seconds: float = Field(..., ge=0.0, le=30.0)
    probability: float = Field(default=1.0, ge=0.0, le=1.0)


class ChaosErrorRequest(BaseModel):
    probability: float = Field(default=1.0, ge=0.0, le=1.0)
    status_code: int = Field(default=500, ge=400, le=599)
    message: str = Field(default="Chaos Injected: Internal Server Error")


class ChaosMemoryRequest(BaseModel):
    megabytes: int = Field(default=50, ge=1, le=500)
