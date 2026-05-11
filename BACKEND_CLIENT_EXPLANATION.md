# RakshAI Backend - Client Explanation Document

## 1. Purpose of This Document
This document explains the complete backend implementation in client-friendly language.

It covers:
- Full backend flow from scan request to downloadable report.
- Role of every agent in the multi-agent pipeline.
- How test cases are selected and applied.
- How payloads are selected, filtered, and executed safely.
- How LLM is used and where deterministic controls are enforced.
- Explanation of every Python code file under backend/.

---

## 2. End-to-End Backend Flow

### Step A: Scan Request and Initialization
1. Frontend sends a scan creation request to API.
2. API writes scan metadata into database.
3. Orchestrator starts enterprise guardrails:
- Scope validation
- Policy checks
- Rate limiting
- Queue/concurrency management

### Step B: Planning and Recon
4. Coordinator Agent creates strategy and controls stage order.
5. Recon Agent discovers target surface:
- Endpoints
- Forms
- Technologies
- Template findings
6. Recon data is persisted to graph/database and raw artifacts are stored.

### Step C: Rule Engine (Deterministic Core)
7. ContextNormalizer normalizes endpoint/context features.
8. OWASPMapper maps endpoint risk to OWASP categories.
9. TestCaseEvaluator chooses matching tests from knowledge base.
10. PayloadBinder binds payload packs to selected test cases.
11. SafetyEnforcer removes unsafe/destructive payloads and actions.
12. ValidatorSelector assigns validation logic for each test.
13. AttackPlanGenerator outputs final executable attack plan.

### Step D: Execution and Validation
14. Executor Agent executes attack plan via sandboxed tools.
15. Findings and evidence are captured.
16. Validation Agent replays findings and enforces confidence thresholds.
17. False positives are reduced using replay evidence and structured logic.

### Step E: Enrichment and Reporting
18. PoC generator creates reproduction commands/evidence.
19. Remediation agent creates practical fix guidance and business impact text.
20. Report generator builds PDF/Word/Excel/JSON outputs.
21. Storage service uploads artifacts and API exposes report downloads.

---

## 3. Agent Roles and Responsibilities

### Coordinator Agent
- Central orchestrator for scan stages.
- Creates strategy and controls transitions across agents.
- Maintains adaptive loop for workflow progression.

### Recon Agent
- Discovers endpoints and technology stack.
- Uses probing/crawling/template discovery methods.
- Sends discovered assets into graph and persistence layers.

### Attack Strategy Agent
- Converts recon output into prioritized attack vectors.
- Produces threat model and attack ordering.

### Exploit Execution Agent
- Executes planned tests through sandbox tooling.
- Manages execution context, session state, and raw outputs.

### Validation Agent
- Replays findings multiple times for reliability.
- Applies threshold logic to mark VALIDATED or FALSE_POSITIVE.
- Produces confidence scores.

### PoC Generator Agent
- Produces practical proof-of-concept content.
- Adds reproducibility to technical findings.

### Remediation Agent
- Produces remediation recommendations.
- Adds business-impact and fix-priority context.

---

## 4. How Test Cases Are Applied
1. Endpoint context is normalized into machine-evaluable fields.
2. OWASP relevance is calculated from endpoint signals.
3. Knowledge-base test cases are filtered by:
- Endpoint type
- Method
- Parameters
- OWASP mapping
4. Matching tests are prepared for payload binding.
5. Safety checks remove risky actions before execution.
6. Validators are attached to verify outcome quality.
7. Final plan is generated with sequence, priority, and runtime configuration.

---

## 5. How Payloads Are Applied
- Payloads come from structured knowledge-base payload sets.
- PayloadBinder attaches payload families to selected tests.
- SafetyEnforcer applies policy constraints.
- Executor injects payloads into endpoint-specific parameters.
- Outputs are captured for evidence and replay validation.

---

## 6. How LLM Works in This Backend
LLM is used for intelligence and explanations, not direct command execution.

LLM is used for:
- Strategy generation
- Threat prioritization
- Finding explanations
- Business impact text
- Remediation language
- Report executive summaries

Deterministic controls still govern execution:
- Rule engine selection and safety
- Tool sandbox controls
- Replay-based validation
- Confidence thresholding

---

## 7. Backend File-by-File Explanation

## 7.1 Top-level backend files

### backend/check_imports.py
Purpose: Utility script to verify expected backend imports/dependencies.

### backend/check_imports.py
Purpose: Utility script to verify expected backend imports/dependencies.

### backend/integrate_remediation.py
Purpose: Integration helper for remediation workflow or migration operations.

### backend/migrate_add_llm_columns.py
Purpose: DB migration helper to add LLM-related fields in schema.

### backend/tmp_check_settings.py
Purpose: Temporary settings validation/debug script.

---

## 7.2 Application entrypoint

### backend/app/main.py
Purpose: FastAPI application bootstrap. Registers routes, middleware, startup behavior.

### backend/app/__init__.py
Purpose: App package initializer.

---

## 7.3 API layer

### backend/app/api/__init__.py
Purpose: API package initializer.

### backend/app/api/v1/__init__.py
Purpose: API v1 router composition.

### backend/app/api/v1/endpoints/__init__.py
Purpose: Endpoint module namespace initializer.

### backend/app/api/v1/endpoints/scans.py
Purpose: Scan lifecycle endpoints (create/start/stop/status/logs/reports generation trigger).

### backend/app/api/v1/endpoints/reports.py
Purpose: Report listing, metadata retrieval, download, and deletion endpoints.

### backend/app/api/v1/endpoints/dashboard.py
Purpose: Dashboard statistics/system status endpoints.

### backend/app/api/v1/endpoints/vulnerabilities.py
Purpose: Findings list/detail, status updates, remediation/poc-related endpoint actions.

---

## 7.4 Core infrastructure

### backend/app/core/__init__.py
Purpose: Core package initializer.

### backend/app/core/config.py
Purpose: Main configuration model and runtime settings access.

### backend/app/core/config_local.py
Purpose: Local-development configuration overrides.

### backend/app/core/database.py
Purpose: SQL database engine/session setup and DB dependency helpers.

### backend/app/core/graph_db.py
Purpose: Graph database integration (attack graph, endpoints, relationships).

### backend/app/core/redis_client.py
Purpose: Redis connectivity and caching/pubsub helper.

### backend/app/core/tool_sandbox.py
Purpose: Controlled execution wrapper for security tools and command safety boundaries.

### backend/app/core/websocket_manager.py
Purpose: Real-time scan progress/events broadcast management.

### backend/app/core/knowledge_base.py
Purpose: Knowledge-base loading/access helpers used by rule/LLM logic.

### backend/app/core/celery_app.py
Purpose: Background task queue configuration and worker integration.

---

## 7.5 Data model layer

### backend/app/models/__init__.py
Purpose: Models package initializer.

### backend/app/models/models.py
Purpose: SQLAlchemy ORM entities (Scan, Vulnerability, Report, Endpoint, etc.).

### backend/app/models/schemas.py
Purpose: Pydantic request/response schemas used by API layer.

---

## 7.6 Agent layer

### backend/app/agents/__init__.py
Purpose: Agent package exports and namespace.

### backend/app/agents/base_agent.py
Purpose: Shared base behavior for all agents (logging/progress/common services).

### backend/app/agents/coordinator.py
Purpose: Central orchestration agent controlling full scan flow.

### backend/app/agents/recon.py
Purpose: Recon/discovery agent for endpoint and technology enumeration.

### backend/app/agents/strategy.py
Purpose: Attack strategy agent for prioritization and threat model planning.

### backend/app/agents/executor.py
Purpose: Execution agent for running tests/payloads and collecting findings.

### backend/app/agents/validator.py
Purpose: Validation agent for replay checks and false-positive control.

### backend/app/agents/poc_generator.py
Purpose: PoC generation agent to create reproducible attack evidence.

### backend/app/agents/remediation_agent.py
Purpose: Remediation generation agent for fixes and business impact guidance.

---

## 7.7 Rule engine layer

### backend/app/rule_engine/__init__.py
Purpose: Rule engine package initializer.

### backend/app/rule_engine/context_normalizer.py
Purpose: Converts raw endpoint/context into normalized feature structure.

### backend/app/rule_engine/owasp_mapper.py
Purpose: Maps endpoint characteristics to OWASP categories.

### backend/app/rule_engine/test_case_evaluator.py
Purpose: Selects applicable tests from KB based on normalized context.

### backend/app/rule_engine/payload_binder.py
Purpose: Binds relevant payloads to each selected test case.

### backend/app/rule_engine/safety_enforcer.py
Purpose: Filters unsafe operations/payloads and enforces safety policy.

### backend/app/rule_engine/validator_selector.py
Purpose: Chooses appropriate validators per test/finding type.

### backend/app/rule_engine/attack_plan_generator.py
Purpose: Produces final executable attack plan with sequencing and stats.

---

## 7.8 Service layer

### backend/app/services/orchestrator.py
Purpose: Enterprise orchestration service for scope/policy/rate/concurrency and scan lifecycle.

### backend/app/services/llm_service.py
Purpose: LLM and RAG integration for strategy/analysis/enrichment tasks.

### backend/app/services/simple_discovery.py
Purpose: Deterministic lightweight endpoint discovery support service.

### backend/app/services/report_generator.py
Purpose: Multi-format report generation (PDF/Word/Excel/JSON) with statistics and summaries.

### backend/app/services/storage_service.py
Purpose: Artifact storage abstraction for reports/evidence (local/MinIO and retrieval helpers).

---

## 7.9 Alembic migration files

### backend/alembic/env.py
Purpose: Alembic environment config and migration runtime setup.

### backend/alembic/versions/001_initial_migration.py
Purpose: Initial DB schema creation migration.

### backend/alembic/versions/002_enterprise_architecture.py
Purpose: Schema extension for enterprise architecture features.

### backend/alembic/versions/003_llm_evidence_poc.py
Purpose: Schema extension for LLM, evidence, and PoC-related fields.

---

## 7.10 Operational scripts

### backend/scripts/run_phase1_real.py
Purpose: Script for running/testing phase-1 workflow against real target context.

### backend/scripts/test_rule_engine.py
Purpose: Script to validate rule engine behavior end-to-end.

### backend/scripts/validate_kb.py
Purpose: Script to validate knowledge-base structure/content consistency.

---

## 7.11 Test files

### backend/tests/conftest.py
Purpose: Shared pytest fixtures and test setup configuration.

### backend/tests/test_rule_engine/test_context_normalizer.py
Purpose: Unit tests for ContextNormalizer behavior and edge cases.

### backend/tests/test_rule_engine/test_safety_enforcer.py
Purpose: Unit tests for SafetyEnforcer policy/safety filtering behavior.

---

## 8. Client-Facing Summary
If you want a short client presentation version, use this sequence:
1. Multi-agent architecture with strict safety controls.
2. Deterministic rule engine for test and payload selection.
3. Replay-based validation to reduce false positives.
4. LLM for intelligence and explanation, not direct execution.
5. Complete audit trail from endpoint discovery to downloadable report.

---

## 9. Notes
- This document is intentionally detailed for technical and audit audiences.
- It can be split into executive and technical annexes if needed.
