"""
Decision Agent Module.

Responsible for orchestrating the policy evaluation for transaction requests:
- Receives transaction context (customer, agent, action, amount, status, rejection flag)
- Consults the RuleEngine to evaluate deterministic policy rules
- Emits structured gatekeeper decisions:
    - ALLOW
    - ASK CUSTOMER
    - BLOCK
- Attaches the applicable rule number (R1 - R8) and justification
"""

from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field

from services.rule_engine import (
    RuleEngine,
    RuleEvaluationRequest,
    RuleEvaluationResult,
    GatekeeperDecision,
    RuleId,
    AgentStatus,
    BankingAction,
)


class TransactionEvaluationRequest(BaseModel):
    """Schema for evaluating an AI agent's banking action."""
    customer_id: str = Field(..., description="Customer identifier")
    agent_name: str = Field(..., description="AI agent initiating transaction")
    action: str = Field(..., description="View Balance | Pay Bill | Transfer Money")
    amount: float = Field(default=0.0, ge=0.0, description="Transaction monetary amount (0.0 for balance view)")
    agent_status: str = Field(default="ACTIVE", description="ACTIVE | REVOKED | UNKNOWN")
    customer_rejected: bool = Field(default=False, description="Customer explicitly rejected request")
    customer_confirmed: Optional[bool] = Field(default=None, description="Customer confirmation flag")


class DecisionAgent:
    """Agent that queries the Rule Engine and synthesizes gatekeeper decisions."""

    def __init__(self, rule_engine: Optional[RuleEngine] = None) -> None:
        self.rule_engine = rule_engine or RuleEngine()

    def evaluate_request(
        self, request: Union[TransactionEvaluationRequest, RuleEvaluationRequest, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate an AI agent banking request and return a structured decision dictionary.
        """
        if isinstance(request, dict):
            req_dict = request
        elif hasattr(request, "model_dump"):
            req_dict = request.model_dump()
        else:
            req_dict = dict(request)

        result: RuleEvaluationResult = self.rule_engine.evaluate(req_dict)
        return result.model_dump()
