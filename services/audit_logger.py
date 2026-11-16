"""
AuditLogger Service Module.

Provides persistent, append-only transaction audit logging for compliance:
- Records timestamp, customer ID, agent name, action, amount, decision, rule ID, reason
- Persistent across program restarts via DataStore SQLite integration
- Immutable append-only audit trail for banking governance

AI Agent Gatekeeper for Banking Transactions
Student Enrolment: PGD202565745
Assigned Domain: Banking
Context: Capital One (Student-designed academic prototype; not official policy).
"""

import csv
import io
from typing import Dict, Any, List, Optional
from pathlib import Path

from services.data_store import DataStore, get_current_utc_timestamp
from services.rule_engine import GatekeeperDecision, RuleId


def format_audit_logs_as_csv(logs: List[Dict[str, Any]]) -> str:
    """
    Format audit log records into standard CSV string.
    Columns: ID, Timestamp, Customer ID, Agent Name, Action, Amount, Decision, Rule ID, Reason.
    """
    headers = [
        "ID",
        "Timestamp",
        "Customer ID",
        "Agent Name",
        "Action",
        "Amount",
        "Decision",
        "Rule ID",
        "Reason",
    ]
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(headers)
    for log in logs:
        amt = float(log.get("amount", 0.0))
        writer.writerow([
            log.get("audit_id", ""),
            log.get("timestamp", ""),
            log.get("customer_id", ""),
            log.get("agent_name", ""),
            log.get("action", ""),
            f"${amt:.2f}",
            log.get("decision", ""),
            log.get("rule_id", "") or log.get("rule_number", ""),
            log.get("reason", ""),
        ])
    return output.getvalue()


class AuditLogger:
    """Manages persistent transaction audit trails."""

    def __init__(
        self,
        data_store: Optional[DataStore] = None,
        log_dir: Optional[Path] = None,
    ) -> None:
        self.data_store = data_store or DataStore()
        self._memory_logs: List[Dict[str, Any]] = []

    def log_event(
        self,
        customer_id: str,
        agent_name: str,
        action: str,
        amount: float,
        decision: str,
        rule_number: str,
        reason: str = "",
        notes: str = "",
    ) -> Dict[str, Any]:
        """
        Record a validated transaction audit log entry persistently.
        """
        c_id = str(customer_id).strip()
        a_name = str(agent_name).strip()
        act = str(action).strip()
        amt = float(amount)
        dec = str(decision).strip()
        rule = str(rule_number).strip()
        rsn = str(reason or notes).strip()

        # Validate decision value
        valid_decisions = [d.value for d in GatekeeperDecision]
        if dec not in valid_decisions:
            raise ValueError(f"Invalid decision '{dec}'. Allowed: {valid_decisions}")

        # Validate rule_id value
        valid_rules = [r.value for r in RuleId]
        if rule not in valid_rules:
            raise ValueError(f"Invalid rule identifier '{rule}'. Allowed: {valid_rules}")

        if amt < 0.0:
            raise ValueError(f"Transaction amount cannot be negative: {amt}")

        timestamp = get_current_utc_timestamp()

        entry = {
            "timestamp": timestamp,
            "customer_id": c_id,
            "agent_name": a_name,
            "action": act,
            "amount": amt,
            "decision": dec,
            "rule_id": rule,
            "rule_number": rule,  # Included for compatibility
            "reason": rsn,
        }

        # Persist to database
        saved = self.data_store.save_audit_log(entry)
        self._memory_logs.append(saved)
        return saved

    def get_logs(
        self,
        customer_id: Optional[str] = None,
        decision: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve persistent audit records with optional customer and decision filters."""
        return self.data_store.get_audit_logs(customer_id=customer_id, decision=decision)

    def export_csv(
        self,
        customer_id: Optional[str] = None,
        decision: Optional[str] = None,
        logs: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Export persistent audit records to RFC 4180 compliant CSV format.
        Uses specified filters or an existing list of log entries.
        """
        if logs is None:
            logs = self.get_logs(customer_id=customer_id, decision=decision)
        return format_audit_logs_as_csv(logs)
