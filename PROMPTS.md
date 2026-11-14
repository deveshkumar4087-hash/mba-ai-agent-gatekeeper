# Development Prompts Log: AI Agent Gatekeeper for Banking Transactions

**Student Enrolment Number:** `PGD202565745`  
**Assigned Industry Domain:** Bank (last digit 5)  
**Selected Reference Institution:** Capital One (Background context only; student-designed academic prototype)  
**Project:** AI Agent Gatekeeper for Banking Transactions  

This document tracks key instructions, development prompts, and iterative refinement prompts used during the design and construction of the prototype.

---

## 1. Stage 1: Architectural Scaffolding & Setup

### Prompt 1.1: Project Initialization & Assignment Constraints
- **Date/Time:** 2026-11-14T14:29:02+05:30
- **Context:** Initial project briefing from MBA coursework requirements.
- **Core Prompt Summary:**
  > "You are a senior Python engineer and business-process automation architect.
  > I am an MBA student building a practical project called:
  > 'AI Agent Gatekeeper for Banking Transactions'.
  > Enrolment number: PGD202565745 (Last digit 5 -> BANK).
  > Address 3 actions: View balance, Pay a bill, Transfer money.
  > System decisions: ALLOW, ASK CUSTOMER, BLOCK.
  > Final prototype features: Register/revoke agent, permanent block for revoked agents, rule number in response, audit logging, enrolment number on main screen, 6 test scenarios, automated tests, README, PROMPTS.md.
  > Constraints: Student-designed policy prototype, synthetic data only, no real banking operations, staged development approach. Stop after Stage 1 without implementing decision rules or inventing final 6-8 rules."
- **Outcome / Actions Taken:**
  - Workspace inspected and verified empty.
  - Python 3.14 / pytest / streamlit runtime environment verified.
  - Clean modular architecture laid out (`agents/`, `services/`, `data/`, `tests/`, `app.py`, `orchestrator.py`).
  - Strict separation of concerns established with Pydantic schemas.
  - Initial tests written and verified for structural integrity.

---

## 2. Stage 2: Policy & Rule Engine Implementation

### Prompt 2.1: Deterministic Rule Engine, Matrix & Unit Testing
- **Date/Time:** 2026-11-14T14:46:10+05:30
- **Context:** Implementation of the deterministic policy and decision engine for banking operations.
- **Selected Institution Context:** Capital One (Used solely as background context for the real-world problem of personal AI agents interacting with consumer banking accounts; not official Capital One policies or systems).
- **Core Prompt Summary:**
  > "STAGE 2 — POLICY & RULE ENGINE IMPLEMENTATION
  > Enrolment number: PGD202565745. Domain: Banking. Selected company: Capital One.
  > Prototype automatic-payment threshold: $500 per transaction.
  > Implement exactly the 8 final rules:
  > R1: Unknown Agent -> BLOCK
  > R2: Registered Read-Only Access (View Balance) -> ALLOW
  > R3: Low-Value Bill Payment (<= $500) -> ALLOW
  > R4: High-Value Bill Payment (> $500) -> ASK CUSTOMER
  > R5: Low-Value Money Transfer (<= $500) -> ASK CUSTOMER
  > R6: High-Value Money Transfer (> $500) -> BLOCK
  > R7: Revoked Agent -> BLOCK (Priority override over permission rules)
  > R8: Customer Rejection -> BLOCK (Ultimate override)
  > Decision Priority: R8 -> R7 -> R1 -> R2 -> R3/R4 -> R5/R6.
  > Structured input and output models.
  > Decisions: ALLOW, ASK CUSTOMER, BLOCK.
  > Create automated unit tests (Tests 1-6, boundary tests, priority overrides, validation).
  > Update README.md and PROMPTS.md.
  > Run pytest and report actual results. Stop after Stage 2."

### The 8 Rule IDs & Specification:
1. **R1 (Unknown Agent):** Condition: Agent not registered. Decision: `BLOCK`.
2. **R2 (Registered Read-Only Access):** Condition: Active agent, View Balance. Decision: `ALLOW`.
3. **R3 (Low-Value Bill Payment):** Condition: Active agent, Pay Bill, amount <= $500. Decision: `ALLOW`.
4. **R4 (High-Value Bill Payment):** Condition: Active agent, Pay Bill, amount > $500. Decision: `ASK CUSTOMER`.
5. **R5 (Low-Value Money Transfer):** Condition: Active agent, Transfer Money, amount <= $500. Decision: `ASK CUSTOMER`.
6. **R6 (High-Value Money Transfer):** Condition: Active agent, Transfer Money, amount > $500. Decision: `BLOCK`.
7. **R7 (Revoked Agent):** Condition: Agent revoked. Decision: `BLOCK` (Overriding priority).
8. **R8 (Customer Rejection):** Condition: Customer explicitly rejected request. Decision: `BLOCK` (Ultimate priority).

### Prototype Threshold:
- **Value:** `$500.00` per transaction.
- **Designation:** Student-designed prototype automatic-payment threshold (not an official bank limit).

---

## 3. Stage 3: Agent Lifecycle, Persistence, Audit Logging & Pipeline

### Prompt 3.1: Operational Backend, Persistence & End-to-End Orchestrator
- **Date/Time:** 2026-11-14T14:52:59+05:30
- **Context:** Implementing the complete operational backend and persistent storage layer.
- **Core Prompt Summary:**
  > "STAGE 3 — AGENT LIFECYCLE, PERSISTENCE, AUDIT LOGGING & END-TO-END PIPELINE
  > Enrolment number: PGD202565745. Domain: Banking. Selected company: Capital One.
  > 1. Persistent agent registration (SQLite database in data/).
  > 2. Persistent agent revocation with system UTC timestamps.
  > 3. Revocation must persist after program restarts and cannot automatically revert.
  > 4. Persistent audit logging for all requests (including unknown and revoked agents).
  > 5. End-to-end request orchestration (Permission -> Rule Engine -> Audit Log).
  > 6. Automated tests: Tests A through J + edge cases.
  > 7. Update README.md and PROMPTS.md. Run pytest and report real results."

### Storage Approach Selected:
- **Engine:** Python built-in `sqlite3` embedded database.
- **Location:** `data/gatekeeper.db` (configurable path, supporting isolated temporary databases for testing).
- **Schema:** `agents` (agent credentials and timestamps), `audit_logs` (immutable audit trail), `accounts` (synthetic balances).

---

## 4. Stage 4: Six Coursework Scenarios & Verification Suite

### Prompt 4.1: Six Mandatory Coursework Scenarios & Verification Runner
- **Date/Time:** 2026-11-14T15:01:13+05:30
- **Context:** Formalizing and automating the six mandatory coursework scenarios for evaluation, screen recording, and report preparation.
- **Core Prompt Summary:**
  > "STAGE 4 — SIX COURSEWORK SCENARIOS & VERIFICATION SUITE
  > Enrolment number: PGD202565745. Domain: Banking. Selected company: Capital One.
  > Implement the six mandatory coursework scenarios:
  > Scenario 1: Known Agent, Read-Only Request (ALLOW / R2)
  > Scenario 2: Unknown Agent (BLOCK / R1)
  > Scenario 3: Payment Above Automatic Threshold (ASK CUSTOMER / R4)
  > Scenario 4: Payment Below Automatic Threshold (ALLOW / R3)
  > Scenario 5: Revoked Agent (BLOCK / R7)
  > Scenario 6: Own Case - Money Transfer <= $500 (ASK CUSTOMER / R5)
  > Create scenario runner in services/scenario_runner.py.
  > Verify audit log for every scenario (including BLOCK decisions).
  > Generate Expected vs Actual verification table. Ensure test isolation.
  > Run pytest and report actual results. Update README.md and PROMPTS.md."

### The Six Mandatory Coursework Scenarios:
1. **Scenario 1:** Customer `CUST001`, Agent `BankBot` (Active), Action `View Balance`, Amount `0.0`. Expected: `ALLOW` / `R2`.
2. **Scenario 2:** Customer `CUST001`, Agent `RandomAI` (Unknown), Action `View Balance`, Amount `0.0`. Expected: `BLOCK` / `R1`.
3. **Scenario 3:** Customer `CUST002`, Agent `PayPilot` (Active), Action `Pay Bill`, Amount `800.0`. Expected: `ASK CUSTOMER` / `R4`.
4. **Scenario 4:** Customer `CUST002`, Agent `PayPilot` (Active), Action `Pay Bill`, Amount `300.0`. Expected: `ALLOW` / `R3`.
5. **Scenario 5:** Customer `CUST001`, Agent `BankBot` (Revoked), Action `Pay Bill`, Amount `100.0`. Expected: `BLOCK` / `R7`.
6. **Scenario 6:** Customer `CUST002`, Agent `PayPilot` (Active), Action `Transfer Money`, Amount `400.0`. Expected: `ASK CUSTOMER` / `R5`.

---

## 5. Stage 5: Interactive Streamlit Dashboard & Demonstration

### Prompt 5.1: Web Dashboard Implementation & Live Verification
- **Date/Time:** 2026-11-14T15:09:20+05:30
- **Context:** Building the user-friendly Streamlit web application connecting to the verified backend without duplicating decision logic.
- **Core Prompt Summary:**
  > "STAGE 5 — INTERACTIVE STREAMLIT DASHBOARD & DEMONSTRATION
  > Enrolment number: PGD202565745. Domain: Banking. Selected company: Capital One.
  > Build a simple, clean, functional Streamlit dashboard in app.py.
  > Connect to the existing backend (GatekeeperOrchestrator, DataStore, RuleEngine, AuditLogger, ScenarioRunner).
  > Do not duplicate rules in app.py.
  > Sections:
  > 1. Hero & Student Header with Enrolment Number PGD202565745 and Academic Disclaimer.
  > 2. Evaluate AI Agent Request (Customer, Agent, Action, Amount, Rejected Checkbox, Evaluate button, Prominent decision text).
  > 3. Register AI Agent (Customer ID, Agent Name, Notes -> ACTIVE status, UTC timestamp).
  > 4. Revoke AI Agent (Customer ID, Agent Name -> REVOKED status, UTC timestamp).
  > 5. Agent Status (Check status -> ACTIVE / REVOKED / UNKNOWN).
  > 6. Coursework Verification (Run 6 Scenarios button -> Live Expected vs Actual table).
  > 7. Persistent Audit Trail (SQLite records table, refresh control, customer filter).
  > Verify launch with 'streamlit run app.py' and verify all tests pass with 'pytest tests/ -v'."

### UI Sections Implemented:
1. **Hero & Student Header:**
   - Enrolment Number prominently displayed: `PGD202565745`
   - Assigned Domain: `Banking (Last digit 5)`
   - Mandatory Responsible Disclosure banner: *"Student-designed academic prototype. Not an official Capital One system or policy. All rules, thresholds, customers, and transactions are synthetic."*
2. **Evaluate Request Tab:**
   - Dropdown with exact actions: `View Balance`, `Pay Bill`, `Transfer Money`.
   - Decimal amount input with dynamic disabling for read-only View Balance.
   - Rejection checkbox (`customer_rejected`).
   - Evaluates via `orchestrator.evaluate_request(...)` and displays prominent text decisions: `ALLOW`, `ASK CUSTOMER`, or `BLOCK` with Rule ID and risk reason.
3. **Agent Registration Tab:**
   - Onboards agents via `orchestrator.register_agent(...)` into SQLite with system UTC timestamps and `ACTIVE` standing.
4. **Revoke Agent Tab:**
   - Permanently decommissions agents via `orchestrator.revoke_agent(...)` with immutable `revoked_at` timestamp.
5. **Agent Status Inspection Tab:**
   - Real-time status lookup (`ACTIVE`, `REVOKED`, `UNKNOWN`) via `DataStore`.
6. **Coursework Verification Tab:**
   - One-click execution calling `CourseworkScenarioRunner().run_all()`.
   - Renders live Expected vs Actual comparison table and printable summary.
7. **Persistent Audit Trail Tab:**
   - Displays real records loaded from `audit_logs` in SQLite with customer filtering and manual refresh.

### Backend Components Reused:
- `GatekeeperOrchestrator`: Ingests requests, routes to permission and rule engine, and coordinates audit logging.
- `DataStore`: Direct SQLite querying for agent standing and historical audit logs.
- `RegistrationAgent` & `RevocationAgent`: Lifecycle state management.
- `CourseworkScenarioRunner`: Live scenario execution.

### Verification Performed:
- **Application Launch Test:** Executed `streamlit run app.py --server.headless=true --server.port=8501`. Verified server launched on port 8501 and successfully bound to `http://localhost:8501`.
- **Automated Tests:** Added `tests/test_app_smoke.py`. Executed `pytest tests/ -v`:
  - 42 tests collected
  - 42 tests passed
  - 0 failures, 0 errors in 14.84s (100% pass rate).

### Code Changes Tracking:
- Completely authored `app.py` replacing the Stage 1 scaffold.
- Authored `tests/test_app_smoke.py` verifying student metadata and orchestrator factory initialization.
- No out-of-band or manual modifications were made.

---

## 6. Student Personal Verification

I personally reviewed the six mandatory coursework scenarios against the assignment requirements and checked that the expected decision and rule number for each scenario match the implemented results.

The six checks were:

1. Known registered agent + View Balance → ALLOW / R2
2. Unknown agent → BLOCK / R1
3. Pay Bill above $500 → ASK CUSTOMER / R4
4. Pay Bill below or equal to $500 → ALLOW / R3
5. Revoked agent → BLOCK / R7
6. Money transfer below or equal to $500 → ASK CUSTOMER / R5

I also checked that the application displays the enrolment number PGD202565745 and that the prototype disclaimer identifies the system as a student-designed academic prototype rather than an official Capital One system.

This verification was performed personally by the student before repository setup.
