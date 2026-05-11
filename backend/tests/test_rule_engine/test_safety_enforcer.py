import pytest
from app.rule_engine.safety_enforcer import SafetyEnforcer


@pytest.fixture
def enforcer():
    return SafetyEnforcer()


def test_blocks_destructive_sql(enforcer):
    """Test that destructive SQL payloads are blocked"""
    payloads = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1'; DELETE FROM accounts; --",
        "admin'; TRUNCATE TABLE data; --"
    ]
    
    for payload in payloads:
        assert enforcer.is_safe(payload) is False


def test_blocks_command_injection(enforcer):
    """Test that command injection payloads are blocked"""
    payloads = [
        "test; rm -rf /",
        "user && shutdown -h now",
        "config | del /f /q *.*"
    ]
    
    for payload in payloads:
        assert enforcer.is_safe(payload) is False


def test_allows_safe_payloads(enforcer):
    """Test that safe payloads are allowed"""
    safe_payloads = [
        "' OR '1'='1",  # Basic SQL injection test (non-destructive)
        "<script>alert('XSS')</script>",  # XSS test
        "../../../etc/passwd",  # Path traversal test
        "http://internal-server.local"  # SSRF test
    ]
    
    for payload in safe_payloads:
        assert enforcer.is_safe(payload) is True


def test_blocks_mixed_case(enforcer):
    """Test that case variations of destructive commands are blocked"""
    assert enforcer.is_safe("'; DrOp TaBlE users; --") is False
    assert enforcer.is_safe("user && ShUtDoWn -h now") is False
