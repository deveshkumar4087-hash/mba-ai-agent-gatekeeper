"""
Stage 3 End-to-End Pipeline & Persistence Tests.

AI Agent Gatekeeper for Banking Transactions.
Student Enrolment: PGD202565745
Assigned Domain: Banking
Context: Capital One (Student-designed academic prototype; not official policy).

Validates:
- Persistent agent registration
- Persistent agent revocation & timestamps
- PermissionAgent standing verification
- Orchestrator end-to-end evaluation
- Audit logging for all decisions (including unknown and revoked agents)
- SQLite database persistence across component re-instantiation
"""

import pytest
from pathlib import Path
from pydantic import ValidationError

from services.data_store import DataStore
from orchestrator import GatekeeperOrchestrator, TransactionRequest, GatekeeperResponse


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Provides a fresh isolated SQLite file path for testing."""
    return tmp_path / "test_gatekeeper.db"


@pytest.fixture
def orchestrator(temp_db_path: Path) -> GatekeeperOrchestrator:
    """Fixture providing an orchestrator configured with the isolated test database."""
    return GatekeeperOrchestrator(db_path=temp_db_path)


# ==============================================================================
# TESTS A THROUGH J (STAGE 3 MANDATORY REQUIREMENTS)
# ==============================================================================

def test_a_register_agent(orchestrator: GatekeeperOrchestrator):
    """TEST A — Register Agent: CUST001, BankBot -> Expected ACTIVE, verified persisted."""
    reg = orchestrator.register_agent(
        customer_id="CUST001",
        agent_name="BankBot",
        notes="Automated banking assistant",
    )

    assert reg["customer_id"] == "CUST001"
    assert reg["agent_name"] == "BankBot"
    assert reg["status"] == "ACTIVE"
    assert reg["registered_at"] is not None
    assert reg["revoked_at"] is None


def test_b_registered_agent_can_be_found(orchestrator: GatekeeperOrchestrator):
    """TEST B — Registered Agent Can Be Found: Retrieve BankBot for CUST001 -> ACTIVE."""
    orchestrator.register_agent(customer_id="CUST001", agent_name="BankBot")

    agent = orchestrator.data_store.get_agent("CUST001", "BankBot")
    assert agent is not None
    assert agent["status"] == "ACTIVE"
    assert agent["customer_id"] == "CUST001"
    assert agent["agent_name"] == "BankBot"


def test_c_revoke_agent(orchestrator: GatekeeperOrchestrator):
    """TEST C — Revoke Agent: Revoke CUST001, BankBot -> Expected REVOKED, revoked_at populated."""
    orchestrator.register_agent(customer_id="CUST001", agent_name="BankBot")
    rev = orchestrator.revoke_agent(
        customer_id="CUST001",
        agent_name="BankBot",
        reason="Security audit compromise",
    )

    assert rev["status"] == "REVOKED"
    assert rev["revoked_at"] is not None
    assert "Security audit compromise" in rev["notes"]


def test_d_revoked_agent_persists(orchestrator: GatekeeperOrchestrator, temp_db_path: Path):
    """TEST D — Revoked Agent Persists: Status must remain REVOKED across lookups and restarts."""
    orchestrator.register_agent(customer_id="CUST001", agent_name="BankBot")
    orchestrator.revoke_agent(customer_id="CUST001", agent_name="BankBot")

    # Verify immediately
    agent_now = orchestrator.data_store.get_agent("CUST001", "BankBot")
    assert agent_now["status"] == "REVOKED"

    # Simulate application restart with a fresh Orchestrator instance pointing to the same DB
    restarted_orchestrator = GatekeeperOrchestrator(db_path=temp_db_path)
    agent_restarted = restarted_orchestrator.data_store.get_agent("CUST001", "BankBot")

    assert agent_restarted is not None
    assert agent_restarted["status"] == "REVOKED"
    assert agent_restarted["revoked_at"] is not None


def test_e_revoked_agent_request(orchestrator: GatekeeperOrchestrator):
    """TEST E — Revoked Agent Request: CUST001, BankBot, Pay Bill $100 -> BLOCK / R7, audit logged."""
    orchestrator.register_agent(customer_id="CUST001", agent_name="BankBot")
    orchestrator.revoke_agent(customer_id="CUST001", agent_name="BankBot")

    response = orchestrator.evaluate_request(
        customer_id="CUST001",
        agent_name="BankBot",
        action="Pay Bill",
        amount=100.0,
    )

    assert response.decision == "BLOCK"
    assert response.rule_id == "R7"
    assert "revocation must immediately override" in response.reason.lower()

    # Verify audit record was created for the revoked agent request
    logs = orchestrator.audit_logger.get_logs(customer_id="CUST001")
    assert len(logs) >= 1
    last_log = logs[-1]
    assert last_log["decision"] == "BLOCK"
    assert last_log["rule_id"] == "R7"
    assert last_log["agent_name"] == "BankBot"


def test_f_unknown_agent_request(orchestrator: GatekeeperOrchestrator):
    """TEST F — Unknown Agent Request: CUST001, UnknownAI, View Balance -> BLOCK / R1, audit logged."""
    response = orchestrator.evaluate_request(
        customer_id="CUST001",
        agent_name="UnknownAI",
        action="View Balance",
        amount=0.0,
    )

    assert response.decision == "BLOCK"
    assert response.rule_id == "R1"
    assert "unknown agents" in response.reason.lower()

    # Verify audit record created for unknown agent request
    logs = orchestrator.audit_logger.get_logs(customer_id="CUST001")
    assert len(logs) >= 1
    last_log = logs[-1]
    assert last_log["decision"] == "BLOCK"
    assert last_log["rule_id"] == "R1"
    assert last_log["agent_name"] == "UnknownAI"


def test_g_active_agent_end_to_end(orchestrator: GatekeeperOrchestrator):
    """TEST G — Active Agent End-to-End: CUST002, PayPilot, Pay Bill $300 -> ALLOW / R3, audit matches."""
    orchestrator.register_agent(customer_id="CUST002", agent_name="PayPilot")

    response = orchestrator.evaluate_request(
        customer_id="CUST002",
        agent_name="PayPilot",
        action="Pay Bill",
        amount=300.0,
    )

    assert response.decision == "ALLOW"
    assert response.rule_id == "R3"
    assert response.threshold == 500.0

    # Verify audit record contains identical decision and rule
    logs = orchestrator.audit_logger.get_logs(customer_id="CUST002")
    assert len(logs) >= 1
    last_log = logs[-1]
    assert last_log["decision"] == response.decision
    assert last_log["rule_id"] == response.rule_id
    assert last_log["amount"] == 300.0


def test_h_high_value_bill_payment(orchestrator: GatekeeperOrchestrator):
    """TEST H — High-Value Bill: Active PayPilot, Pay Bill $800 -> ASK CUSTOMER / R4, audit logged."""
    orchestrator.register_agent(customer_id="CUST002", agent_name="PayPilot")

    response = orchestrator.evaluate_request(
        customer_id="CUST002",
        agent_name="PayPilot",
        action="Pay Bill",
        amount=800.0,
    )

    assert response.decision == "ASK CUSTOMER"
    assert response.rule_id == "R4"
    assert response.threshold == 500.0

    logs = orchestrator.audit_logger.get_logs(customer_id="CUST002")
    last_log = logs[-1]
    assert last_log["decision"] == "ASK CUSTOMER"
    assert last_log["rule_id"] == "R4"
    assert last_log["amount"] == 800.0


def test_i_low_value_transfer(orchestrator: GatekeeperOrchestrator):
    """TEST I — Transfer: Active PayPilot, Transfer Money $400 -> ASK CUSTOMER / R5, audit logged."""
    orchestrator.register_agent(customer_id="CUST002", agent_name="PayPilot")

    response = orchestrator.evaluate_request(
        customer_id="CUST002",
        agent_name="PayPilot",
        action="Transfer Money",
        amount=400.0,
    )

    assert response.decision == "ASK CUSTOMER"
    assert response.rule_id == "R5"
    assert response.threshold == 500.0

    logs = orchestrator.audit_logger.get_logs(customer_id="CUST002")
    last_log = logs[-1]
    assert last_log["decision"] == "ASK CUSTOMER"
    assert last_log["rule_id"] == "R5"
    assert last_log["amount"] == 400.0


def test_j_audit_persistence(orchestrator: GatekeeperOrchestrator, temp_db_path: Path):
    """TEST J — Audit Persistence: Verify all required fields exist and persist across re-instantiation."""
    orchestrator.register_agent(customer_id="CUST003", agent_name="AuditTester")
    response = orchestrator.evaluate_request(
        customer_id="CUST003",
        agent_name="AuditTester",
        action="View Balance",
        amount=0.0,
    )

    # Re-instantiate orchestrator from the same persistent SQLite database
    restarted = GatekeeperOrchestrator(db_path=temp_db_path)
    logs = restarted.audit_logger.get_logs(customer_id="CUST003")

    assert len(logs) == 1
    log_entry = logs[0]

    # Verify all mandatory audit fields
    assert "audit_id" in log_entry and log_entry["audit_id"] is not None
    assert "timestamp" in log_entry and len(log_entry["timestamp"]) > 0
    assert log_entry["customer_id"] == "CUST003"
    assert log_entry["agent_name"] == "AuditTester"
    assert log_entry["action"] == "View Balance"
    assert log_entry["amount"] == 0.0
    assert log_entry["decision"] == "ALLOW"
    assert log_entry["rule_id"] == "R2"
    assert "read-only" in log_entry["reason"].lower()


# ==============================================================================
# PIPELINE EDGE CASES & INTEGRITY VALIDATIONS
# ==============================================================================

def test_high_value_money_transfer_blocked(orchestrator: GatekeeperOrchestrator):
    """High-value money transfer ($1200) -> BLOCK / R6 end-to-end."""
    orchestrator.register_agent(customer_id="CUST004", agent_name="TransferBot")
    response = orchestrator.evaluate_request(
        customer_id="CUST004",
        agent_name="TransferBot",
        action="Transfer Money",
        amount=1200.0,
    )
    assert response.decision == "BLOCK"
    assert response.rule_id == "R6"


def test_customer_explicit_rejection_in_pipeline(orchestrator: GatekeeperOrchestrator):
    """Explicit customer rejection results in BLOCK / R8 even for low amounts."""
    orchestrator.register_agent(customer_id="CUST005", agent_name="ActiveBot")
    response = orchestrator.evaluate_request(
        customer_id="CUST005",
        agent_name="ActiveBot",
        action="Pay Bill",
        amount=50.0,
        customer_rejected=True,
    )
    assert response.decision == "BLOCK"
    assert response.rule_id == "R8"


def test_validation_empty_customer_or_agent(orchestrator: GatekeeperOrchestrator):
    """Empty customer or agent names must raise validation errors."""
    with pytest.raises(ValidationError):
        orchestrator.evaluate_request(customer_id="", agent_name="Bot", action="View Balance")

    with pytest.raises(ValidationError):
        orchestrator.evaluate_request(customer_id="CUST001", agent_name="", action="View Balance")


def test_validation_negative_amount(orchestrator: GatekeeperOrchestrator):
    """Negative transaction amounts must raise validation error."""
    with pytest.raises(ValidationError):
        orchestrator.evaluate_request(
            customer_id="CUST001",
            agent_name="Bot",
            action="Pay Bill",
            amount=-50.0,
        )


def test_audit_log_filtering_by_decision(orchestrator: GatekeeperOrchestrator):
    """
    Verify persistent audit log query filtering by decision (ALLOW, ASK CUSTOMER, BLOCK, ALL),
    ensuring both unknown-agent (R1) and revoked-agent (R7) decisions are recorded and retrievable.
    """
    cust_id = "CUST_AUDIT_FILTER"
    # 1. ALLOW (R2: active agent view balance)
    orchestrator.register_agent(customer_id=cust_id, agent_name="ActiveBot")
    orchestrator.evaluate_request(customer_id=cust_id, agent_name="ActiveBot", action="View Balance", amount=0.0)

    # 2. ASK CUSTOMER (R4: active agent bill pay > $500)
    orchestrator.evaluate_request(customer_id=cust_id, agent_name="ActiveBot", action="Pay Bill", amount=750.0)

    # 3. BLOCK via Revoked Agent (R7)
    orchestrator.register_agent(customer_id=cust_id, agent_name="RevokedBot")
    orchestrator.revoke_agent(customer_id=cust_id, agent_name="RevokedBot", reason="Compromised credentials")
    orchestrator.evaluate_request(customer_id=cust_id, agent_name="RevokedBot", action="Pay Bill", amount=50.0)

    # 4. BLOCK via Unknown Agent (R1)
    orchestrator.evaluate_request(customer_id=cust_id, agent_name="UnknownGhostBot", action="Transfer Money", amount=20.0)

    # Test ALL filter
    all_logs = orchestrator.audit_logger.get_logs(customer_id=cust_id, decision="ALL")
    assert len(all_logs) == 4

    # Test ALLOW filter
    allow_logs = orchestrator.audit_logger.get_logs(customer_id=cust_id, decision="ALLOW")
    assert len(allow_logs) == 1
    assert allow_logs[0]["decision"] == "ALLOW"
    assert allow_logs[0]["rule_id"] == "R2"

    # Test ASK CUSTOMER filter
    ask_logs = orchestrator.audit_logger.get_logs(customer_id=cust_id, decision="ASK CUSTOMER")
    assert len(ask_logs) == 1
    assert ask_logs[0]["decision"] == "ASK CUSTOMER"
    assert ask_logs[0]["rule_id"] == "R4"

    # Test BLOCK filter: must include BOTH revoked-agent (R7) and unknown-agent (R1)
    block_logs = orchestrator.audit_logger.get_logs(customer_id=cust_id, decision="BLOCK")
    assert len(block_logs) == 2
    block_rules = {log["rule_id"] for log in block_logs}
    assert "R7" in block_rules
    assert "R1" in block_rules


def test_audit_log_filtering_combined_customer_and_decision(orchestrator: GatekeeperOrchestrator):
    """Verify combining customer_id filter with decision filter isolates matching audit entries."""
    orchestrator.register_agent(customer_id="CUST_X", agent_name="BotX")
    orchestrator.register_agent(customer_id="CUST_Y", agent_name="BotY")

    orchestrator.evaluate_request(customer_id="CUST_X", agent_name="BotX", action="View Balance", amount=0.0)
    orchestrator.evaluate_request(customer_id="CUST_Y", agent_name="BotY", action="View Balance", amount=0.0)
    orchestrator.evaluate_request(customer_id="CUST_X", agent_name="BotX", action="Pay Bill", amount=900.0)

    # Customer X + ALLOW -> 1
    x_allow = orchestrator.audit_logger.get_logs(customer_id="CUST_X", decision="ALLOW")
    assert len(x_allow) == 1
    assert x_allow[0]["customer_id"] == "CUST_X"

    # Customer X + ASK CUSTOMER -> 1
    x_ask = orchestrator.audit_logger.get_logs(customer_id="CUST_X", decision="ASK CUSTOMER")
    assert len(x_ask) == 1
    assert x_ask[0]["customer_id"] == "CUST_X"

    # Customer Y + ASK CUSTOMER -> 0
    y_ask = orchestrator.audit_logger.get_logs(customer_id="CUST_Y", decision="ASK CUSTOMER")
    assert len(y_ask) == 0
