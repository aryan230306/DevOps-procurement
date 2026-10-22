"""Procurement spend analytics & business intelligence API."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chaos.engine import chaos_engine
from app.database import get_db
from app.models import Requisition, RequisitionStatus
from app.schemas import DepartmentSpend, SpendAnalyticsResponse

router = APIRouter(prefix="/analytics", tags=["Procurement Analytics"])


@router.get(
    "/spend",
    response_model=SpendAnalyticsResponse,
    summary="Spend Analytics Summary",
    description="Aggregates procurement spend volume across departments and status categories.",
)
async def get_spend_analytics(db: AsyncSession = Depends(get_db)):
    await chaos_engine.maybe_inject_latency()
    chaos_engine.maybe_inject_error()
    chaos_engine.check_db_interception()

    # Total counts and amount
    total_stats = await db.execute(
        select(
            func.count(Requisition.id),
            func.coalesce(func.sum(Requisition.total_amount), 0.0),
        )
    )
    total_count, total_sum = total_stats.one()

    # Status breakdown
    status_stats = await db.execute(
        select(Requisition.status, func.count(Requisition.id)).group_by(
            Requisition.status
        )
    )
    status_map = {st.value: 0 for st in RequisitionStatus}
    for row in status_stats.all():
        status_map[row[0].value] = row[1]

    # Department breakdown
    dept_stats = await db.execute(
        select(
            Requisition.department,
            func.coalesce(func.sum(Requisition.total_amount), 0.0),
            func.count(Requisition.id),
        ).group_by(Requisition.department)
    )
    dept_list = [
        DepartmentSpend(
            department=row[0],
            total_spend=round(float(row[1]), 2),
            requisition_count=row[2],
        )
        for row in dept_stats.all()
    ]

    return SpendAnalyticsResponse(
        total_requisition_count=total_count,
        total_spend_usd=round(float(total_sum), 2),
        status_breakdown=status_map,
        department_spend=dept_list,
    )
