"""
Unit Tests for Deterministic Rule Engine (Stage 2).

AI Agent Gatekeeper for Banking Transactions.
Student Enrolment: PGD202565745
Company Context: Capital One (Student-designed prototype; not official policy).

Validates the 8 deterministic rules, boundary conditions, priority ordering,
and structured outputs.
"""

import pytest
from pydantic import ValidationError

from services.rule_engine import (
    RuleEngine,
    RuleEvaluationRequest,
    RuleEvaluationResult,
    GatekeeperDecision,
    RuleId,
    AgentStatus,
    BankingAction,
    PROTOTYPE_AUTOMATIC_PAYMENT_THRESHOLD,
)
from agents.decision_agent import DecisionAgent, TransactionEvaluationRequest


@pytest.fixture
def rule_engine() -> RuleEngine:
    """Fixture providing a fresh RuleEngine instance with standard prototype threshold ($500)."""
    return RuleEngine()


@pytest.fixture
def decision_agent(rule_engine: RuleEngine) -> DecisionAgent:
    """Fixture providing a DecisionAgent wired to the RuleEngine."""
    return DecisionAgent(rule_engine=rule_engine)


# ==============================================================================
# MANDATORY TESTS 1 THROUGH 6
# ==============================================================================

def test_1_registered_active_view_balance(rule_engine: RuleEngine):
    """TEST 1: Registered active BankBot, View Balance -> ALLOW / R2."""
    req = RuleEvaluationRequest(
        customer_id="CUST-001",
        agent_name="BankBot",
        action=BankingAction.VIEW_BALANCE,
        amount=0.0,
        agent_status=AgentStatus.ACTIVE,
    )
    result = rule_engine.evaluate(req)

    assert result.decision == GatekeeperDecision.ALLOW
    assert result.rule_id == RuleId.R2
    assert "read-only" in result.reason.lower()


def test_2_unknown_agent_view_balance(rule_engine: RuleEngine):
    """TEST 2: Unknown RandomAI, View Balance -> BLOCK / R1."""
    req = RuleEvaluationRequest(
        customer_id="CUST-001",
        agent_name="RandomAI",
        action=BankingAction.VIEW_BALANCE,
        amount=0.0,
        agent_status=AgentStatus.UNKNOWN,
    )
    result = rule_engine.evaluate(req)

    assert result.decision == GatekeeperDecision.BLOCK
    assert result.rule_id == RuleId.R1
    assert "unknown agents" in result.reason.lower()


def test_3_high_value_bill_payment(rule_engine: RuleEngine):
    """TEST 3: Registered active BankBot, Pay Bill $800 -> ASK CUSTOMER / R4."""
    req = RuleEvaluationRequest(
        customer_id="CUST-001",
        agent_name="BankBot",
        action=BankingAction.PAY_BILL,
        amount=800.0,
        agent_status=AgentStatus.ACTIVE,
    )
    result = rule_engine.evaluate(req)

    assert result.decision == GatekeeperDecision.ASK_CUSTOMER
    assert result.rule_id == RuleId.R4
    assert result.threshold == PROTOTYPE_AUTOMATIC_PAYMENT_THRESHOLD
    assert "above the prototype automatic-payment threshold" in result.reason.lower()


def test_4_low_value_bill_payment(rule_engine: RuleEngine):
    """TEST 4: Registered active BankBot, Pay Bill $300 -> ALLOW / R3."""
    req = RuleEvaluationRequest(
        customer_id="CUST-001",
        agent_name="BankBot",
        action=BankingAction.PAY_BILL,
        amount=300.0,
        agent_status=AgentStatus.ACTIVE,
    )
    result = rule_engine.evaluate(req)

    assert result.decision == GatekeeperDecision.ALLOW
    assert result.rule_id == RuleId.R3
    assert result.threshold == PROTOTYPE_AUTOMATIC_PAYMENT_THRESHOLD
    assert "automated within the prototype threshold" in result.reason.lower()


def test_5_revoked_agent_blocked(rule_engine: RuleEngine):
    """TEST 5: Revoked BankBot, Pay Bill $100 -> BLOCK / R7."""
    req = RuleEvaluationRequest(
        customer_id="CUST-001",
        agent_name="BankBot",
        action=BankingAction.PAY_BILL,
        amount=100.0,
        agent_status=AgentStatus.REVOKED,
    )
    result = rule_engine.evaluate(req)

    assert result.decision == GatekeeperDecision.BLOCK
    assert result.rule_id == RuleId.R7
    assert "revocation must immediately override" in result.reason.lower()


def test_6_low_value_money_transfer(rule_engine: RuleEngine):
    """TEST 6: Registered active BankBot, Transfer Money $400 -> ASK CUSTOMER / R5."""
    req = RuleEvaluationRequest(
        customer_id="CUST-001",
        agent_name="BankBot",
        action=BankingAction.TRANSFER_MONEY,
        amount=400.0,
        agent_status=AgentStatus.ACTIVE,
    )
    result = rule_engine.evaluate(req)

    assert result.decision == GatekeeperDecision.ASK_CUSTOMER
    assert result.rule_id == RuleId.R5
    assert result.threshold == PROTOTYPE_AUTOMATIC_PAYMENT_THRESHOLD
    assert "more sensitive" in result.reason.lower()


# ==============================================================================
# BOUNDARY TESTS ($500 THRESHOLD)
# ==============================================================================

def test_boundary_bill_pay_exact_threshold(rule_engine: RuleEngine):
    """Boundary: Pay Bill exactly $500.00 -> ALLOW / R3."""
    req = RuleEvaluationRequest(
        customer_id="CUST-001",
        agent_name="BankBot",
        action="Pay Bill",
        amount=500.00,
        agent_status="ACTIVE",
    )
    result = rule_engine.evaluate(req)

    assert result.decision == GatekeeperDecision.ALLOW
    assert result.rule_id == RuleId.R3


def test_boundary_bill_pay_over_threshold(rule_engine: RuleEngine):
    """Boundary: Pay Bill $500.01 -> ASK CUSTOMER / R4."""
    req = RuleEvaluationRequest(
        customer_id="CUST-001",
        agent_name="BankBot",
        action="Pay Bill",
        amount=500.01,
        agent_status="ACTIVE",
    )
    result = rule_engine.evaluate(req)

    assert result.decision == GatekeeperDecision.ASK_CUSTOMER
    assert result.rule_id == RuleId.R4


def test_boundary_transfer_money_exact_threshold(rule_engine: RuleEngine):
    """Boundary: Transfer Money exactly $500.00 -> ASK CUSTOMER / R5."""
    req = RuleEvaluationRequest(
        customer_id="CUST-001",
        agent_name="BankBot",
        action="Transfer Money",
        amount=500.00,
        agent_status="ACTIVE",
    )
    result = rule_engine.evaluate(req)

    assert result.decision == GatekeeperDecision.ASK_CUSTOMER
    assert result.rule_id == RuleId.R5


def test_boundary_transfer_money_over_threshold(rule_engine: RuleEngine):
    """Boundary: Transfer Money $500.01 -> BLOCK / R6."""
    req = RuleEvaluationRequest(
        customer_id="CUST-001",
        agent_name="BankBot",
        action="Transfer Money",
        amount=500.01,
        agent_status="ACTIVE",
    )
    result = rule_engine.evaluate(req)

    assert result.decision == GatekeeperDecision.BLOCK
    assert result.rule_id == RuleId.R6
    assert "fraud and liability risk" in result.reason.lower()


# ==============================================================================
# PRIORITY & OVERRIDE TESTS (R7, R8)
# ==============================================================================

def test_revoked_agent_cannot_bypass_with_low_amount(rule_engine: RuleEngine):
    """Revoked agent cannot bypass R7 even with tiny amount or view balance."""
    # Low-value bill payment ($10) with revoked status
    res1 = rule_engine.evaluate({
        "customer_id": "CUST-001",
        "agent_name": "BadBot",
        "action": "Pay Bill",
        "amount": 10.0,
        "agent_status": "REVOKED",
    })
    assert res1.decision == GatekeeperDecision.BLOCK
    assert res1.rule_id == RuleId.R7

    # View balance with revoked status
    res2 = rule_engine.evaluate({
        "customer_id": "CUST-001",
        "agent_name": "BadBot",
        "action": "View Balance",
        "amount": 0.0,
        "agent_status": "REVOKED",
    })
    assert res2.decision == GatekeeperDecision.BLOCK
    assert res2.rule_id == RuleId.R7


def test_customer_explicit_rejection_overrides_all(rule_engine: RuleEngine):
    """R8: Explicit customer rejection results in BLOCK / R8, overriding normal allowances."""
    # Even a $10 bill pay that would normally be ALLOW under R3 is BLOCKED under R8
    req = RuleEvaluationRequest(
        customer_id="CUST-001",
        agent_name="BankBot",
        action=BankingAction.PAY_BILL,
        amount=10.0,
        agent_status=AgentStatus.ACTIVE,
        customer_rejected=True,
    )
    result = rule_engine.evaluate(req)

    assert result.decision == GatekeeperDecision.BLOCK
    assert result.rule_id == RuleId.R8
    assert "explicit decision overrides" in result.reason.lower()


def test_priority_rejection_over_revocation(rule_engine: RuleEngine):
    """Priority order check: R8 customer rejection is checked first before R7."""
    req = RuleEvaluationRequest(
        customer_id="CUST-001",
        agent_name="BadBot",
        action=BankingAction.PAY_BILL,
        amount=100.0,
        agent_status=AgentStatus.REVOKED,
        customer_rejected=True,
    )
    result = rule_engine.evaluate(req)
    assert result.decision == GatekeeperDecision.BLOCK
    assert result.rule_id == RuleId.R8


# ==============================================================================
# INPUT VALIDATION & DECISION AGENT INTEGRATION TESTS
# ==============================================================================

def test_negative_amount_raises_validation_error():
    """Negative amounts must be rejected by Pydantic schema validation."""
    with pytest.raises(ValidationError):
        RuleEvaluationRequest(
            customer_id="CUST-001",
            agent_name="BankBot",
            action="Pay Bill",
            amount=-25.0,
        )


def test_decision_agent_integration(decision_agent: DecisionAgent):
    """Verify DecisionAgent delegates cleanly to RuleEngine and returns structured dict."""
    request = TransactionEvaluationRequest(
        customer_id="CUST-001",
        agent_name="BankBot",
        action="Pay Bill",
        amount=250.0,
        agent_status="ACTIVE",
    )
    response = decision_agent.evaluate_request(request)

    assert isinstance(response, dict)
    assert response["decision"] == "ALLOW"
    assert response["rule_id"] == "R3"
    assert response["threshold"] == 500.0
    assert "reason" in response
