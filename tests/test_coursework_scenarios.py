"""
Automated Pytest Suite for Six Coursework Scenarios (Stage 4).

AI Agent Gatekeeper for Banking Transactions
Student Enrolment Number: PGD202565745
Assigned Business Domain: Banking
Context Reference Institution: Capital One (Student-designed academic prototype; not official policy).

Validates:
- Scenario 1: Known Agent, Read-Only Request -> ALLOW / R2
- Scenario 2: Unknown Agent -> BLOCK / R1
- Scenario 3: Payment Above Automatic Threshold -> ASK CUSTOMER / R4
- Scenario 4: Payment Below Automatic Threshold -> ALLOW / R3
- Scenario 5: Revoked Agent -> BLOCK / R7
- Scenario 6: Own Case - Money Transfer <= $500 -> ASK CUSTOMER / R5
- Audit trail creation and verification for all decisions
- Coursework summary generation
"""

import pytest
from pathlib import Path

from services.scenario_runner import CourseworkScenarioRunner, ScenarioResult


@pytest.fixture
def runner(tmp_path: Path) -> CourseworkScenarioRunner:
    """Fixture providing a CourseworkScenarioRunner instance backed by an isolated temporary database."""
    db_file = tmp_path / "coursework_scenarios_test.db"
    return CourseworkScenarioRunner(db_path=str(db_file))


def test_scenario_1_known_agent_read_only(runner: CourseworkScenarioRunner):
    """
    Scenario 1: Known Agent, Read-Only Request
    Customer: CUST001, Agent: BankBot, Action: View Balance, Amount: 0.0
    Expected: ALLOW / R2
    """
    runner.setup_baseline_state()
    response = runner.orchestrator.evaluate_request(
        customer_id="CUST001",
        agent_name="BankBot",
        action="View Balance",
        amount=0.0,
    )

    assert response.decision == "ALLOW"
    assert response.rule_id == "R2"
    assert runner._verify_audit_log("CUST001", "BankBot", "View Balance", 0.0, "ALLOW", "R2") is True


def test_scenario_2_unknown_agent(runner: CourseworkScenarioRunner):
    """
    Scenario 2: Unknown Agent
    Customer: CUST001, Agent: RandomAI, Action: View Balance, Amount: 0.0
    Expected: BLOCK / R1 (Audit logged)
    """
    runner.setup_baseline_state()
    response = runner.orchestrator.evaluate_request(
        customer_id="CUST001",
        agent_name="RandomAI",
        action="View Balance",
        amount=0.0,
    )

    assert response.decision == "BLOCK"
    assert response.rule_id == "R1"
    assert runner._verify_audit_log("CUST001", "RandomAI", "View Balance", 0.0, "BLOCK", "R1") is True


def test_scenario_3_payment_above_automatic_threshold(runner: CourseworkScenarioRunner):
    """
    Scenario 3: Payment Above Automatic Threshold
    Customer: CUST002, Agent: PayPilot, Action: Pay Bill, Amount: 800.0 (> $500)
    Expected: ASK CUSTOMER / R4
    """
    runner.setup_baseline_state()
    response = runner.orchestrator.evaluate_request(
        customer_id="CUST002",
        agent_name="PayPilot",
        action="Pay Bill",
        amount=800.0,
    )

    assert response.decision == "ASK CUSTOMER"
    assert response.rule_id == "R4"
    assert response.threshold == 500.0
    assert runner._verify_audit_log("CUST002", "PayPilot", "Pay Bill", 800.0, "ASK CUSTOMER", "R4") is True


def test_scenario_4_payment_below_automatic_threshold(runner: CourseworkScenarioRunner):
    """
    Scenario 4: Payment Below Automatic Threshold
    Customer: CUST002, Agent: PayPilot, Action: Pay Bill, Amount: 300.0 (<= $500)
    Expected: ALLOW / R3
    """
    runner.setup_baseline_state()
    response = runner.orchestrator.evaluate_request(
        customer_id="CUST002",
        agent_name="PayPilot",
        action="Pay Bill",
        amount=300.0,
    )

    assert response.decision == "ALLOW"
    assert response.rule_id == "R3"
    assert response.threshold == 500.0
    assert runner._verify_audit_log("CUST002", "PayPilot", "Pay Bill", 300.0, "ALLOW", "R3") is True


def test_scenario_5_revoked_agent(runner: CourseworkScenarioRunner):
    """
    Scenario 5: Revoked Agent
    Customer: CUST001, Agent: BankBot (revoked), Action: Pay Bill, Amount: 100.0
    Expected: BLOCK / R7 (Audit logged)
    """
    runner.setup_baseline_state()
    runner.orchestrator.revoke_agent(
        customer_id="CUST001",
        agent_name="BankBot",
        reason="Revocation test prior to scenario 5",
    )

    response = runner.orchestrator.evaluate_request(
        customer_id="CUST001",
        agent_name="BankBot",
        action="Pay Bill",
        amount=100.0,
    )

    assert response.decision == "BLOCK"
    assert response.rule_id == "R7"
    assert runner._verify_audit_log("CUST001", "BankBot", "Pay Bill", 100.0, "BLOCK", "R7") is True


def test_scenario_6_own_case_money_transfer_below_threshold(runner: CourseworkScenarioRunner):
    """
    Scenario 6: Own Case - Money Transfer <= $500
    Customer: CUST002, Agent: PayPilot, Action: Transfer Money, Amount: 400.0 (<= $500)
    Expected: ASK CUSTOMER / R5
    """
    runner.setup_baseline_state()
    response = runner.orchestrator.evaluate_request(
        customer_id="CUST002",
        agent_name="PayPilot",
        action="Transfer Money",
        amount=400.0,
    )

    assert response.decision == "ASK CUSTOMER"
    assert response.rule_id == "R5"
    assert response.threshold == 500.0
    assert runner._verify_audit_log("CUST002", "PayPilot", "Transfer Money", 400.0, "ASK CUSTOMER", "R5") is True


def test_full_coursework_runner_all_pass(runner: CourseworkScenarioRunner):
    """
    Execute runner.run_all() and verify:
    - Exactly 6 scenarios run in sequential order
    - All 6 scenarios pass decision, rule, and audit verifications
    - Formatted table and summary include required enrolment metadata
    """
    results = runner.run_all()

    assert len(results) == 6
    for idx, r in enumerate(results, start=1):
        assert r.scenario_number == idx
        assert r.decision_match is True
        assert r.rule_match is True
        assert r.audit_verified is True
        assert r.overall_pass is True

    summary = runner.generate_coursework_summary(results)
    assert "ENROLMENT: PGD202565745" in summary
    assert "DOMAIN: BANKING" in summary
    assert "Scenario 1 — PASS" in summary
    assert "Scenario 6 — PASS" in summary
    assert "EXPECTED VS ACTUAL VERIFICATION TABLE:" in summary
