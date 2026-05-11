"""Quick import health-check for all app modules."""
modules = [
    "app.main",
    "app.models.models",
    "app.models.schemas",
    "app.core.config",
    "app.core.database",
    "app.core.redis_client",
    "app.core.celery_app",
    "app.core.tool_sandbox",
    "app.core.websocket_manager",
    "app.core.knowledge_base",
    "app.core.graph_db",
    "app.services.orchestrator",
    "app.services.llm_service",
    "app.services.report_generator",
    "app.services.storage_service",
    "app.agents.base_agent",
    "app.agents.coordinator",
    "app.agents.recon",
    "app.agents.strategy",
    "app.agents.executor",
    "app.agents.validator",
    "app.agents.poc_generator",
    "app.rule_engine.context_normalizer",
    "app.rule_engine.owasp_mapper",
    "app.rule_engine.attack_plan_generator",
    "app.rule_engine.payload_binder",
    "app.rule_engine.validator_selector",
    "app.rule_engine.test_case_evaluator",
    "app.rule_engine.safety_enforcer",
    "app.api.v1.endpoints.scans",
    "app.api.v1.endpoints.vulnerabilities",
    "app.api.v1.endpoints.reports",
    "app.api.v1.endpoints.dashboard",
]

ok, fail = 0, 0
for m in modules:
    try:
        __import__(m)
        print(f"  OK    {m}")
        ok += 1
    except Exception as e:
        print(f"  FAIL  {m}  -->  {e}")
        fail += 1

print(f"\nResult: {ok} OK, {fail} FAILED")
