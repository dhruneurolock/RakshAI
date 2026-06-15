# NeuroPentWeb Scan Pipeline Analysis

This document provides an analysis of the backend Python files, specifically focusing on which files are actively executed ("working") and which are bypassed or inactive ("not working") when a new scan pipeline is started.

## Overview

The scan execution in NeuroPentWeb has shifted from a fully agentic architecture to a deterministic, fallback-based enterprise pipeline managed by the `OrchestratorService`. When a scan starts, the system attempts a "best-effort" bootstrap of the `CoordinatorAgent`, but the primary execution relies on the synchronous `_fallback_discovery_for_scan` workflow located in `orchestrator.py`.

---

## 🟢 Working Files (Actively Executed During Scan)

These files are directly involved in executing the scan pipeline from start to finish.

### Entry Points & Orchestration
*   **`app/main.py`**: The FastAPI application entry point.
*   **`app/api/v1/endpoints/scans.py`**: Receives the `POST /scans/` request and initializes the scan via `OrchestratorService`.
*   **`app/services/orchestrator.py`**: The core controller. It drives the 7-phase deterministic pipeline (`_fallback_discovery_for_scan`), overriding the older agentic flows.

### Core Services (Invoked by Orchestrator)
*   **`app/services/advanced_discovery.py`**: Called in Phase 2 for deep reconnaissance (crawling, technology detection, forms) and Phase 4 for enhanced vulnerability checks.
*   **`app/services/payload_engine.py`**: Actively provides test payloads (XSS, SQLi, NoSQLi, XXE, etc.) used during Phase 4 exploit testing.
*   **`app/services/validator_engine.py`**: Provides validation signatures (like SQL error patterns) used to confirm vulnerabilities during Phase 4.
*   **`app/services/finding_enricher.py`**: Used to enrich validated findings with OWASP, CWE, and CVSS metadata.
*   **`app/services/storage_service.py`**: Executed during Phase 6 (`_generate_poc_evidence_phase`) to store PoC artifacts and evidence traces.
*   **`app/services/report_generator.py`**: Executed during Phase 7 (`_generate_reports_phase`) to compile the final PDF/Word/Excel or JSON fallback report.

### Core Infrastructure
*   **`app/core/config.py`** & **`app/core/database.py`**: Provide configuration and database session management.
*   **`app/models/models.py`**: Actively used to persist `Scan`, `Endpoint`, `Vulnerability`, and `Report` states to PostgreSQL/SQLite.

---

## 🔴 Not Working Files (Bypassed / Inactive During Scan)

These files are either bypassed in favor of deterministic fallback logic, serve as legacy components, or are not related to the scan pipeline execution loop.

### Agentic Architecture (Bypassed)
The orchestrator skips these agents to avoid LLM timeouts and uses hardcoded, rule-based deterministic logic instead.
*   **`app/agents/coordinator.py`**: Attempted briefly in `_run_coordinator_bootstrap_sync`, but often skipped/fails, delegating execution to the fallback pipeline.
*   **`app/agents/recon.py`**: Replaced by `advanced_discovery.py` and local `requests` logic inside the orchestrator.
*   **`app/agents/strategy.py`**: Replaced by `_create_initial_attack_strategy` and `_create_execution_plan` (local rule-based methods in orchestrator).
*   **`app/agents/validator.py`**: Replaced by `_validate_findings_replay_phase` inside orchestrator.
*   **`app/agents/poc_generator.py`**: Replaced by `_generate_poc_evidence_phase` inside orchestrator.
*   **`app/agents/executor.py`**, **`app/agents/base_agent.py`**, **`app/agents/remediation_agent.py`**: Not actively used in the current fallback pipeline.

### Unused Services (During Pipeline)
*   **`app/services/llm_service.py`**: Explicitly skipped in Phase 1, Phase 3, and HTTP Surface Analysis (as seen in `orchestrator.py` comments: `LLM skipped for Phase 1 strategy — deterministic fallback is equally effective`).
*   **`app/services/simple_discovery.py`**: Legacy module. Discovery is now handled directly by `AdvancedDiscoveryEngine` and local orchestrator logic.
*   **`app/services/audit_service.py`**, **`app/services/evidence_service.py`**, **`app/services/correlation_service.py`**: Active for REST API queries, but not part of the active scan discovery/testing loop.

---


---

## 🔧 Migration: Neo4j → Native SQLAlchemy Bridge (Completed)

The original codebase depended on Neo4j for attack graph storage, which was a key reason the agentic architecture (`coordinator.py`, `recon.py`, etc.) failed to execute natively without heavy external dependencies. To allow the agents to run locally without Docker or Java, Neo4j has been completely removed and replaced with a **Native SQLAlchemy Bridge**.

### Changes Made:
| File | Change |
|------|--------|
| `app/core/graph_db.py` | Completely rewritten to use standard SQLAlchemy (`SessionLocal()`) instead of Cypher/Neo4j. It mimics graph logic by reading/writing to the `endpoints`, `scans`, and `attack_plans` PostgreSQL/SQLite tables. |
| `app/agents/coordinator.py` | Updated `initialize_attack_graph` and `adaptive_check` to use the native Python methods provided by the SQLAlchemy bridge instead of raw Cypher queries. |
| `app/services/orchestrator.py` | Updated `_build_attack_graph_best_effort` to use the same SQLAlchemy bridge natively. |
| `docker-compose.memgraph.yml` | Deleted. Docker is no longer required to run the graph database. |
| `.env` | Removed graph database connection strings entirely. |
