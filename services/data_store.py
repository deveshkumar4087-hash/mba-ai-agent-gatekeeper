"""
DataStore Service Module.

Provides structured, persistent storage using SQLite for:
- Registered AI agents (status: ACTIVE, REVOKED)
- System-generated registration and revocation timestamps
- Immutable transaction audit log entries
- Synthetic customer account records

AI Agent Gatekeeper for Banking Transactions
Student Enrolment: PGD202565745
Assigned Domain: Banking
Context: Capital One (Student-designed academic prototype; not official policy).
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Union


def get_current_utc_timestamp() -> str:
    """Generate system-verified UTC ISO 8601 timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


class DataStore:
    """
    Manages persistent SQLite records for agents, audit logs, and synthetic accounts.
    """

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        if db_path is None:
            default_dir = Path(__file__).resolve().parent.parent / "data"
            default_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = default_dir / "gatekeeper.db"
        elif str(db_path) == ":memory:":
            self.db_path = ":memory:"
        else:
            self.db_path = Path(db_path)
            if self.db_path.parent:
                self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a configured database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize database schema if not present."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Agents table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    registered_at TEXT NOT NULL,
                    revoked_at TEXT,
                    notes TEXT,
                    UNIQUE(customer_id, agent_name)
                )
                """
            )
            # Persistent Audit Log table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    customer_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    amount REAL NOT NULL,
                    decision TEXT NOT NULL,
                    rule_id TEXT NOT NULL,
                    reason TEXT NOT NULL
                )
                """
            )
            # Synthetic Accounts table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    customer_id TEXT PRIMARY KEY,
                    account_type TEXT NOT NULL,
                    synthetic_balance REAL NOT NULL
                )
                """
            )
            conn.commit()

    # =========================================================================
    # AGENT MANAGEMENT
    # =========================================================================

    def register_agent(
        self,
        customer_id: str,
        agent_name: str,
        notes: str = "",
    ) -> Dict[str, Any]:
        """
        Register a new AI agent for a customer with ACTIVE status and current UTC timestamp.
        If agent already revoked, preserves revocation to prevent accidental re-activation.
        """
        c_id = customer_id.strip()
        a_name = agent_name.strip()
        if not c_id:
            raise ValueError("customer_id cannot be empty.")
        if not a_name:
            raise ValueError("agent_name cannot be empty.")

        existing = self.get_agent(c_id, a_name)
        if existing:
            if existing["status"] == "REVOKED":
                # Revoked agent cannot automatically become active again
                raise ValueError(
                    f"Agent '{a_name}' for customer '{c_id}' was previously REVOKED "
                    f"at {existing['revoked_at']} and cannot automatically be reactivated."
                )
            return existing

        agent_id = f"{c_id}_{a_name}"
        registered_at = get_current_utc_timestamp()
        status = "ACTIVE"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO agents (agent_id, customer_id, agent_name, status, registered_at, revoked_at, notes)
                VALUES (?, ?, ?, ?, ?, NULL, ?)
                """,
                (agent_id, c_id, a_name, status, registered_at, notes),
            )
            conn.commit()

        return {
            "agent_id": agent_id,
            "customer_id": c_id,
            "agent_name": a_name,
            "status": status,
            "registered_at": registered_at,
            "revoked_at": None,
            "notes": notes,
        }

    def get_agent(
        self,
        customer_id_or_name: str,
        agent_name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve an agent record.
        Supports both (customer_id, agent_name) and single agent_name lookup for compatibility.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if agent_name is not None:
                cursor.execute(
                    "SELECT * FROM agents WHERE customer_id = ? AND agent_name = ?",
                    (customer_id_or_name.strip(), agent_name.strip()),
                )
            else:
                cursor.execute(
                    "SELECT * FROM agents WHERE agent_name = ? ORDER BY registered_at DESC LIMIT 1",
                    (customer_id_or_name.strip(),),
                )
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def get_agent_status(self, customer_id: str, agent_name: str) -> str:
        """
        Determine operational status of an agent for a customer:
        Returns: 'ACTIVE' | 'REVOKED' | 'UNKNOWN'
        """
        agent = self.get_agent(customer_id, agent_name)
        if not agent:
            return "UNKNOWN"
        return str(agent["status"]).upper()

    def revoke_agent(
        self,
        customer_id: str,
        agent_name: str,
        reason: str = "Customer requested revocation",
    ) -> Dict[str, Any]:
        """
        Permanently revoke an agent's authority.
        Sets status to REVOKED and records the current system timestamp.
        """
        c_id = customer_id.strip()
        a_name = agent_name.strip()
        if not c_id:
            raise ValueError("customer_id cannot be empty.")
        if not a_name:
            raise ValueError("agent_name cannot be empty.")

        existing = self.get_agent(c_id, a_name)
        if not existing:
            raise ValueError(f"Agent '{a_name}' not registered for customer '{c_id}'.")

        # If already revoked, keep existing revocation timestamp
        if existing["status"] == "REVOKED":
            return existing

        revoked_at = get_current_utc_timestamp()
        status = "REVOKED"
        combined_notes = f"{existing['notes']} | Revocation reason: {reason}".strip(" | ")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE agents
                SET status = ?, revoked_at = ?, notes = ?
                WHERE customer_id = ? AND agent_name = ?
                """,
                (status, revoked_at, combined_notes, c_id, a_name),
            )
            conn.commit()

        return {
            "agent_id": existing["agent_id"],
            "customer_id": c_id,
            "agent_name": a_name,
            "status": status,
            "registered_at": existing["registered_at"],
            "revoked_at": revoked_at,
            "notes": combined_notes,
        }

    def list_agents(self, customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all agents, optionally filtered by customer_id."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if customer_id:
                cursor.execute(
                    "SELECT * FROM agents WHERE customer_id = ? ORDER BY registered_at ASC",
                    (customer_id.strip(),),
                )
            else:
                cursor.execute("SELECT * FROM agents ORDER BY registered_at ASC")
            return [dict(row) for row in cursor.fetchall()]

    # =========================================================================
    # AUDIT LOGGING
    # =========================================================================

    def save_audit_log(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Persistently save an immutable transaction audit log record.
        """
        timestamp = entry.get("timestamp") or get_current_utc_timestamp()
        customer_id = str(entry["customer_id"]).strip()
        agent_name = str(entry["agent_name"]).strip()
        action = str(entry["action"]).strip()
        amount = float(entry.get("amount", 0.0))
        decision = str(entry["decision"]).strip()
        rule_id = str(entry.get("rule_id") or entry.get("rule_number", "")).strip()
        reason = str(entry.get("reason", "")).strip()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_logs (
                    timestamp, customer_id, agent_name, action, amount, decision, rule_id, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (timestamp, customer_id, agent_name, action, amount, decision, rule_id, reason),
            )
            audit_id = cursor.lastrowid
            conn.commit()

        saved = dict(entry)
        saved["audit_id"] = audit_id
        saved["timestamp"] = timestamp
        return saved

    def get_audit_logs(
        self,
        customer_id: Optional[str] = None,
        decision: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve historical audit records sorted chronologically with optional filters."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM audit_logs"
            conditions: List[str] = []
            params: list = []
            if customer_id and customer_id.strip():
                conditions.append("customer_id = ?")
                params.append(customer_id.strip())
            if decision and decision.strip() and decision.strip().upper() != "ALL":
                conditions.append("decision = ?")
                params.append(decision.strip().upper())
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY audit_id ASC"
            if limit:
                query += " LIMIT ?"
                params.append(int(limit))

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    # =========================================================================
    # SYNTHETIC ACCOUNTS
    # =========================================================================

    def get_account_balance(self, customer_id: str) -> float:
        """Retrieve synthetic customer balance (defaults to 5000.0 USD)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT synthetic_balance FROM accounts WHERE customer_id = ?", (customer_id.strip(),))
            row = cursor.fetchone()
            if row:
                return float(row["synthetic_balance"])
            # Default synthetic baseline
            return 5000.0
