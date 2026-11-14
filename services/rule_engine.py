"""
Deterministic Rule Engine Service Module.

AI Agent Gatekeeper for Banking Transactions.
Student Enrolment: PGD202565745
Assigned Domain: Banking
Context Organization: Capital One (Student-designed academic prototype;
NOT an official Capital One system and not official Capital One policies).

STAGE 2 IMPLEMENTATION:
Deterministic Python logic implementing the 8 policy rules for autonomous
AI agents accessing customer bank accounts.
"""

from enum import Enum
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator


# Student-designed prototype threshold (NOT an official bank spending limit)
PROTOTYPE_AUTOMATIC_PAYMENT_THRESHOLD: float = 500.0


class GatekeeperDecision(str, Enum):
    """Allowed gatekeeper decision outcomes."""
    ALLOW = "ALLOW"
    ASK_CUSTOMER = "ASK CUSTOMER"
    BLOCK = "BLOCK"


class RuleId(str, Enum):
    """Rule identifiers for the 8 student-designed prototype policy rules."""
    R1 = "R1"  # Unknown Agent
    R2 = "R2"  # Registered Read-Only Access (View Balance)
    R3 = "R3"  # Low-Value Bill Payment (<= $500)
    R4 = "R4"  # High-Value Bill Payment (> $500)
    R5 = "R5"  # Low-Value Money Transfer (<= $500)
    R6 = "R6"  # High-Value Money Transfer (> $500)
    R7 = "R7"  # Revoked Agent
    R8 = "R8"  # Customer Rejection


class BankingAction(str, Enum):
    """Supported banking actions for the prototype."""
    VIEW_BALANCE = "View Balance"
    PAY_BILL = "Pay Bill"
    TRANSFER_MONEY = "Transfer Money"

    @classmethod
    def from_str(cls, value: str) -> "BankingAction":
        """Normalize and parse an action string."""
        cleaned = value.strip().lower()
        if cleaned in ("view balance", "view_balance", "balance", "view"):
            return cls.VIEW_BALANCE
        elif cleaned in ("pay bill", "pay_bill", "pay a bill", "bill_pay", "pay"):
            return cls.PAY_BILL
        elif cleaned in ("transfer money", "transfer_money", "transfer", "money transfer"):
            return cls.TRANSFER_MONEY
        raise ValueError(
            f"Unsupported banking action '{value}'. "
            f"Allowed actions: {[a.value for a in cls]}"
        )


class AgentStatus(str, Enum):
    """Operational status of personal AI agent."""
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_str(cls, value: str) -> "AgentStatus":
        """Normalize and parse an agent status string."""
        cleaned = value.strip().upper()
        if cleaned in ("ACTIVE", "REGISTERED", "TRUE", "ACTIVE_REGISTERED"):
            return cls.ACTIVE
        elif cleaned in ("REVOKED", "DEACTIVATED", "SUSPENDED"):
            return cls.REVOKED
        elif cleaned in ("UNKNOWN", "UNREGISTERED", "FALSE"):
            return cls.UNKNOWN
        raise ValueError(f"Unrecognized agent status '{value}'. Allowed: {[s.value for s in cls]}")


class RuleEvaluationRequest(BaseModel):
    """Structured input model for policy rule evaluation."""
    customer_id: str = Field(..., description="Customer identifier")
    agent_name: str = Field(..., description="Name of the AI agent")
    action: Union[BankingAction, str] = Field(..., description="Banking action: View Balance | Pay Bill | Transfer Money")
    amount: float = Field(default=0.0, ge=0.0, description="Transaction amount (numeric, non-negative)")
    agent_status: Union[AgentStatus, str] = Field(default=AgentStatus.ACTIVE, description="ACTIVE | REVOKED | UNKNOWN")
    customer_rejected: bool = Field(default=False, description="Whether customer explicitly rejected this request")
    customer_confirmed: Optional[bool] = Field(default=None, description="Explicit customer confirmation flag")

    @field_validator("action", mode="before")
    @classmethod
    def parse_action(cls, v: Any) -> BankingAction:
        if isinstance(v, BankingAction):
            return v
        return BankingAction.from_str(str(v))

    @field_validator("agent_status", mode="before")
    @classmethod
    def parse_status(cls, v: Any) -> AgentStatus:
        if isinstance(v, AgentStatus):
            return v
        return AgentStatus.from_str(str(v))


class RuleEvaluationResult(BaseModel):
    """Structured output returned by the deterministic rule engine."""
    decision: GatekeeperDecision = Field(..., description="ALLOW | ASK CUSTOMER | BLOCK")
    rule_id: RuleId = Field(..., description="Triggered rule identifier (R1 - R8)")
    reason: str = Field(..., description="Business and risk rationale for decision")
    threshold: Optional[float] = Field(
        default=None,
        description="Applicable prototype threshold in USD (where relevant)",
    )


class RuleEngine:
    """
    Deterministic rule engine implementing the 8 student-designed banking policy rules.
    Operates with strict deterministic priority:
      1. R8 — Customer explicit rejection
      2. R7 — Revoked agent (permanent override)
      3. R1 — Unknown/unregistered agent
      4. R2 — View Balance (read-only)
      5. R3/R4 — Pay Bill (<= $500 vs > $500 threshold)
      6. R5/R6 — Transfer Money (<= $500 vs > $500 threshold)
    """

    def __init__(self, threshold: float = PROTOTYPE_AUTOMATIC_PAYMENT_THRESHOLD) -> None:
        self.threshold = threshold

    def evaluate(self, request_data: Union[RuleEvaluationRequest, Dict[str, Any]]) -> RuleEvaluationResult:
        """
        Evaluate a transaction request against the 8 policy rules in strict priority order.
        """
        if isinstance(request_data, dict):
            request = RuleEvaluationRequest(**request_data)
        elif isinstance(request_data, RuleEvaluationRequest):
            request = request_data
        else:
            raise TypeError(f"Expected RuleEvaluationRequest or dict, got {type(request_data)}")

        # PRIORITY 1: RULE R8 — CUSTOMER REJECTION
        # Customer explicit rejection takes ultimate precedence
        if request.customer_rejected:
            return RuleEvaluationResult(
                decision=GatekeeperDecision.BLOCK,
                rule_id=RuleId.R8,
                reason="The customer's explicit decision overrides the AI agent's permission.",
                threshold=None,
            )

        # PRIORITY 2: RULE R7 — REVOKED AGENT
        # Must be checked before normal permission/action rules. Revoked agent never receives ALLOW or ASK CUSTOMER.
        if request.agent_status == AgentStatus.REVOKED:
            return RuleEvaluationResult(
                decision=GatekeeperDecision.BLOCK,
                rule_id=RuleId.R7,
                reason="Customer revocation must immediately override other permissions.",
                threshold=None,
            )

        # PRIORITY 3: RULE R1 — UNKNOWN AGENT
        # Agent not registered for the customer
        if request.agent_status == AgentStatus.UNKNOWN:
            return RuleEvaluationResult(
                decision=GatekeeperDecision.BLOCK,
                rule_id=RuleId.R1,
                reason="Unknown agents should not access the customer's banking account.",
                threshold=None,
            )

        # For remaining rules, agent is ACTIVE and REGISTERED
        action = request.action
        amount = request.amount

        # PRIORITY 4: RULE R2 — REGISTERED READ-ONLY ACCESS
        if action == BankingAction.VIEW_BALANCE:
            return RuleEvaluationResult(
                decision=GatekeeperDecision.ALLOW,
                rule_id=RuleId.R2,
                reason="Viewing the balance is read-only and has lower transaction risk.",
                threshold=None,
            )

        # PRIORITY 5: BILL PAYMENT (RULES R3 & R4)
        if action == BankingAction.PAY_BILL:
            if amount <= self.threshold:
                # RULE R3 — LOW-VALUE BILL PAYMENT
                return RuleEvaluationResult(
                    decision=GatekeeperDecision.ALLOW,
                    rule_id=RuleId.R3,
                    reason="Routine lower-value bill payments can be automated within the prototype threshold.",
                    threshold=self.threshold,
                )
            else:
                # RULE R4 — HIGH-VALUE BILL PAYMENT
                return RuleEvaluationResult(
                    decision=GatekeeperDecision.ASK_CUSTOMER,
                    rule_id=RuleId.R4,
                    reason="A payment above the prototype automatic-payment threshold requires customer confirmation.",
                    threshold=self.threshold,
                )

        # PRIORITY 6: MONEY TRANSFER (RULES R5 & R6)
        if action == BankingAction.TRANSFER_MONEY:
            if amount <= self.threshold:
                # RULE R5 — LOW-VALUE MONEY TRANSFER
                return RuleEvaluationResult(
                    decision=GatekeeperDecision.ASK_CUSTOMER,
                    rule_id=RuleId.R5,
                    reason="Money transfers are more sensitive than read-only access or routine bill payments, so customer confirmation is required even below the threshold.",
                    threshold=self.threshold,
                )
            else:
                # RULE R6 — HIGH-VALUE MONEY TRANSFER
                return RuleEvaluationResult(
                    decision=GatekeeperDecision.BLOCK,
                    rule_id=RuleId.R6,
                    reason="A high-value money transfer presents greater fraud and liability risk in this prototype.",
                    threshold=self.threshold,
                )

        # Fallback for unexpected action (defensive programming)
        return RuleEvaluationResult(
            decision=GatekeeperDecision.BLOCK,
            rule_id=RuleId.R1,
            reason="Unrecognized or unsupported banking action.",
            threshold=None,
        )
