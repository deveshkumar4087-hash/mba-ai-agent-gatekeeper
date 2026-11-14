"""
Streamlit Web Dashboard Smoke Tests (Stage 5).

AI Agent Gatekeeper for Banking Transactions
Student Enrolment Number: PGD202565745
Assigned Business Domain: Banking
Context Reference Institution: Capital One (Student-designed academic prototype; not official policy).

Validates:
- Import integrity of app.py
- Mandatory metadata constants (ENROLMENT_NUMBER, ASSIGNED_DOMAIN, etc.)
- Orchestrator connection to persistent storage
"""

import pytest
from orchestrator import GatekeeperOrchestrator


def test_app_imports_and_constants():
    """Verify app.py imports cleanly and exports required student metadata."""
    import app
    assert hasattr(app, "ENROLMENT_NUMBER")
    assert app.ENROLMENT_NUMBER == "PGD202565745"
    assert "Banking" in app.ASSIGNED_DOMAIN
    assert "AI Agent Gatekeeper" in app.PROJECT_TITLE
    assert "Capital One" in app.REFERENCE_INSTITUTION
    assert "$500" in app.PROTOTYPE_THRESHOLD


def test_app_orchestrator_initialization():
    """Verify that the cached orchestrator factory in app.py returns an initialized instance."""
    from app import get_orchestrator
    orch = get_orchestrator()
    assert isinstance(orch, GatekeeperOrchestrator)
    assert orch.is_initialized is True
    assert orch.data_store is not None
    assert orch.rule_engine is not None
    assert orch.audit_logger is not None
