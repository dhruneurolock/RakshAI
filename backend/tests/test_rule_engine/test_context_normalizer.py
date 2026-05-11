import pytest
from app.rule_engine.context_normalizer import ContextNormalizer


@pytest.fixture
def normalizer():
    return ContextNormalizer()


def test_normalize_endpoint_basic(normalizer):
    """Test basic endpoint normalization"""
    raw_endpoint = {
        "url": "https://example.com/api/users?id=123",
        "method": "GET",
        "parameters": {"id": "123"}
    }
    
    normalized = normalizer.normalize_endpoint(raw_endpoint)
    
    assert normalized["url"] == "https://example.com/api/users"
    assert normalized["method"] == "GET"
    assert "id" in normalized["parameters"]
    assert normalized["parameters"]["id"]["type"] == "integer"


def test_infer_parameter_type(normalizer):
    """Test parameter type inference"""
    assert normalizer._infer_parameter_type("123") == "integer"
    assert normalizer._infer_parameter_type("test@example.com") == "email"
    assert normalizer._infer_parameter_type("https://example.com") == "url"
    assert normalizer._infer_parameter_type("2024-01-20") == "date"
    assert normalizer._infer_parameter_type("random text") == "string"


def test_detect_technology(normalizer):
    """Test technology detection"""
    headers = {
        "Server": "Apache/2.4.41",
        "X-Powered-By": "PHP/7.4.3"
    }
    
    technologies = normalizer._detect_technology(headers, {})
    
    assert "apache" in technologies
    assert "php" in technologies


def test_is_injectable_parameter(normalizer):
    """Test injectable parameter detection"""
    assert normalizer._is_injectable_parameter("integer") is True
    assert normalizer._is_injectable_parameter("string") is True
    assert normalizer._is_injectable_parameter("boolean") is False
