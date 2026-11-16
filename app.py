"""
AI Agent Gatekeeper for Banking Transactions - Streamlit Web Dashboard.

Student Enrolment Number: PGD202565745
Assigned Business Domain: Banking
Context Reference Institution: Capital One (Background context only;
student-designed academic prototype, NOT an official Capital One system or policy).

Academic Prototype — Stage 5 Demonstration Interface.
Connects directly to the deterministic backend without duplicating business rules.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import streamlit as st
import pandas as pd

# Ensure repository root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from orchestrator import GatekeeperOrchestrator, GatekeeperResponse
from services.scenario_runner import CourseworkScenarioRunner, ScenarioResult
from services.audit_logger import format_audit_logs_as_csv

# Mandatory Metadata Exports (Required for automated tests & student grading)
ENROLMENT_NUMBER: str = "PGD202565745"
ASSIGNED_DOMAIN: str = "Banking (Last digit 5)"
PROJECT_TITLE: str = "AI Agent Gatekeeper for Banking Transactions"
REFERENCE_INSTITUTION: str = "Capital One (Academic Context Only)"
PROTOTYPE_THRESHOLD: str = "Prototype automatic-payment threshold: $500"


@st.cache_resource
def get_orchestrator() -> GatekeeperOrchestrator:
    """Initialize and cache the singleton GatekeeperOrchestrator instance."""
    return GatekeeperOrchestrator()


def main() -> None:
    st.set_page_config(
        page_title="AI Agent Gatekeeper - PGD202565745",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    orchestrator = get_orchestrator()

    # =========================================================================
    # SIDEBAR: Student Credentials & Responsible Disclosure
    # =========================================================================
    with st.sidebar:
        st.header("🎓 Student Identification")
        st.markdown(f"**Enrolment No:** `{ENROLMENT_NUMBER}`")
        st.markdown(f"**Assigned Domain:** `{ASSIGNED_DOMAIN}`")
        st.markdown(f"**Reference Context:** {REFERENCE_INSTITUTION}")
        st.markdown(f"**Rule Threshold:** {PROTOTYPE_THRESHOLD}")
        st.divider()

        st.subheader("⚠️ Responsible Disclosure")
        st.warning(
            "Student-designed academic prototype. "
            "Not an official Capital One system or policy. "
            "All rules, thresholds, customers, and transactions are synthetic."
        )

        st.divider()
        st.caption("AI Agent Gatekeeper Prototype • Stage 5 Complete")

    # =========================================================================
    # HEADER & HERO BANNER
    # =========================================================================
    st.title("🛡️ AI Agent Gatekeeper")
    st.subheader("Banking Transaction Governance Prototype")

    meta_col1, meta_col2, meta_col3 = st.columns(3)
    with meta_col1:
        st.info(f"**Student Enrolment No:** `{ENROLMENT_NUMBER}`")
    with meta_col2:
        st.info(f"**Assigned Domain:** `{ASSIGNED_DOMAIN}`")
    with meta_col3:
        st.info("**Academic Prototype:** Not an Official Capital One System")

    st.markdown(
        """
        > **Mandatory Academic Notice:**
        > Student-designed academic prototype. Not an official Capital One system or policy.
        > All rules, thresholds, customers, and transactions are synthetic.
        """
    )

    # =========================================================================
    # MAIN NAVIGATION TABS
    # =========================================================================
    tabs = st.tabs([
        "💳 Evaluate Request",
        "🤖 Agent Registration",
        "🚫 Revoke Agent",
        "🔍 Agent Status",
        "🧪 Coursework Verification",
        "📜 Audit Trail",
    ])

    # -------------------------------------------------------------------------
    # TAB 1: EVALUATE AI AGENT REQUEST
    # -------------------------------------------------------------------------
    with tabs[0]:
        st.header("Evaluate AI Agent Request")
        st.caption("Submit an autonomous agent transaction for deterministic gatekeeper policy evaluation.")

        col_input1, col_input2 = st.columns(2)
        with col_input1:
            eval_customer_id = st.text_input(
                "Customer ID",
                value="CUST002",
                help="Identifier for the customer (e.g. CUST001, CUST002)",
                key="eval_cust_id",
            )
            eval_agent_name = st.text_input(
                "Agent Name",
                value="PayPilot",
                help="Name of the personal AI agent (e.g. BankBot, PayPilot, RandomAI)",
                key="eval_agent_name",
            )

        with col_input2:
            eval_action = st.selectbox(
                "Action",
                options=["View Balance", "Pay Bill", "Transfer Money"],
                index=1,
                help="Requested banking operation",
                key="eval_action",
            )
            eval_amount = st.number_input(
                "Amount ($)",
                min_value=0.0,
                value=0.0 if eval_action == "View Balance" else 300.0,
                step=10.0,
                format="%.2f",
                disabled=(eval_action == "View Balance"),
                help="Transaction monetary amount. 0.0 for View Balance.",
                key="eval_amount",
            )

        eval_customer_rejected = st.checkbox(
            "Customer explicitly rejected this request",
            value=False,
            help="Simulates customer manual refusal/override (Rule R8)",
            key="eval_rejected",
        )

        if st.button("Evaluate Request", type="primary", key="btn_eval_request"):
            try:
                # Basic input validation
                if not eval_customer_id.strip():
                    st.error("Error: Customer ID cannot be empty.")
                elif not eval_agent_name.strip():
                    st.error("Error: Agent Name cannot be empty.")
                else:
                    # Call the existing GatekeeperOrchestrator backend
                    response: GatekeeperResponse = orchestrator.evaluate_request(
                        customer_id=eval_customer_id.strip(),
                        agent_name=eval_agent_name.strip(),
                        action=eval_action,
                        amount=float(eval_amount),
                        customer_rejected=eval_customer_rejected,
                    )

                    st.markdown("---")
                    st.subheader("Gatekeeper Decision Outcome")

                    res_col1, res_col2, res_col3 = st.columns(3)
                    with res_col1:
                        # Highlight decision prominently in text
                        if response.decision == "ALLOW":
                            st.success(f"### Decision: {response.decision}")
                        elif response.decision == "ASK CUSTOMER":
                            st.warning(f"### Decision: {response.decision}")
                        else:
                            st.error(f"### Decision: {response.decision}")

                    with res_col2:
                        st.info(f"### Applicable Rule: `{response.rule_id}`")

                    with res_col3:
                        st.metric(
                            label="Transaction Amount",
                            value=f"${response.amount:.2f}",
                            delta="Read-Only" if response.action == "View Balance" else None,
                        )

                    st.markdown(f"**Risk Rationale / Reason:** {response.reason}")

                    with st.expander("Transaction & Audit Details", expanded=True):
                        det_col1, det_col2, det_col3 = st.columns(3)
                        det_col1.write(f"**Customer ID:** `{response.customer_id}`")
                        det_col1.write(f"**AI Agent:** `{response.agent_name}`")
                        det_col2.write(f"**Action:** `{response.action}`")
                        det_col2.write(f"**Amount:** `${response.amount:.2f}`")
                        det_col3.write(f"**Timestamp:** `{response.timestamp}`")
                        det_col3.write(f"**Persistent Audit ID:** `#{response.audit_id}`")

            except Exception as ex:
                st.error(f"Evaluation Error: {str(ex)}")

    # -------------------------------------------------------------------------
    # TAB 2: AGENT REGISTRATION
    # -------------------------------------------------------------------------
    with tabs[1]:
        st.header("Register AI Agent")
        st.caption("Enroll a new personal AI agent with ACTIVE operational status in persistent SQLite storage.")

        with st.form("register_agent_form"):
            reg_customer_id = st.text_input("Customer ID", value="CUST001", key="reg_cust_id")
            reg_agent_name = st.text_input("Agent Name", placeholder="e.g. BudgetAssistant", key="reg_agent_name")
            reg_notes = st.text_input("Purpose / Notes", placeholder="e.g. Routine bill payment automation", key="reg_notes")
            submit_reg = st.form_submit_button("Register Agent", type="primary")

        if submit_reg:
            if not reg_customer_id.strip() or not reg_agent_name.strip():
                st.error("Error: Both Customer ID and Agent Name are required.")
            else:
                try:
                    reg_result = orchestrator.register_agent(
                        customer_id=reg_customer_id.strip(),
                        agent_name=reg_agent_name.strip(),
                        notes=reg_notes.strip(),
                    )
                    st.success(f"Agent '{reg_result['agent_name']}' successfully registered for customer '{reg_result['customer_id']}'!")
                    st.write(f"**Operational Status:** `{reg_result['status']}`")
                    st.write(f"**Registration Timestamp (UTC):** `{reg_result['registered_at']}`")
                except ValueError as val_err:
                    st.error(f"Registration Denied: {str(val_err)}")
                except Exception as ex:
                    st.error(f"Unexpected Registration Error: {str(ex)}")

    # -------------------------------------------------------------------------
    # TAB 3: REVOKE AI AGENT
    # -------------------------------------------------------------------------
    with tabs[2]:
        st.header("Revoke AI Agent")
        st.caption("Permanently de-authorize a compromised or unwanted personal AI agent. Persisted across restarts.")

        with st.form("revoke_agent_form"):
            rev_customer_id = st.text_input("Customer ID", value="CUST001", key="rev_cust_id")
            rev_agent_name = st.text_input("Agent Name to Revoke", placeholder="e.g. BankBot", key="rev_agent_name")
            rev_reason = st.text_input("Revocation Reason", value="Customer requested revocation", key="rev_reason")
            submit_rev = st.form_submit_button("Revoke Agent", type="primary")

        if submit_rev:
            if not rev_customer_id.strip() or not rev_agent_name.strip():
                st.error("Error: Both Customer ID and Agent Name are required.")
            else:
                try:
                    rev_result = orchestrator.revoke_agent(
                        customer_id=rev_customer_id.strip(),
                        agent_name=rev_agent_name.strip(),
                        reason=rev_reason.strip(),
                    )
                    st.error(
                        f"🚫 Agent **'{rev_result['agent_name']}'** for customer "
                        f"**'{rev_result['customer_id']}'** is now PERMANENTLY REVOKED."
                    )
                    st.markdown("---")
                    # Structured post-revocation status display
                    rev_col1, rev_col2, rev_col3 = st.columns(3)
                    with rev_col1:
                        st.metric(label="Customer ID", value=rev_result["customer_id"])
                    with rev_col2:
                        st.metric(label="Agent Name", value=rev_result["agent_name"])
                    with rev_col3:
                        st.metric(label="Current Status", value=rev_result["status"])

                    ts_col1, ts_col2 = st.columns(2)
                    with ts_col1:
                        st.info(f"**Registered At (UTC):** `{rev_result['registered_at']}`")
                    with ts_col2:
                        st.info(f"**Revoked At (UTC):** `{rev_result['revoked_at']}`")

                    if rev_result.get("notes"):
                        st.caption(f"Audit Notes: {rev_result['notes']}")
                    st.warning(
                        "⚠️ All subsequent requests from this agent will be permanently "
                        "**BLOCKED** under Rule **R7** (Revoked Agent), regardless of action type or amount."
                    )
                except ValueError as val_err:
                    st.error(f"Revocation Error: {str(val_err)}")
                except Exception as ex:
                    st.error(f"Unexpected Error: {str(ex)}")

    # -------------------------------------------------------------------------
    # TAB 4: AGENT STATUS INSPECTION
    # -------------------------------------------------------------------------
    with tabs[3]:
        st.header("Agent Status Inspection")
        st.caption("Inspect real-time standing of an AI agent in the persistent SQLite registry.")

        status_col1, status_col2 = st.columns(2)
        with status_col1:
            check_customer_id = st.text_input("Customer ID", value="CUST001", key="check_cust_id")
        with status_col2:
            check_agent_name = st.text_input("Agent Name", value="BankBot", key="check_agent_name")

        if st.button("Check Status", key="btn_check_status"):
            if not check_customer_id.strip() or not check_agent_name.strip():
                st.error("Error: Please provide Customer ID and Agent Name.")
            else:
                agent_record = orchestrator.data_store.get_agent(
                    check_customer_id.strip(),
                    check_agent_name.strip(),
                )
                if not agent_record:
                    # UNKNOWN — not in registry
                    st.markdown("---")
                    uk_col1, uk_col2, uk_col3 = st.columns(3)
                    with uk_col1:
                        st.metric(label="Customer ID", value=check_customer_id.strip())
                    with uk_col2:
                        st.metric(label="Agent Name", value=check_agent_name.strip())
                    with uk_col3:
                        st.metric(label="Status", value="UNKNOWN")
                    st.error(
                        f"Agent **'{check_agent_name.strip()}'** is **not registered** "
                        f"for customer **'{check_customer_id.strip()}'**."
                    )
                    st.info("Any action by this agent will trigger Rule **R1** → Decision: **BLOCK**.")
                else:
                    status = agent_record["status"]
                    st.markdown("---")
                    # Top row: Customer ID | Agent Name | Status
                    s_col1, s_col2, s_col3 = st.columns(3)
                    with s_col1:
                        st.metric(label="Customer ID", value=agent_record["customer_id"])
                    with s_col2:
                        st.metric(label="Agent Name", value=agent_record["agent_name"])
                    with s_col3:
                        st.metric(label="Status", value=status)

                    # Status banner
                    if status == "ACTIVE":
                        st.success(
                            f"✅ **ACTIVE** — Agent '{agent_record['agent_name']}' is fully authorized "
                            f"for customer '{agent_record['customer_id']}'."
                        )
                    else:
                        st.error(
                            f"🚫 **REVOKED** — Agent '{agent_record['agent_name']}' authority has been "
                            f"permanently revoked. All requests will be BLOCKED (Rule R7)."
                        )

                    # Timestamps row
                    ts_col1, ts_col2 = st.columns(2)
                    with ts_col1:
                        st.info(f"**Registered At (UTC):** `{agent_record['registered_at']}`")
                    with ts_col2:
                        revoked_at = agent_record.get("revoked_at")
                        if revoked_at:
                            st.info(f"**Revoked At (UTC):** `{revoked_at}`")
                        else:
                            st.info("**Revoked At (UTC):** —  *(not revoked)*")

                    # Notes (if present)
                    if agent_record.get("notes"):
                        st.caption(f"Notes: {agent_record['notes']}")
                    st.caption(f"Internal Agent ID: `{agent_record['agent_id']}`")

    # -------------------------------------------------------------------------
    # TAB 5: COURSEWORK VERIFICATION (SIX SCENARIOS)
    # -------------------------------------------------------------------------
    with tabs[4]:
        st.header("Coursework Verification: Six Mandatory Scenarios")
        st.caption("Executes the complete test suite of six coursework scenarios under isolated conditions.")

        st.markdown(
            """
            Click below to execute the 6 academic test scenarios against the deterministic backend:
            1. **Known BankBot** → View Balance → $0 → `ALLOW` / `R2`
            2. **Unknown RandomAI** → View Balance → $0 → `BLOCK` / `R1`
            3. **PayPilot** → Pay Bill → $800 → `ASK CUSTOMER` / `R4`
            4. **PayPilot** → Pay Bill → $300 → `ALLOW` / `R3`
            5. **Revoked BankBot** → Pay Bill → $100 → `BLOCK` / `R7`
            6. **PayPilot** → Transfer Money → $400 → `ASK CUSTOMER` / `R5`
            """
        )

        if st.button("Run Six Coursework Scenarios", type="primary", key="btn_run_scenarios"):
            with st.spinner("Executing scenarios through CourseworkScenarioRunner..."):
                runner = CourseworkScenarioRunner()
                results: List[ScenarioResult] = runner.run_all()

                all_passed = all(r.overall_pass for r in results)
                if all_passed:
                    st.success("### ✅ All Six Coursework Scenarios PASSED")
                else:
                    st.error("### ❌ Some Coursework Scenarios FAILED")

                # Format DataFrame for table display
                table_data = []
                for r in results:
                    table_data.append({
                        "Scenario": f"Scenario {r.scenario_number}",
                        "Name": r.scenario_name,
                        "Customer": r.customer_id,
                        "Agent": r.agent_name,
                        "Action": r.action,
                        "Amount": f"${r.amount:.2f}",
                        "Expected Decision": r.expected_decision,
                        "Actual Decision": r.actual_decision,
                        "Expected Rule": r.expected_rule,
                        "Actual Rule": r.actual_rule,
                        "Audit Verified": "PASS" if r.audit_verified else "FAIL",
                        "Result": "PASS" if r.overall_pass else "FAIL",
                    })

                df_scenarios = pd.DataFrame(table_data)
                st.dataframe(df_scenarios, use_container_width=True)

                with st.expander("Summary Text for Assignment Report / Recording", expanded=True):
                    st.code(runner.generate_coursework_summary(results), language="text")

    # -------------------------------------------------------------------------
    # TAB 6: PERSISTENT AUDIT TRAIL
    # -------------------------------------------------------------------------
    with tabs[5]:
        st.header("Persistent Audit Trail & Compliance Log")
        st.caption("Immutable transaction records loaded directly from the persistent SQLite audit_logs table.")

        col_audit_btn, col_audit_cust, col_audit_dec = st.columns([1, 2, 2])
        with col_audit_btn:
            refresh_audit = st.button("🔄 Refresh Audit Log", key="btn_refresh_audit")
        with col_audit_cust:
            filter_cust = st.text_input("Filter by Customer ID (Optional)", value="", key="filter_cust")
        with col_audit_dec:
            filter_decision = st.selectbox(
                "Filter by Decision",
                options=["ALL", "ALLOW", "ASK CUSTOMER", "BLOCK"],
                index=0,
                key="filter_decision",
                help="Filter audit entries by gatekeeper decision outcome",
            )

        logs = orchestrator.audit_logger.get_logs(
            customer_id=filter_cust.strip() if filter_cust.strip() else None,
            decision=filter_decision.strip() if filter_decision != "ALL" else None,
        )

        if not logs:
            st.info("No audit logs found matching criteria. Submit transactions in Tab 1 to generate audit records.")
            st.download_button(
                label="📥 Download Audit Trail CSV",
                data=format_audit_logs_as_csv([]),
                file_name="audit_trail_empty.csv",
                mime="text/csv",
                disabled=True,
                key="btn_download_empty",
                help="No matching audit records to export",
            )
        else:
            # Summary Metrics for rapid demonstration & review
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            total_count = len(logs)
            allow_count = sum(1 for log in logs if log.get("decision") == "ALLOW")
            ask_count = sum(1 for log in logs if log.get("decision") == "ASK CUSTOMER")
            block_count = sum(1 for log in logs if log.get("decision") == "BLOCK")

            with m_col1:
                st.metric("Total Records", total_count)
            with m_col2:
                st.metric("ALLOW Decisions", allow_count)
            with m_col3:
                st.metric("ASK CUSTOMER", ask_count)
            with m_col4:
                st.metric("BLOCK Decisions", block_count)

            # Audit Trail Export Button and Status
            csv_data = orchestrator.audit_logger.export_csv(logs=logs)
            export_col1, export_col2 = st.columns([1, 3])
            with export_col1:
                st.download_button(
                    label="📥 Download Audit Trail CSV",
                    data=csv_data,
                    file_name="audit_trail_export.csv",
                    mime="text/csv",
                    key="btn_download_audit_csv",
                    help="Download the filtered audit trail as an RFC 4180 CSV file",
                )
            with export_col2:
                filter_desc = []
                if filter_cust.strip():
                    filter_desc.append(f"Customer: '{filter_cust.strip()}'")
                if filter_decision != "ALL":
                    filter_desc.append(f"Decision: '{filter_decision}'")
                applied_filters_text = ", ".join(filter_desc) if filter_desc else "All Records"
                st.caption(f"Ready to export {total_count} record(s) matching filter: **{applied_filters_text}**.")

            df_logs = pd.DataFrame(logs)
            if "amount" in df_logs.columns:
                df_logs["formatted_amount"] = df_logs["amount"].apply(lambda a: f"${float(a):.2f}")
            else:
                df_logs["formatted_amount"] = "$0.00"

            cols_order = [
                "audit_id",
                "timestamp",
                "customer_id",
                "agent_name",
                "action",
                "formatted_amount",
                "decision",
                "rule_id",
                "reason",
            ]
            available_cols = [c for c in cols_order if c in df_logs.columns]
            df_display = df_logs[available_cols].rename(columns={
                "audit_id": "ID",
                "timestamp": "Timestamp",
                "customer_id": "Customer ID",
                "agent_name": "Agent Name",
                "action": "Action",
                "formatted_amount": "Amount",
                "decision": "Decision",
                "rule_id": "Rule ID",
                "reason": "Reason",
            })

            st.dataframe(df_display, use_container_width=True)
            st.caption(
                f"Displaying {len(df_display)} persistent audit log entries from SQLite storage. "
                "Note: Unknown agent requests (Rule R1) and revoked agent requests (Rule R7) "
                "are permanently retained in the audit trail for forensic traceability and compliance."
            )


if __name__ == "__main__":
    main()
