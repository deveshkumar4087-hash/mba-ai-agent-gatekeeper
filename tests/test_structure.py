"""
Sanity tests verifying Stage 1 project structure and interfaces.
Does not test business rules (which are deferred to later stages).
"""

import pytest


def test_student_metadata_in_app():
    """Verify that student enrolment number is properly configured."""
    from app import ENROLMENT_NUMBER, ASSIGNED_DOMAIN
    assert ENROLMENT_NUMBER == "PGD202565745"
    assert "Banking" in ASSIGNED_DOMAIN


def test_agent_modules_importable():
    """Verify all planned agent modules exist and can be imported."""
    from agents.registration_agent import RegistrationAgent, AgentRegistrationRequest
    from agents.revocation_agent import RevocationAgent, AgentRevocationRequest
    from agents.permission_agent import PermissionAgent, AgentVerificationRequest
    from agents.decision_agent import DecisionAgent, GatekeeperDecision, TransactionEvaluationRequest
    from agents.audit_agent import AuditAgent, AuditRecord

    assert RegistrationAgent is not None
    assert RevocationAgent is not None
    assert PermissionAgent is not None
    assert DecisionAgent is not None
    assert AuditAgent is not None
    assert GatekeeperDecision.ALLOW == "ALLOW"
    assert GatekeeperDecision.ASK_CUSTOMER == "ASK CUSTOMER"
    assert GatekeeperDecision.BLOCK == "BLOCK"


def test_service_modules_importable():
    """Verify all planned service modules exist and can be imported."""
    from services.data_store import DataStore
    from services.rule_engine import RuleEngine
    from services.audit_logger import AuditLogger

    ds = DataStore()
    re = RuleEngine()
    al = AuditLogger()

    assert ds is not None
    assert re is not None
    assert al is not None


def test_orchestrator_module_importable():
    """Verify orchestrator skeleton and schemas."""
    from orchestrator import GatekeeperOrchestrator, TransactionRequest, GatekeeperResponse

    orch = GatekeeperOrchestrator()
    assert orch.is_initialized is True
