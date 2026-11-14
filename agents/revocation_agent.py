"""
Revocation Agent Module.

Responsible for handling agent decommissioning and access revocation:
- Marking an AI agent as REVOKED
- Persisting real system UTC revocation timestamp
- Ensuring permanent blocking of revoked agents in subsequent transactions
- Logging revocation events for regulatory compliance

AI Agent Gatekeeper for Banking Transactions
Student Enrolment: PGD202565745
Assigned Domain: Banking
Context: Capital One (Student-designed academic prototype; not official policy).
"""

from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field

from services.data_store import DataStore


class AgentRevocationRequest(BaseModel):
    """Schema for agent revocation request."""
    customer_id: str = Field(..., min_length=1, description="Customer requesting the revocation")
    agent_id: Optional[str] = Field(default=None, description="ID or unique name of the agent to revoke")
    agent_name: Optional[str] = Field(default=None, description="Display name of the agent to revoke")
    reason: Optional[str] = Field(default="Customer request", description="Reason for revoking agent authority")


class RevocationAgent:
    """Agent managing suspension and permanent revocation of AI agents."""

    def __init__(self, data_store: Optional[DataStore] = None) -> None:
        self.data_store = data_store or DataStore()

    def revoke_agent(
        self,
        request: Union[AgentRevocationRequest, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Mark the specified agent as permanently revoked in the persistent DataStore.
        """
        if isinstance(request, dict):
            req = AgentRevocationRequest(**request)
        elif isinstance(request, AgentRevocationRequest):
            req = request
        else:
            raise TypeError(f"Expected AgentRevocationRequest or dict, got {type(request)}")

        agent_target = req.agent_name or req.agent_id
        if not agent_target:
            raise ValueError("Either agent_name or agent_id must be provided for revocation.")

        # If agent_target contains customer prefix (e.g. CUST001_BankBot), parse it
        if "_" in agent_target and agent_target.startswith(f"{req.customer_id}_"):
            agent_target = agent_target[len(req.customer_id) + 1:]

        return self.data_store.revoke_agent(
            customer_id=req.customer_id,
            agent_name=agent_target,
            reason=req.reason or "Customer request",
        )
