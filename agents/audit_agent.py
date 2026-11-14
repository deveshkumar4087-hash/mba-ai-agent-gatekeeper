"""
Audit Agent Module.

Responsible for capturing and preserving immutable audit records:
- Captures timestamp, request parameters, gatekeeper decision, and triggered rule number
- Ensures traceability for compliance and regulatory reporting
- Interfaces with the AuditLogger service for persistent SQLite record-keeping

AI Agent Gatekeeper for Banking Transactions
Student Enrolment: PGD202565745
Assigned Domain: Banking
Context: Capital One (Student-designed academic prototype; not official policy).
"""

from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field

from services.audit_logger import AuditLogger
from services.data_store import get_current_utc_timestamp


class AuditRecord(BaseModel):
    """Schema for a single audit log entry."""
    customer_id: str = Field(..., min_length=1, description="Customer identifier")
    agent_name: str = Field(..., min_length=1, description="AI agent identifier")
    action: str = Field(..., min_length=1, description="Banking action attempted")
    amount: float = Field(default=0.0, ge=0.0, description="Transaction amount")
    decision: str = Field(..., description="Gatekeeper decision: ALLOW | ASK CUSTOMER | BLOCK")
    rule_number: str = Field(..., description="Triggered rule identifier (R1 - R8)")
    rule_id: Optional[str] = Field(default=None, description="Alias for rule_id")
    reason: Optional[str] = Field(default="", description="Explanatory notes or risk rationale")
    notes: Optional[str] = Field(default="", description="Optional additional notes")
    timestamp: Optional[str] = Field(default_factory=get_current_utc_timestamp, description="UTC timestamp")


class AuditAgent:
    """Agent responsible for overseeing audit trail integrity."""

    def __init__(self, audit_logger: Optional[AuditLogger] = None) -> None:
        self.audit_logger = audit_logger or AuditLogger()

    def record_transaction(
        self,
        record: Union[AuditRecord, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Record a gatekeeper transaction into the immutable audit trail.
        """
        if isinstance(record, dict):
            rec = AuditRecord(**record)
        elif isinstance(record, AuditRecord):
            rec = record
        else:
            raise TypeError(f"Expected AuditRecord or dict, got {type(record)}")

        rule = rec.rule_id or rec.rule_number
        reason = rec.reason or rec.notes or ""

        return self.audit_logger.log_event(
            customer_id=rec.customer_id,
            agent_name=rec.agent_name,
            action=rec.action,
            amount=rec.amount,
            decision=rec.decision,
            rule_number=rule,
            reason=reason,
        )
