"""Procurement Requisitions & Approval Workflow API endpoints."""

from __future__ import annotations

import random
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chaos.engine import chaos_engine
from app.database import get_db
from app.metrics import (
    APPROVALS_PROCESSED_TOTAL,
    REQUISITION_VALUE_TOTAL,
    REQUISITIONS_BY_STATE,
    REQUISITIONS_CREATED_TOTAL,
)
from app.models import (
    ApprovalLog,
    AuditLog,
    LineItem,
    Requisition,
    RequisitionStatus,
)
from app.schemas import (
    ApprovalCreate,
    RequisitionCreate,
    RequisitionResponse,
)

router = APIRouter(prefix="/requisitions", tags=["Procurement Requisitions"])


def _generate_req_number() -> str:
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_suffix = random.randint(1000, 9999)
    return f"PR-{today_str}-{random_suffix}"


async def _sync_state_metrics(db: AsyncSession) -> None:
    """Updates Prometheus gauges for each requisition state."""
    state_counts = await db.execute(
        select(Requisition.status, func.count(Requisition.id)).group_by(Requisition.status)
    )
    for st in RequisitionStatus:
        REQUISITIONS_BY_STATE.labels(state=st.value).set(0)
    for row in state_counts.all():
        REQUISITIONS_BY_STATE.labels(state=row[0].value).set(row[1])


@router.post(
    "/",
    response_model=RequisitionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Procurement Requisition",
    description="Creates a new purchase requisition with line items and recalculates total amount.",
)
async def create_requisition(
    payload: RequisitionCreate,
    db: AsyncSession = Depends(get_db),
):
    await chaos_engine.maybe_inject_latency()
    chaos_engine.maybe_inject_error()
    chaos_engine.check_db_interception()

    # Calculate line items total
    total_amount = sum(item.quantity * item.unit_price for item in payload.line_items)

    req_number = _generate_req_number()

    requisition = Requisition(
        req_number=req_number,
        title=payload.title,
        description=payload.description,
        requester_name=payload.requester_name,
        requester_email=payload.requester_email,
        department=payload.department,
        currency=payload.currency.upper(),
        priority=payload.priority,
        total_amount=round(total_amount, 2),
        status=RequisitionStatus.DRAFT,
    )

    for item in payload.line_items:
        line_item = LineItem(
            item_description=item.item_description,
            category=item.category,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=round(item.quantity * item.unit_price, 2),
            supplier_name=item.supplier_name,
        )
        requisition.line_items.append(line_item)

    audit = AuditLog(
        entity_type="Requisition",
        entity_id=0,  # updated after commit
        action="CREATED",
        performed_by=payload.requester_name,
        details=f"Created requisition {req_number} with {len(payload.line_items)} line items. Total: {total_amount} {payload.currency}",
    )

    db.add(requisition)
    await db.flush()

    audit.entity_id = requisition.id
    db.add(audit)
    await db.commit()
    await db.refresh(requisition)

    # Emit Prometheus business metrics
    REQUISITIONS_CREATED_TOTAL.labels(
        department=requisition.department,
        currency=requisition.currency,
    ).inc()
    REQUISITION_VALUE_TOTAL.labels(
        department=requisition.department,
        currency=requisition.currency,
    ).inc(total_amount)

    await _sync_state_metrics(db)

    return requisition


@router.get(
    "/",
    response_model=list[RequisitionResponse],
    summary="List Requisitions",
    description="Retrieves requisitions with optional filtering by status or department.",
)
async def list_requisitions(
    department: str | None = Query(None, description="Filter by department"),
    req_status: RequisitionStatus | None = Query(None, alias="status", description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    await chaos_engine.maybe_inject_latency()
    chaos_engine.maybe_inject_error()
    chaos_engine.check_db_interception()

    stmt = select(Requisition).order_by(desc(Requisition.created_at)).offset(skip).limit(limit)

    if department:
        stmt = stmt.where(Requisition.department == department)
    if req_status:
        stmt = stmt.where(Requisition.status == req_status)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get(
    "/{req_id}",
    response_model=RequisitionResponse,
    summary="Get Requisition Details",
)
async def get_requisition(
    req_id: int,
    db: AsyncSession = Depends(get_db),
):
    await chaos_engine.maybe_inject_latency()
    chaos_engine.maybe_inject_error()
    chaos_engine.check_db_interception()

    result = await db.execute(select(Requisition).where(Requisition.id == req_id))
    requisition = result.scalar_one_or_none()

    if not requisition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requisition #{req_id} not found",
        )
    return requisition


@router.post(
    "/{req_id}/submit",
    response_model=RequisitionResponse,
    summary="Submit Requisition for Approval",
)
async def submit_requisition(
    req_id: int,
    db: AsyncSession = Depends(get_db),
):
    await chaos_engine.maybe_inject_latency()
    chaos_engine.maybe_inject_error()
    chaos_engine.check_db_interception()

    result = await db.execute(select(Requisition).where(Requisition.id == req_id))
    requisition = result.scalar_one_or_none()

    if not requisition:
        raise HTTPException(status_code=404, detail="Requisition not found")

    if requisition.status != RequisitionStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit requisition in '{requisition.status}' state. Only DRAFT can be submitted.",
        )

    requisition.status = RequisitionStatus.SUBMITTED
    db.add(
        AuditLog(
            entity_type="Requisition",
            entity_id=req_id,
            action="SUBMITTED",
            performed_by=requisition.requester_name,
            details=f"Submitted requisition {requisition.req_number} for manager approval.",
        )
    )

    await db.commit()
    await db.refresh(requisition)
    await _sync_state_metrics(db)

    return requisition


@router.post(
    "/{req_id}/approve",
    response_model=RequisitionResponse,
    summary="Review Requisition (Approve / Reject)",
)
async def review_requisition(
    req_id: int,
    payload: ApprovalCreate,
    db: AsyncSession = Depends(get_db),
):
    await chaos_engine.maybe_inject_latency()
    chaos_engine.maybe_inject_error()
    chaos_engine.check_db_interception()

    result = await db.execute(select(Requisition).where(Requisition.id == req_id))
    requisition = result.scalar_one_or_none()

    if not requisition:
        raise HTTPException(status_code=404, detail="Requisition not found")

    if requisition.status != RequisitionStatus.SUBMITTED:
        raise HTTPException(
            status_code=400,
            detail=f"Requisition is in '{requisition.status}' state. Only SUBMITTED requisitions can be reviewed.",
        )

    new_status = (
        RequisitionStatus.APPROVED
        if payload.decision == "APPROVED"
        else RequisitionStatus.REJECTED
    )
    requisition.status = new_status

    approval = ApprovalLog(
        requisition_id=requisition.id,
        approver_name=payload.approver_name,
        approver_role=payload.approver_role,
        decision=payload.decision,
        comments=payload.comments,
    )
    requisition.approvals.append(approval)

    db.add(
        AuditLog(
            entity_type="Requisition",
            entity_id=req_id,
            action=f"DECISION_{payload.decision}",
            performed_by=payload.approver_name,
            details=f"Decision {payload.decision} by {payload.approver_name} ({payload.approver_role}). Comments: {payload.comments}",
        )
    )

    await db.commit()
    await db.refresh(requisition)

    APPROVALS_PROCESSED_TOTAL.labels(
        decision=payload.decision,
        approver_role=payload.approver_role,
    ).inc()

    await _sync_state_metrics(db)

    return requisition


@router.delete(
    "/{req_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Requisition",
)
async def delete_requisition(
    req_id: int,
    db: AsyncSession = Depends(get_db),
):
    await chaos_engine.maybe_inject_latency()
    chaos_engine.maybe_inject_error()
    chaos_engine.check_db_interception()

    result = await db.execute(select(Requisition).where(Requisition.id == req_id))
    requisition = result.scalar_one_or_none()

    if not requisition:
        raise HTTPException(status_code=404, detail="Requisition not found")

    await db.delete(requisition)
    await db.commit()
    await _sync_state_metrics(db)

