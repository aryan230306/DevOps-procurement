import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class RequisitionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ORDERED = "ORDERED"
    CANCELLED = "CANCELLED"


class PriorityLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class Requisition(Base):
    __tablename__ = "requisitions"

    id = Column(Integer, primary_key=True, index=True)
    req_number = Column(String(32), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    requester_name = Column(String(128), nullable=False)
    requester_email = Column(String(128), nullable=False)
    department = Column(String(64), index=True, nullable=False)
    total_amount = Column(Float, default=0.0, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    status = Column(
        Enum(RequisitionStatus),
        default=RequisitionStatus.DRAFT,
        index=True,
        nullable=False,
    )
    priority = Column(
        Enum(PriorityLevel),
        default=PriorityLevel.MEDIUM,
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    line_items = relationship(
        "LineItem",
        back_populates="requisition",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    approvals = relationship(
        "ApprovalLog",
        back_populates="requisition",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(Integer, primary_key=True, index=True)
    requisition_id = Column(
        Integer, ForeignKey("requisitions.id", ondelete="CASCADE"), nullable=False
    )
    item_description = Column(String(255), nullable=False)
    category = Column(String(64), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    supplier_name = Column(String(128), nullable=False)

    requisition = relationship("Requisition", back_populates="line_items")


class ApprovalLog(Base):
    __tablename__ = "approval_logs"

    id = Column(Integer, primary_key=True, index=True)
    requisition_id = Column(
        Integer, ForeignKey("requisitions.id", ondelete="CASCADE"), nullable=False
    )
    approver_name = Column(String(128), nullable=False)
    approver_role = Column(String(64), nullable=False)
    decision = Column(String(32), nullable=False)  # APPROVED or REJECTED
    comments = Column(Text, nullable=True)
    decided_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    requisition = relationship("Requisition", back_populates="approvals")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(Integer, nullable=False)
    action = Column(String(64), nullable=False)
    performed_by = Column(String(128), nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
