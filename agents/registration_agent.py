"""
Registration Agent Module.

Responsible for onboarding personal AI agents acting on behalf of bank customers:
- Capturing agent metadata (agent_id, agent_name, customer_id, description)
- Assigning operational status (ACTIVE)
- Generating real system UTC registration timestamp
- Persisting agent records via DataStore

AI Agent Gatekeeper for Banking Transactions
Student Enrolment: PGD202565745
Assigned Domain: Banking
Context: Capital One (Student-designed academic prototype; not official policy).
"""

from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field

from services.data_store import DataStore


class AgentRegistrationRequest(BaseModel):
    """Schema for incoming agent registration requests."""
    agent_name: str = Field(..., min_length=1, description="Unique display name of the AI agent")
    customer_id: str = Field(..., min_length=1, description="Identifier of the customer delegating authority")
    description: Optional[str] = Field(default="", description="Stated purpose of the AI agent")


class RegistrationAgent:
    """Agent handling the validation and enrollment of customer AI agents."""

    def __init__(self, data_store: Optional[DataStore] = None) -> None:
        self.data_store = data_store or DataStore()

    def register_agent(
        self,
        request: Union[AgentRegistrationRequest, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Validate and register a new personal AI agent in the persistent DataStore.
        """
        if isinstance(request, dict):
            req = AgentRegistrationRequest(**request)
        elif isinstance(request, AgentRegistrationRequest):
            req = request
        else:
            raise TypeError(f"Expected AgentRegistrationRequest or dict, got {type(request)}")

        return self.data_store.register_agent(
            customer_id=req.customer_id,
            agent_name=req.agent_name,
            notes=req.description or "",
        )
