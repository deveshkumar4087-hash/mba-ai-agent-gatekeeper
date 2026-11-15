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


def test_agent_status_fields_active(tmp_path):
    """
    Verify that an ACTIVE agent record returned by DataStore contains all fields
    required by the improved Agent Status tab: customer_id, agent_name, status,
    registered_at, revoked_at (None when active).
    Uses an isolated temp-file DB (consistent with Stage 3 test pattern).
    """
    from services.data_store import DataStore
    ds = DataStore(tmp_path / "status_smoke.db")
    record = ds.register_agent("CUST_STATUS_TEST", "StatusBot", "smoke test")

    assert record["customer_id"] == "CUST_STATUS_TEST"
    assert record["agent_name"] == "StatusBot"
    assert record["status"] == "ACTIVE"
    assert record["registered_at"] is not None
    assert record["revoked_at"] is None


def test_agent_status_fields_after_revocation(tmp_path):
    """
    Verify that after revocation the DataStore record exposes both registered_at
    and revoked_at — the two timestamps shown in the improved Revoke and Status tabs.
    Uses an isolated temp-file DB (consistent with Stage 3 test pattern).
    """
    from services.data_store import DataStore
    ds = DataStore(tmp_path / "revoke_smoke.db")
    ds.register_agent("CUST_REV_TEST", "RevokeBot", "smoke test")
    revoked = ds.revoke_agent("CUST_REV_TEST", "RevokeBot", "testing revocation display")

    assert revoked["status"] == "REVOKED"
    assert revoked["registered_at"] is not None
    assert revoked["revoked_at"] is not None
    # revocation must happen at the same second as or after registration
    assert revoked["revoked_at"] >= revoked["registered_at"]


def test_audit_trail_decision_filter_in_datastore(tmp_path):
    """
    Verify DataStore get_audit_logs properly handles decision filter options
    (ALLOW, ASK CUSTOMER, BLOCK, ALL) used by the improved Audit Trail dashboard tab.
    """
    from services.data_store import DataStore
    ds = DataStore(tmp_path / "audit_smoke.db")

    ds.save_audit_log({
        "customer_id": "CUST1",
        "agent_name": "Bot1",
        "action": "View Balance",
        "amount": 0.0,
        "decision": "ALLOW",
        "rule_id": "R2",
        "reason": "Balance read-only",
    })
    ds.save_audit_log({
        "customer_id": "CUST1",
        "agent_name": "Bot1",
        "action": "Pay Bill",
        "amount": 600.0,
        "decision": "ASK CUSTOMER",
        "rule_id": "R4",
        "reason": "Exceeds threshold",
    })
    ds.save_audit_log({
        "customer_id": "CUST1",
        "agent_name": "GhostBot",
        "action": "Transfer Money",
        "amount": 100.0,
        "decision": "BLOCK",
        "rule_id": "R1",
        "reason": "Unknown agent",
    })

    assert len(ds.get_audit_logs(decision="ALL")) == 3
    assert len(ds.get_audit_logs(decision="ALLOW")) == 1
    assert len(ds.get_audit_logs(decision="ASK CUSTOMER")) == 1
    assert len(ds.get_audit_logs(decision="BLOCK")) == 1
    assert ds.get_audit_logs(decision="BLOCK")[0]["rule_id"] == "R1"
