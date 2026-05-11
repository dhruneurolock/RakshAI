# Code File Summary

Auto-generated summary of project code files (excluding dependency/build folders).

Total code files summarized: **75**

## backend/alembic/env.py
- Type: Python module
- Imports: 8
- Functions: run_migrations_offline, run_migrations_online

## backend/alembic/versions/001_initial_migration.py
- Type: Python module
- Purpose: Initial migration Revision ID: 001 Revises: Create Date: 2024-01-20 10:00:00.000000
- Imports: 4
- Functions: upgrade, downgrade

## backend/alembic/versions/002_enterprise_architecture.py
- Type: Python module
- Purpose: Add enterprise architecture fields Revision ID: 002_enterprise Revises: 001 Create Date: 2026-02-22 11:00:00.000000
- Imports: 3
- Functions: upgrade, downgrade

## backend/app/__init__.py
- Type: Python module
- Purpose: __init__.py for app
- Imports: 0

## backend/app/agents/__init__.py
- Type: Python module
- Purpose: NeuroPentWeb Agentic Architecture Enterprise-grade autonomous pentesting agents
- Imports: 7

## backend/app/agents/base_agent.py
- Type: Python module
- Purpose: Base Agent Class All specialized agents inherit from this class
- Imports: 7
- Classes: BaseAgent

## backend/app/agents/coordinator.py
- Type: Python module
- Purpose: Coordinator Agent - LLM-Driven Planning Engine Orchestrates the entire penetration testing workflow
- Imports: 6
- Classes: CoordinatorAgent

## backend/app/agents/executor.py
- Type: Python module
- Purpose: Exploit Execution Agent Responsibilities: 1. Execute planned attacks via Tool Sandbox 2. Session management (cookies, tokens, headers) 3. Parameter fuzzing 4. Capture raw outputs 5. Upload results to MinIO 6. Create Finding nodes in Neo4j 7
- Imports: 5
- Classes: ExploitExecutionAgent

## backend/app/agents/poc_generator.py
- Type: Python module
- Purpose: Proof-of-Concept (PoC) Generation Agent Responsibilities: 1. Capture screenshots via Playwright 2. Record HTTP request/response traces 3. Generate cURL commands 4. LLM-generated business impact analysis 5. LLM-generated remediation steps 6.
- Imports: 6
- Classes: PoCAgent

## backend/app/agents/recon.py
- Type: Python module
- Purpose: Reconnaissance Agent Responsibilities: 1. Execute discovery tools (httpx, katana, nuclei, subfinder) 2. Browser automation with Playwright 3. Form discovery 4. Technology detection 5. Create Endpoint nodes in Neo4j 6. Upload raw outputs to 
- Imports: 5
- Classes: ReconAgent

## backend/app/agents/strategy.py
- Type: Python module
- Purpose: Attack Strategy Agent Responsibilities: 1. Analyze discovered endpoints with LLM 2. Prioritize attack vectors (IDOR, XSS, SQLi, etc.) 3. Create AttackNode relationships in Neo4j 4. Consider authentication requirements 5. Generate attack seq
- Imports: 4
- Classes: AttackStrategyAgent

## backend/app/agents/validator.py
- Type: Python module
- Purpose: Validation Agent Responsibilities: 1. Implement zero-hallucination guardrails 2. Replay findings 3 times 3. Check 85% success threshold (≥2 out of 3) 4. Update validation_replays and validation_count 5. Set status to VALIDATED or FALSE_POSI
- Imports: 5
- Classes: ValidationAgent

## backend/app/api/__init__.py
- Type: Python module
- Purpose: API __init__.py
- Imports: 0

## backend/app/api/v1/__init__.py
- Type: Python module
- Purpose: API v1 Router
- Imports: 2

## backend/app/api/v1/endpoints/__init__.py
- Type: Python module
- Purpose: Endpoints __init__.py
- Imports: 0

## backend/app/api/v1/endpoints/dashboard.py
- Type: Python module
- Purpose: Dashboard API Endpoints
- Imports: 6
- Functions: get_dashboard_stats (async), get_recent_activity (async), get_trends (async)

## backend/app/api/v1/endpoints/reports.py
- Type: Python module
- Purpose: Reports API Endpoints
- Imports: 8
- Functions: list_reports (async), get_report (async), download_report (async), delete_report (async)

## backend/app/api/v1/endpoints/scans.py
- Type: Python module
- Purpose: Scans API Endpoints Enterprise Architecture - Uses OrchestratorService for scan management
- Imports: 10
- Functions: create_scan (async), list_scans (async), get_scan (async), update_scan (async), start_scan (async), stop_scan (async), get_scan_endpoints (async), delete_scan (async), generate_scan_report (async), execute_scan_detection (async), validate_scan_findings (async)

## backend/app/api/v1/endpoints/vulnerabilities.py
- Type: Python module
- Purpose: Vulnerabilities API Endpoints
- Imports: 6
- Functions: _attach_endpoint_url, list_vulnerabilities (async), get_vulnerability (async), mark_false_positive (async), mark_false_positive (async), create_poc (async), get_severity_stats (async), get_category_stats (async)

## backend/app/core/__init__.py
- Type: Python module
- Purpose: __init__.py for core
- Imports: 0

## backend/app/core/celery_app.py
- Type: Python module
- Purpose: Celery configuration
- Imports: 2

## backend/app/core/config.py
- Type: Python module
- Purpose: Core configuration module
- Imports: 3
- Classes: Settings
- Functions: get_settings

## backend/app/core/database.py
- Type: Python module
- Purpose: Database module
- Imports: 6
- Functions: get_db

## backend/app/core/graph_db.py
- Type: Python module
- Purpose: Neo4j Graph Database Connection Manages attack graph relationships and complex queries
- Imports: 3
- Classes: GraphDatabase
- Functions: get_graph_db (async)

## backend/app/core/knowledge_base.py
- Type: Python module
- Purpose: Knowledge Base Loader Utility Centralized loader for all YAML files in the knowledge base
- Imports: 5
- Classes: KnowledgeBaseLoader
- Functions: get_knowledge_base_loader

## backend/app/core/redis_client.py
- Type: Python module
- Purpose: Redis Client Configuration Provides async Redis connection for agents
- Imports: 2
- Functions: get_redis (async), close_redis (async)

## backend/app/core/tool_sandbox.py
- Type: Python module
- Purpose: Tool Sandbox Layer - LAYER 5 CRITICAL SECURITY: LLM cannot execute directly All tool executions go through this deterministic layer
- Imports: 9
- Classes: ToolResult, ToolSandbox
- Functions: get_tool_sandbox

## backend/app/core/websocket_manager.py
- Type: Python module
- Purpose: WebSocket connection manager
- Imports: 3
- Classes: WebSocketManager

## backend/app/main.py
- Type: Python module
- Purpose: NeuroPentWeb Backend Main FastAPI application entry point
- Imports: 9
- Functions: startup_event (async), shutdown_event (async), root (async), health_check (async), websocket_endpoint (async)

## backend/app/models/__init__.py
- Type: Python module
- Purpose: __init__.py for models
- Imports: 1

## backend/app/models/models.py
- Type: Python module
- Purpose: Database models for NeuroPentWeb
- Imports: 6
- Classes: ScanStatus, VulnerabilitySeverity, Scan, Endpoint, Vulnerability, Report, AttackPlan

## backend/app/models/schemas.py
- Type: Python module
- Purpose: Pydantic schemas for request/response validation
- Imports: 4
- Classes: ScanStatusEnum, SeverityEnum, ScanCreate, ScanUpdate, ScanResponse, EndpointCreate, EndpointResponse, VulnerabilityCreate, VulnerabilityResponse, ReportCreate, ReportResponse, WSMessage ...

## backend/app/rule_engine/__init__.py
- Type: Python module
- Purpose: Rule Engine __init__.py
- Imports: 7

## backend/app/rule_engine/attack_plan_generator.py
- Type: Python module
- Purpose: Rule Engine - Component 7: Attack Plan Generator Assembles the final attack execution plan
- Imports: 4
- Classes: AttackPlanGenerator

## backend/app/rule_engine/context_normalizer.py
- Type: Python module
- Purpose: Rule Engine - Component 1: Context Normalizer Transforms discovery output to standardized format for rule processing
- Imports: 4
- Classes: ContextNormalizer

## backend/app/rule_engine/owasp_mapper.py
- Type: Python module
- Purpose: Rule Engine - Component 2: OWASP Mapper Maps endpoints to applicable OWASP Top 10:2025 categories
- Imports: 4
- Classes: OWASPMapper

## backend/app/rule_engine/payload_binder.py
- Type: Python module
- Purpose: Rule Engine - Component 4: Payload Binder Binds safe payloads from ~1000 YAML entries to test cases
- Imports: 7
- Classes: PayloadBinder

## backend/app/rule_engine/safety_enforcer.py
- Type: Python module
- Purpose: Rule Engine - Component 5: Safety Enforcer Blocks destructive payloads in production environments
- Imports: 3
- Classes: SafetyEnforcer

## backend/app/rule_engine/test_case_evaluator.py
- Type: Python module
- Purpose: Rule Engine - Component 3: Test Case Evaluator Selects applicable test cases from 96 YAML files based on context
- Imports: 6
- Classes: TestCaseEvaluator

## backend/app/rule_engine/validator_selector.py
- Type: Python module
- Purpose: Rule Engine - Component 6: Validator Selector Selects appropriate validators from 6 YAML validator files
- Imports: 6
- Classes: ValidatorSelector

## backend/app/services/llm_service.py
- Type: Python module
- Purpose: LLM Service - Intelligence Layer Ollama + LangChain for autonomous reasoning CRITICAL: LLM is used ONLY for analysis, NOT for direct execution
- Imports: 5
- Classes: LLMService
- Functions: get_llm_service (async)

## backend/app/services/orchestrator.py
- Type: Python module
- Purpose: Orchestrator Service (LAYER 2) Responsibilities: 1. Scope validation 2. Policy enforcement 3. Rate limiting 4. Target isolation 5. Manage concurrent scans 6. Trigger CoordinatorAgent 7. Monitor resource usage
- Imports: 7
- Classes: OrchestratorService
- Functions: get_orchestrator

## backend/app/services/report_generator.py
- Type: Python module
- Purpose: Advanced Report Generation Service Responsibilities: 1. Generate PDF reports (WeasyPrint) 2. Generate Word documents (python-docx) 3. Generate Excel spreadsheets (openpyxl) 4. LLM-generated executive summary 5. CVSS scoring 6. Compliance ma
- Imports: 7
- Classes: ReportGeneratorService
- Functions: get_report_generator (async)

## backend/app/services/storage_service.py
- Type: Python module
- Purpose: MinIO Object Storage Service Stores PoC screenshots, HTTP traces, and evidence files
- Imports: 6
- Classes: StorageService
- Functions: get_storage_service (async)

## backend/check_imports.py
- Type: Python module
- Purpose: Quick import health-check for all app modules.
- Imports: 0

## backend/scripts/run_phase1_real.py
- Type: Python module
- Imports: 4
- Functions: main (async)

## backend/scripts/test_rule_engine.py
- Type: Python module
- Purpose: Integration Test: Rule Engine + Knowledge Base Tests that all 7 rule engine components can access YAML data
- Imports: 11
- Functions: test_rule_engine_integration

## backend/scripts/validate_kb.py
- Type: Python module
- Purpose: Knowledge Base Validation and Testing Script Run this to verify all YAML files are correctly loaded
- Imports: 4
- Functions: validate_knowledge_base

## backend/tests/conftest.py
- Type: Python module
- Imports: 7
- Functions: override_get_db (async), setup_database (async), client (async), db_session (async)

## backend/tests/test_rule_engine/test_context_normalizer.py
- Type: Python module
- Imports: 2
- Functions: normalizer, test_normalize_endpoint_basic, test_infer_parameter_type, test_detect_technology, test_is_injectable_parameter

## backend/tests/test_rule_engine/test_safety_enforcer.py
- Type: Python module
- Imports: 2
- Functions: enforcer, test_blocks_destructive_sql, test_blocks_command_injection, test_allows_safe_payloads, test_blocks_mixed_case

## check-local-services.ps1
- Type: Script/automation
- Purpose: # NeuroPentWeb - Local Services Health Check

## frontend/postcss.config.js
- Type: Frontend/Node script
- Purpose: plugins: {
- Imports: 0

## frontend/src/App.tsx
- Type: Frontend/Node script
- Purpose: function App() {
- Imports: 11
- Functions: App

## frontend/src/components/Layout.tsx
- Type: Frontend/Node script
- Purpose: Shield,
- Imports: 2
- Functions: Layout
- Key declarations: isActive

## frontend/src/components/ProtectedRoute.tsx
- Type: Frontend/Node script
- Purpose: interface ProtectedRouteProps {
- Imports: 1
- Functions: ProtectedRoute

## frontend/src/main.tsx
- Type: Frontend/Node script
- Purpose: const queryClient = new QueryClient({
- Imports: 6

## frontend/src/pages/AttackSurface.tsx
- Type: Frontend/Node script
- Purpose: const [searchQuery, setSearchQuery] = useState('')
- Imports: 4
- Functions: AttackSurface, getMethodColor

## frontend/src/pages/Dashboard.tsx
- Type: Frontend/Node script
- Purpose: AlertTriangle,
- Imports: 5
- Functions: Dashboard, StatCard, getStatusColor

## frontend/src/pages/Login.tsx
- Type: Frontend/Node script
- Purpose: const [email, setEmail] = useState('')
- Imports: 3
- Functions: Login
- Key declarations: handleSubmit

## frontend/src/pages/Reports.tsx
- Type: Frontend/Node script
- Purpose: Placeholder page
- Imports: 0
- Functions: Reports

## frontend/src/pages/ScanDetail.tsx
- Type: Frontend/Node script
- Purpose: function SeverityBadge({ severity }: { severity: string }) {
- Imports: 5
- Functions: SeverityBadge, StatusIcon, SeverityCard, fmtDate, elapsed, ScanDetail

## frontend/src/pages/Scans.tsx
- Type: Frontend/Node script
- Purpose: const navigate = useNavigate()
- Imports: 5
- Functions: Scans, getStatusColor
- Key declarations: handleStartScan, handleStopScan, handleDeleteScan

## frontend/src/pages/Vulnerabilities.tsx
- Type: Frontend/Node script
- Purpose: ── Severity badge ────────────────────────────────────────────────────────────
- Imports: 6
- Functions: SeverityBadge, StatusBadge, ConfidenceBar, Select, owaspLabel, Vulnerabilities
- Key declarations: raw, raw

## frontend/src/pages/VulnerabilityDetail.tsx
- Type: Frontend/Node script
- Purpose: ArrowLeft,
- Imports: 6
- Functions: SeverityBadge, ConfidenceBar, StatusBadge, cvssLabel, cvssColor, owaspLabel, VulnerabilityDetail
- Key declarations: raw, handleExport

## frontend/src/services/api.ts
- Type: Frontend/Node script
- Purpose: const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
- Imports: 1

## frontend/src/services/endpoints.ts
- Type: Frontend/Node script
- Purpose: Scans API
- Imports: 2

## frontend/src/types/index.ts
- Type: Frontend/Node script
- Purpose: id: number
- Imports: 0

## frontend/tailwind.config.js
- Type: Frontend/Node script
- Purpose: ** @type {import('tailwindcss').Config} */
- Imports: 0

## frontend/vite.config.ts
- Type: Frontend/Node script
- Purpose: https://vitejs.dev/config/
- Imports: 3

## scripts/check_services_status.ps1
- Type: Script/automation
- Purpose: # Quick Service Status Check for NeuroPentWeb

## scripts/generate_codefile_summary.py
- Type: Python module
- Imports: 3
- Functions: iter_code_files, summarize_py, summarize_ts_js, summarize_ps

## scripts/test_enterprise_components.py
- Type: Python module
- Purpose: Test Enterprise Architecture Components This script verifies all new components are working: 1. LLM Service (Ollama + LangChain) 2. Tool Sandbox 3. Graph Database (Neo4j) 4. Storage Service (MinIO) 5. Coordinator Agent
- Imports: 8
- Functions: test_llm_service (async), test_tool_sandbox (async), test_graph_db (async), test_storage_service (async), test_coordinator_agent (async), main (async)

## start-backend.ps1
- Type: Script/automation
- Purpose: # NeuroPentWeb - Backend Only Startup Script

## start-local.ps1
- Type: Script/automation
- Purpose: # NeuroPentWeb - Local Machine Startup Script
- Functions: Test-ServiceRunning, Test-ProcessRunning, Test-PortListening
