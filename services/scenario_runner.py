"""
Coursework Scenario Runner Module.

AI Agent Gatekeeper for Banking Transactions
Student Enrolment Number: PGD202565745
Assigned Business Domain: Banking
Context Reference Institution: Capital One (Student-designed academic prototype; not official policy).

STAGE 4 IMPLEMENTATION:
Executes and validates the six mandatory coursework scenarios:
  - Scenario 1: Known Agent, Read-Only Request (ALLOW / R2)
  - Scenario 2: Unknown Agent (BLOCK / R1)
  - Scenario 3: Payment Above Automatic Threshold $500 (ASK CUSTOMER / R4)
  - Scenario 4: Payment Below Automatic Threshold $500 (ALLOW / R3)
  - Scenario 5: Revoked Agent (BLOCK / R7)
  - Scenario 6: Own Case - Money Transfer <= $500 (ASK CUSTOMER / R5)

Performs automated audit trail verification for all scenarios (including BLOCK decisions).
"""

import sys
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from pathlib import Path
import tempfile

# Ensure project root is in sys.path when executed directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from orchestrator import GatekeeperOrchestrator, GatekeeperResponse
from services.data_store import DataStore


@dataclass
class ScenarioResult:
    """Structured result of a single scenario execution."""
    scenario_number: int
    scenario_name: str
    customer_id: str
    agent_name: str
    action: str
    amount: float
    expected_decision: str
    actual_decision: str
    expected_rule: str
    actual_rule: str
    decision_match: bool
    rule_match: bool
    audit_verified: bool
    overall_pass: bool
    business_reason: str
    audit_id: Optional[int] = None
    timestamp: str = ""


class CourseworkScenarioRunner:
    """
    Executes and verifies the six mandatory coursework scenarios under isolated conditions.
    """

    ENROLMENT_NUMBER: str = "PGD202565745"
    DOMAIN: str = "BANKING"
    PROJECT_TITLE: str = "AI Agent Gatekeeper"

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            # Use isolated temporary database by default for clean test repeatability
            temp_file = tempfile.NamedTemporaryFile(suffix="_scenario_test.db", delete=False)
            temp_file.close()
            self._db_path = temp_file.name
        else:
            self._db_path = db_path

        self.data_store = DataStore(db_path=self._db_path)
        self.orchestrator = GatekeeperOrchestrator(data_store=self.data_store)

    def setup_baseline_state(self) -> None:
        """
        Setup known baseline agents:
          - CUST001 -> BankBot (ACTIVE)
          - CUST002 -> PayPilot (ACTIVE)
          - (RandomAI is intentionally NOT registered to serve as UNKNOWN agent)
        """
        self.orchestrator.register_agent(
            customer_id="CUST001",
            agent_name="BankBot",
            notes="Authorized personal banking assistant",
        )
        self.orchestrator.register_agent(
            customer_id="CUST002",
            agent_name="PayPilot",
            notes="Authorized automated bill payment assistant",
        )

    def _verify_audit_log(
        self,
        customer_id: str,
        agent_name: str,
        action: str,
        amount: float,
        expected_decision: str,
        expected_rule: str,
    ) -> bool:
        """
        Verifies that an audit record matching the transaction was written to persistent storage.
        """
        logs = self.data_store.get_audit_logs(customer_id=customer_id)
        if not logs:
            return False

        # Inspect the latest log for this customer and agent
        matching_logs = [
            l for l in logs
            if l["agent_name"] == agent_name and l["action"] == action
        ]
        if not matching_logs:
            return False

        latest = matching_logs[-1]

        # Verify all mandatory audit fields
        has_timestamp = bool(latest.get("timestamp"))
        matches_cust = (latest.get("customer_id") == customer_id)
        matches_agent = (latest.get("agent_name") == agent_name)
        matches_action = (latest.get("action") == action)
        matches_amount = (float(latest.get("amount", -1)) == float(amount))
        matches_decision = (latest.get("decision") == expected_decision)
        matches_rule = (latest.get("rule_id") == expected_rule)
        has_reason = bool(latest.get("reason"))

        return all([
            has_timestamp,
            matches_cust,
            matches_agent,
            matches_action,
            matches_amount,
            matches_decision,
            matches_rule,
            has_reason,
        ])

    def run_all(self) -> List[ScenarioResult]:
        """
        Execute all six scenarios in strict sequence with isolated state management.
        """
        self.setup_baseline_state()
        results: List[ScenarioResult] = []

        # ======================================================================
        # SCENARIO 1: Known Agent, Read-Only Request
        # ======================================================================
        resp1: GatekeeperResponse = self.orchestrator.evaluate_request(
            customer_id="CUST001",
            agent_name="BankBot",
            action="View Balance",
            amount=0.0,
        )
        audit1_ok = self._verify_audit_log("CUST001", "BankBot", "View Balance", 0.0, "ALLOW", "R2")
        dec1_ok = (resp1.decision == "ALLOW")
        rule1_ok = (resp1.rule_id == "R2")
        results.append(ScenarioResult(
            scenario_number=1,
            scenario_name="Known Agent, Read-Only Request",
            customer_id="CUST001",
            agent_name="BankBot",
            action="View Balance",
            amount=0.0,
            expected_decision="ALLOW",
            actual_decision=resp1.decision,
            expected_rule="R2",
            actual_rule=resp1.rule_id,
            decision_match=dec1_ok,
            rule_match=rule1_ok,
            audit_verified=audit1_ok,
            overall_pass=(dec1_ok and rule1_ok and audit1_ok),
            business_reason="A registered and active agent may perform a read-only balance inquiry.",
            audit_id=resp1.audit_id,
            timestamp=resp1.timestamp,
        ))

        # ======================================================================
        # SCENARIO 2: Unknown Agent
        # ======================================================================
        resp2: GatekeeperResponse = self.orchestrator.evaluate_request(
            customer_id="CUST001",
            agent_name="RandomAI",
            action="View Balance",
            amount=0.0,
        )
        audit2_ok = self._verify_audit_log("CUST001", "RandomAI", "View Balance", 0.0, "BLOCK", "R1")
        dec2_ok = (resp2.decision == "BLOCK")
        rule2_ok = (resp2.rule_id == "R1")
        results.append(ScenarioResult(
            scenario_number=2,
            scenario_name="Unknown Agent",
            customer_id="CUST001",
            agent_name="RandomAI",
            action="View Balance",
            amount=0.0,
            expected_decision="BLOCK",
            actual_decision=resp2.decision,
            expected_rule="R1",
            actual_rule=resp2.rule_id,
            decision_match=dec2_ok,
            rule_match=rule2_ok,
            audit_verified=audit2_ok,
            overall_pass=(dec2_ok and rule2_ok and audit2_ok),
            business_reason="An agent that is not registered for the customer must not access the account.",
            audit_id=resp2.audit_id,
            timestamp=resp2.timestamp,
        ))

        # ======================================================================
        # SCENARIO 3: Payment Above Automatic Threshold ($800 > $500)
        # ======================================================================
        resp3: GatekeeperResponse = self.orchestrator.evaluate_request(
            customer_id="CUST002",
            agent_name="PayPilot",
            action="Pay Bill",
            amount=800.0,
        )
        audit3_ok = self._verify_audit_log("CUST002", "PayPilot", "Pay Bill", 800.0, "ASK CUSTOMER", "R4")
        dec3_ok = (resp3.decision == "ASK CUSTOMER")
        rule3_ok = (resp3.rule_id == "R4")
        results.append(ScenarioResult(
            scenario_number=3,
            scenario_name="Payment Above Automatic Threshold",
            customer_id="CUST002",
            agent_name="PayPilot",
            action="Pay Bill",
            amount=800.0,
            expected_decision="ASK CUSTOMER",
            actual_decision=resp3.decision,
            expected_rule="R4",
            actual_rule=resp3.rule_id,
            decision_match=dec3_ok,
            rule_match=rule3_ok,
            audit_verified=audit3_ok,
            overall_pass=(dec3_ok and rule3_ok and audit3_ok),
            business_reason="Payments above the $500 prototype automatic-payment threshold require customer confirmation.",
            audit_id=resp3.audit_id,
            timestamp=resp3.timestamp,
        ))

        # ======================================================================
        # SCENARIO 4: Payment Below Automatic Threshold ($300 <= $500)
        # ======================================================================
        resp4: GatekeeperResponse = self.orchestrator.evaluate_request(
            customer_id="CUST002",
            agent_name="PayPilot",
            action="Pay Bill",
            amount=300.0,
        )
        audit4_ok = self._verify_audit_log("CUST002", "PayPilot", "Pay Bill", 300.0, "ALLOW", "R3")
        dec4_ok = (resp4.decision == "ALLOW")
        rule4_ok = (resp4.rule_id == "R3")
        results.append(ScenarioResult(
            scenario_number=4,
            scenario_name="Payment Below Automatic Threshold",
            customer_id="CUST002",
            agent_name="PayPilot",
            action="Pay Bill",
            amount=300.0,
            expected_decision="ALLOW",
            actual_decision=resp4.decision,
            expected_rule="R3",
            actual_rule=resp4.rule_id,
            decision_match=dec4_ok,
            rule_match=rule4_ok,
            audit_verified=audit4_ok,
            overall_pass=(dec4_ok and rule4_ok and audit4_ok),
            business_reason="A registered active agent may automatically pay a bill up to and including the $500 prototype threshold.",
            audit_id=resp4.audit_id,
            timestamp=resp4.timestamp,
        ))

        # ======================================================================
        # SCENARIO 5: Revoked Agent
        # State change: Revoke BankBot for CUST001 before transaction
        # ======================================================================
        self.orchestrator.revoke_agent(
            customer_id="CUST001",
            agent_name="BankBot",
            reason="Customer requested revocation prior to Scenario 5 evaluation",
        )
        resp5: GatekeeperResponse = self.orchestrator.evaluate_request(
            customer_id="CUST001",
            agent_name="BankBot",
            action="Pay Bill",
            amount=100.0,
        )
        audit5_ok = self._verify_audit_log("CUST001", "BankBot", "Pay Bill", 100.0, "BLOCK", "R7")
        dec5_ok = (resp5.decision == "BLOCK")
        rule5_ok = (resp5.rule_id == "R7")
        results.append(ScenarioResult(
            scenario_number=5,
            scenario_name="Revoked Agent",
            customer_id="CUST001",
            agent_name="BankBot",
            action="Pay Bill",
            amount=100.0,
            expected_decision="BLOCK",
            actual_decision=resp5.decision,
            expected_rule="R7",
            actual_rule=resp5.rule_id,
            decision_match=dec5_ok,
            rule_match=rule5_ok,
            audit_verified=audit5_ok,
            overall_pass=(dec5_ok and rule5_ok and audit5_ok),
            business_reason="A revoked agent must always be blocked, regardless of the transaction amount.",
            audit_id=resp5.audit_id,
            timestamp=resp5.timestamp,
        ))

        # ======================================================================
        # SCENARIO 6: Own Case - Money Transfer <= $500 ($400)
        # ======================================================================
        resp6: GatekeeperResponse = self.orchestrator.evaluate_request(
            customer_id="CUST002",
            agent_name="PayPilot",
            action="Transfer Money",
            amount=400.0,
        )
        audit6_ok = self._verify_audit_log("CUST002", "PayPilot", "Transfer Money", 400.0, "ASK CUSTOMER", "R5")
        dec6_ok = (resp6.decision == "ASK CUSTOMER")
        rule6_ok = (resp6.rule_id == "R5")
        results.append(ScenarioResult(
            scenario_number=6,
            scenario_name="Own Case: Money Transfer <= $500",
            customer_id="CUST002",
            agent_name="PayPilot",
            action="Transfer Money",
            amount=400.0,
            expected_decision="ASK CUSTOMER",
            actual_decision=resp6.decision,
            expected_rule="R5",
            actual_rule=resp6.rule_id,
            decision_match=dec6_ok,
            rule_match=rule6_ok,
            audit_verified=audit6_ok,
            overall_pass=(dec6_ok and rule6_ok and audit6_ok),
            business_reason="Money transfers are more sensitive than bill payments and require explicit customer confirmation even below $500.",
            audit_id=resp6.audit_id,
            timestamp=resp6.timestamp,
        ))

        return results

    def generate_expected_vs_actual_table(self, results: List[ScenarioResult]) -> str:
        """
        Generate Markdown Expected vs Actual verification table.
        """
        header = (
            "| Scenario | Expected Decision | Actual Decision | Expected Rule | Actual Rule | Audit | Result |\n"
            "|:--------:|:-----------------:|:---------------:|:-------------:|:-----------:|:-----:|:------:|"
        )
        rows = []
        for r in results:
            audit_str = "PASS" if r.audit_verified else "FAIL"
            res_str = "PASS" if r.overall_pass else "FAIL"
            rows.append(
                f"| Scenario {r.scenario_number} "
                f"| {r.expected_decision} "
                f"| {r.actual_decision} "
                f"| {r.expected_rule} "
                f"| {r.actual_rule} "
                f"| {audit_str} "
                f"| **{res_str}** |"
            )
        return header + "\n" + "\n".join(rows)

    def generate_coursework_summary(self, results: List[ScenarioResult]) -> str:
        """
        Generate standardized assignment report output for coursework and screen recording.
        """
        lines = [
            f"ENROLMENT: {self.ENROLMENT_NUMBER}",
            f"DOMAIN: {self.DOMAIN}",
            f"PROJECT: {self.PROJECT_TITLE}",
            "",
        ]
        for r in results:
            status = "PASS" if r.overall_pass else "FAIL"
            lines.append(f"Scenario {r.scenario_number} — {status}")

        lines.append("")
        lines.append("EXPECTED VS ACTUAL VERIFICATION TABLE:")
        lines.append(self.generate_expected_vs_actual_table(results))
        return "\n".join(lines)


if __name__ == "__main__":
    runner = CourseworkScenarioRunner()
    results = runner.run_all()
    print("\n" + "=" * 70)
    print("AI AGENT GATEKEEPER — SIX COURSEWORK SCENARIOS VERIFICATION")
    print("=" * 70)
    print(runner.generate_coursework_summary(results))
    print("=" * 70 + "\n")
