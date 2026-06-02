# Scan Stage File Usage (Current Runtime Path)

Generated: 2026-05-14
Scope: backend scan flow from scan start to scan completion/failure.

## Runtime Entry Path

1. `backend/app/services/orchestrator.py::start_scan`
2. `backend/app/services/orchestrator.py::_launch_scan`
3. Background thread -> `backend/app/services/orchestrator.py::_run_phase_pipeline_sync`
4. Best-effort coordinator bootstrap -> `backend/app/services/orchestrator.py::_run_coordinator_bootstrap_sync`
5. Deterministic pipeline -> `backend/app/services/orchestrator.py::_fallback_discovery_for_scan`

## Stage-by-Stage Python Files Used

### Stage 0 - Scan Request Validation and Launch
- `backend/app/services/orchestrator.py`
- `backend/app/core/config.py` (via `get_settings`)
- `backend/app/core/database.py` (via `SessionLocal`)
- `backend/app/models/models.py` (`Scan`, `Endpoint`, `Vulnerability`, `Report`, enums)

### Stage 1 - Best-Effort Agent Bootstrap (Now Attempted)
- `backend/app/services/orchestrator.py` (`_run_coordinator_bootstrap_sync`)
- `backend/app/agents/coordinator.py` (`CoordinatorAgent.run`)
- `backend/app/agents/base_agent.py` (`initialize`, `cleanup`, logging)
- `backend/app/core/redis_client.py` (agent publish calls)
- `backend/app/core/graph_db.py` (agent graph operations, if available)
- `backend/app/services/llm_service.py` (only if available)

Note: this bootstrap is best-effort and bounded by timeout; failure does not stop the main deterministic pipeline.

### Stage 2 - Recon / Discovery
- `backend/app/services/orchestrator.py` (`_fallback_discovery_for_scan`)
- `backend/app/services/advanced_discovery.py` (`run_phase2_recon`, crawl, form extraction, dir brute)
- `requests` (HTTP fetch/crawl)
- `re` and `urllib.parse` utilities used inside service code

### Stage 3 - Endpoint Persistence
- `backend/app/services/orchestrator.py`
- `backend/app/models/models.py` (`Endpoint`)
- `backend/app/core/database.py` (`SessionLocal`)

Current behavior: discovered URLs are persisted as GET endpoints, and discovered forms are persisted with their actual method (POST/PUT/PATCH/etc.) using `(url, method)` dedupe.

### Stage 4 - Exploit Testing / Finding Generation
- `backend/app/services/orchestrator.py` (`_run_post_discovery_pipeline`)
- `backend/app/services/advanced_discovery.py` (`run_phase4_checks`)
- `backend/app/services/payload_engine.py`
- `backend/app/services/validator_engine.py`
- `backend/app/services/finding_enricher.py`
- External optional tools via subprocess (`sqlmap`, `dalfox`) if installed

### Stage 5 - Finding Persistence and Validation
- `backend/app/services/orchestrator.py` (`_persist_findings`, `_validate_findings_replay_phase`)
- `backend/app/models/models.py` (`Vulnerability`, `Endpoint`)
- `backend/app/core/database.py`

### Stage 6 - PoC Artifact Generation
- `backend/app/services/orchestrator.py` (`_generate_poc_evidence_phase`)
- `backend/app/services/storage_service.py` (`get_storage_service`, upload calls)

### Stage 7 - Report Generation
- `backend/app/services/orchestrator.py` (`_generate_reports_phase`)
- `backend/app/services/report_generator.py` (`ReportGeneratorService`)
- `backend/app/models/models.py` (`Report`)
- `backend/app/core/database.py`

### Stage 8 - Phase/Event Publishing and Completion
- `backend/app/services/orchestrator.py` (`_publish_phase_event`, status/final counters)
- `backend/app/core/redis_client.py` (best effort event publish)
- `backend/app/models/models.py` (`Scan` status/progress fields)

## Files Present But Not Directly Used In Current Scan Start Path

These files exist, but are not directly invoked by `start_scan -> _launch_scan -> _run_phase_pipeline_sync` in the current code path:

- `backend/app/agents/recon.py`
- `backend/app/agents/strategy.py`
- `backend/app/agents/executor.py`
- `backend/app/agents/validator.py`
- `backend/app/agents/poc_generator.py`
- `backend/app/agents/remediation_agent.py`

Why: `CoordinatorAgent` currently publishes Redis events (`agent:recon:start`, `scheduler:adaptive_check`), but no subscriber/consumer implementation was found in the current backend files for those channels.

## Conditional / Optional Usage Notes

- `backend/app/services/llm_service.py`: used only if available and initialized.
- `backend/app/core/graph_db.py`: used only if graph DB is reachable.
- `backend/app/core/redis_client.py`: used for best-effort events; pipeline still runs if Redis is unavailable.
- External tools (`sqlmap`, `dalfox`) are optional and skipped if missing.

## Quick Summary

- Deterministic orchestrator pipeline is the primary execution path.
- Coordinator bootstrap is now attempted before fallback, but still non-blocking.
- Several agent files are currently architectural modules, not fully wired into active event-driven execution.
