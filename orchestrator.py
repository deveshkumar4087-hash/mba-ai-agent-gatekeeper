"""
Orchestrator Module - AI Agent Gatekeeper for Banking Transactions.

Coordinates the complete end-to-end evaluation flow between:
- User / Streamlit interface
- Specialized Agents (Registration, Permission, Decision, Revocation, Audit)
- Core Services (DataStore, RuleEngine, AuditLogger)

Pipeline:
REQUEST
  ↓
IDENTIFY CUSTOMER + AGENT
  ↓
CHECK AGENT REGISTRATION/STATUS (PermissionAgent)
  ↓
CHECK REVOCATION (PermissionAgent / RuleEngine)
  ↓
DETERMINISTIC RULE ENGINE (RuleEngine / DecisionAgent)
  ↓
STRUCTURED DECISION (ALLOW / ASK CUSTOMER / BLOCK + Rule ID)
  ↓
PERSISTENT AUDIT LOG (AuditAgent / AuditLogger - including Unknown & Revoked)
  ↓
RETURN STRUCTURED RESULT

AI Agent Gatekeeper for Banking Transactions
Student Enrolment: PGD202565745
Assigned Domain: Banking
Context: Capital One (Student-designed academic prototype; not official policy).
"""

from typing import Dict, Any, Optional, Union
from pathlib import Path
from pydantic import BaseModel, Field, field_validator

from services.data_store import DataStore
from services.rule_engine import (
    RuleEngine,
    RuleEvaluationRequest,
    RuleEvaluationResult,
    BankingAction,
    AgentStatus,
    GatekeeperDecision,
    RuleId,
    PROTOTYPE_AUTOMATIC_PAYMENT_THRESHOLD,
)
from services.audit_logger import AuditLogger
from agents.registration_agent import RegistrationAgent
from agents.revocation_agent import RevocationAgent
from agents.permission_agent import PermissionAgent, AgentVerificationRequest
from agents.decision_agent import DecisionAgent
from agents.audit_agent import AuditAgent, AuditRecord


class TransactionRequest(BaseModel):
    """Input payload for banking action gatekeeping."""
    customer_id: str = Field(..., min_length=1, description="Customer identifier")
    agent_name: str = Field(..., min_length=1, description="Personal AI agent name")
    action: str = Field(..., min_length=1, description="Banking action: View Balance | Pay Bill | Transfer Money")
    amount: float = Field(default=0.0, ge=0.0, description="Transaction monetary amount (>= 0.0)")
    customer_rejected: bool = Field(default=False, description="Customer explicitly rejected this request")
    customer_confirmed: Optional[bool] = Field(default=None, description="Explicit customer confirmation flag")

    @field_validator("customer_id", "agent_name", "action")
    @classmethod
    def check_non_empty(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Field cannot be empty or whitespace only.")
        return s


class GatekeeperResponse(BaseModel):
    """Output payload returned by the Gatekeeper Orchestrator."""
    decision: str = Field(..., description="ALLOW | ASK CUSTOMER | BLOCK")
    rule_id: str = Field(..., description="Triggered rule identifier (R1 - R8)")
    rule_number: str = Field(..., description="Triggered rule identifier alias for compatibility")
    reason: str = Field(..., description="Business risk justification")
    customer_id: str
    agent_name: str
    action: str
    amount: float
    timestamp: str
    threshold: Optional[float] = None
    audit_id: Optional[int] = None
    message: str = ""


class GatekeeperOrchestrator:
    """Central coordinator for the AI Agent Gatekeeper prototype."""

    def __init__(
        self,
        data_store: Optional[DataStore] = None,
        rule_engine: Optional[RuleEngine] = None,
        audit_logger: Optional[AuditLogger] = None,
        db_path: Optional[Union[str, Path]] = None,
    ) -> None:
        # Initialize persistent data store
        self.data_store = data_store or DataStore(db_path=db_path)

        # Initialize deterministic rule engine with prototype threshold ($500)
        self.rule_engine = rule_engine or RuleEngine(threshold=PROTOTYPE_AUTOMATIC_PAYMENT_THRESHOLD)

        # Initialize persistent audit logger
        self.audit_logger = audit_logger or AuditLogger(data_store=self.data_store)

        # Initialize specialized agents
        self.registration_agent = RegistrationAgent(data_store=self.data_store)
        self.revocation_agent = RevocationAgent(data_store=self.data_store)
        self.permission_agent = PermissionAgent(data_store=self.data_store)
        self.decision_agent = DecisionAgent(rule_engine=self.rule_engine)
        self.audit_agent = AuditAgent(audit_logger=self.audit_logger)

        self.is_initialized = True

    def register_agent(self, customer_id: str, agent_name: str, notes: str = "") -> Dict[str, Any]:
        """Convenience method to register an AI agent for a customer."""
        return self.registration_agent.register_agent({
            "customer_id": customer_id,
            "agent_name": agent_name,
            "description": notes,
        })

    def revoke_agent(self, customer_id: str, agent_name: str, reason: str = "") -> Dict[str, Any]:
        """Convenience method to permanently revoke an AI agent."""
        return self.revocation_agent.revoke_agent({
            "customer_id": customer_id,
            "agent_name": agent_name,
            "reason": reason,
        })

    def export_audit_csv(
        self,
        customer_id: Optional[str] = None,
        decision: Optional[str] = None,
        logs: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Export persistent audit trail to CSV format using AuditLogger."""
        return self.audit_logger.export_csv(customer_id=customer_id, decision=decision, logs=logs)

    def evaluate_request(
        self,
        customer_id: str,
        agent_name: str,
        action: str,
        amount: float = 0.0,
        customer_rejected: bool = False,
        customer_confirmed: Optional[bool] = None,
    ) -> GatekeeperResponse:
        """
        Evaluate a transaction request end-to-end through the complete gatekeeper pipeline.
        """
        request = TransactionRequest(
            customer_id=customer_id,
            agent_name=agent_name,
            action=action,
            amount=amount,
            customer_rejected=customer_rejected,
            customer_confirmed=customer_confirmed,
        )
        return self.process_transaction(request)

    def process_transaction(self, request: TransactionRequest) -> GatekeeperResponse:
        """
        Execute the end-to-end pipeline:
        1. Input validation (handled by TransactionRequest schema)
        2. Permission & standing verification (PermissionAgent)
        3. Deterministic rule evaluation (RuleEngine / DecisionAgent)
        4. Audit logging (AuditAgent / AuditLogger - covers all decisions including R1 & R7)
        5. Return structured GatekeeperResponse
        """
        # Step 1: Permission Agent checks agent standing
        # Verifies if agent is ACTIVE, REVOKED, or UNKNOWN
        standing = self.permission_agent.verify_agent_standing(
            AgentVerificationRequest(
                customer_id=request.customer_id,
                agent_name=request.agent_name,
                action=request.action,
            )
        )
        agent_status = standing["status"]  # "ACTIVE" | "REVOKED" | "UNKNOWN"
        normalized_action = standing["action"]

        # Step 2: Pass context to Deterministic Rule Engine
        eval_req = RuleEvaluationRequest(
            customer_id=request.customer_id,
            agent_name=request.agent_name,
            action=normalized_action,
            amount=request.amount,
            agent_status=agent_status,
            customer_rejected=request.customer_rejected,
            customer_confirmed=request.customer_confirmed,
        )
        rule_result: RuleEvaluationResult = self.rule_engine.evaluate(eval_req)

        # Step 3: Record persistent audit log entry (including Unknown & Revoked agents)
        audit_entry = self.audit_logger.log_event(
            customer_id=request.customer_id,
            agent_name=request.agent_name,
            action=normalized_action,
            amount=request.amount,
            decision=rule_result.decision.value,
            rule_number=rule_result.rule_id.value,
            reason=rule_result.reason,
        )

        # Step 4: Return structured response
        return GatekeeperResponse(
            decision=rule_result.decision.value,
            rule_id=rule_result.rule_id.value,
            rule_number=rule_result.rule_id.value,
            reason=rule_result.reason,
            customer_id=request.customer_id,
            agent_name=request.agent_name,
            action=normalized_action,
            amount=request.amount,
            timestamp=audit_entry["timestamp"],
            threshold=rule_result.threshold,
            audit_id=audit_entry.get("audit_id"),
            message=f"Gatekeeper decision: {rule_result.decision.value} based on Rule {rule_result.rule_id.value}.",
        )
