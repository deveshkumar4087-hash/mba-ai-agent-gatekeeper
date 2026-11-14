"""
Permission Agent Module.

Responsible for verifying agent credential status and preliminary scope:
- Checks if the AI agent is registered, active, revoked, or unknown via DataStore
- Distinguishes operational status: ACTIVE | REVOKED | UNKNOWN
- Validates banking action against supported set
- Passes status to the pipeline without duplicating Stage 2 rule evaluation logic

AI Agent Gatekeeper for Banking Transactions
Student Enrolment: PGD202565745
Assigned Domain: Banking
Context: Capital One (Student-designed academic prototype; not official policy).
"""

from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field

from services.data_store import DataStore
from services.rule_engine import BankingAction, AgentStatus


class AgentVerificationRequest(BaseModel):
    """Schema for checking agent operational standing."""
    customer_id: str = Field(..., min_length=1, description="Customer on whose behalf the action is taken")
    agent_name: str = Field(..., min_length=1, description="Name of the agent initiating the action")
    action: str = Field(..., min_length=1, description="Banking action: View Balance | Pay Bill | Transfer Money")


class PermissionAgent:
    """Agent validating agent credentials, standing, and baseline permissions."""

    def __init__(self, data_store: Optional[DataStore] = None) -> None:
        self.data_store = data_store or DataStore()

    def verify_agent_standing(
        self,
        request: Union[AgentVerificationRequest, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Check if the agent is registered, active, or revoked in the DataStore.
        Validates action string against supported banking actions.
        Does NOT execute policy rules (RuleEngine owns decision logic).
        """
        if isinstance(request, dict):
            req = AgentVerificationRequest(**request)
        elif isinstance(request, AgentVerificationRequest):
            req = request
        else:
            raise TypeError(f"Expected AgentVerificationRequest or dict, got {type(request)}")

        # Validate action
        normalized_action = BankingAction.from_str(req.action)

        # Retrieve status from DataStore: "ACTIVE" | "REVOKED" | "UNKNOWN"
        raw_status = self.data_store.get_agent_status(req.customer_id, req.agent_name)
        status = AgentStatus.from_str(raw_status)

        return {
            "customer_id": req.customer_id,
            "agent_name": req.agent_name,
            "action": normalized_action.value,
            "status": status.value,
            "is_active": (status == AgentStatus.ACTIVE),
            "is_revoked": (status == AgentStatus.REVOKED),
            "is_unknown": (status == AgentStatus.UNKNOWN),
        }
