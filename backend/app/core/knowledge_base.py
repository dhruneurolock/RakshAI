"""
Knowledge Base Loader Utility
Centralized loader for all YAML files in the knowledge base
"""
import yaml
import structlog
from typing import Dict, List, Any, Optional
from pathlib import Path
from functools import lru_cache

logger = structlog.get_logger()


class KnowledgeBaseLoader:
    """
    Centralized loader for all knowledge base YAML files.
    Provides caching and validation for test cases, payloads, validators, and metadata.
    """
    
    def __init__(self, knowledge_base_path: str = "./knowledge-base"):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.logger = logger.bind(component="KnowledgeBaseLoader")
        
        # Cache structures
        self.test_cases: Dict[str, List[Dict]] = {}
        self.payloads: Dict[str, List[Dict]] = {}
        self.validators: Dict[str, Dict] = {}
        self.metadata: Dict[str, Dict] = {}
        
        # Load all resources
        self._validate_structure()
        self._load_all()
    
    def _validate_structure(self):
        """Validate that all required directories exist"""
        required_dirs = [
            "test-cases",
            "payloads", 
            "validators",
            "metadata"
        ]
        
        for dir_name in required_dirs:
            dir_path = self.knowledge_base_path / dir_name
            if not dir_path.exists():
                self.logger.error(
                    "Required directory missing", 
                    directory=dir_name,
                    path=str(dir_path)
                )
                raise FileNotFoundError(f"Required directory not found: {dir_path}")
    
    def _load_all(self):
        """Load all knowledge base resources"""
        self.logger.info("Loading knowledge base...", path=str(self.knowledge_base_path))
        
        self._load_test_cases()
        self._load_payloads()
        self._load_validators()
        self._load_metadata()
        
        self._log_statistics()
    
    def _load_test_cases(self):
        """Load all test cases from YAML files"""
        test_cases_dir = self.knowledge_base_path / "test-cases"
        total_loaded = 0
        
        # Expected OWASP categories
        owasp_categories = [
            "A01-broken-access-control",
            "A02-security-misconfiguration",
            "A03-software-supply-chain",
            "A04-crypto-failures",
            "A05-injection",
            "A06-insecure-design",
            "A07-auth-failures",
            "A08-software-data-integrity",
            "A09-logging-alerting",
            "A10-exceptional-conditions",
            "A10-ssrf"
        ]
        
        for category_dir in test_cases_dir.iterdir():
            if category_dir.is_dir():
                category = category_dir.name
                self.test_cases[category] = []
                
                # Load each YAML file
                for yaml_file in category_dir.glob("*.yaml"):
                    try:
                        with open(yaml_file, 'r', encoding='utf-8') as f:
                            content = yaml.safe_load(f)
                            
                            if content:
                                # Add metadata
                                content['_source_file'] = yaml_file.name
                                content['_category'] = category
                                
                                self.test_cases[category].append(content)
                                total_loaded += 1
                    except Exception as e:
                        self.logger.error(
                            "Failed to load test case",
                            file=yaml_file.name,
                            category=category,
                            error=str(e)
                        )
        
        self.logger.info(
            "Test cases loaded",
            total=total_loaded,
            categories=len(self.test_cases)
        )
    
    def _load_payloads(self):
        """Load all payloads from YAML files"""
        payloads_dir = self.knowledge_base_path / "payloads"
        total_payloads = 0
        
        # Recursively load all payload files
        for yaml_file in payloads_dir.rglob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                    
                    if content:
                        # Create hierarchical key: category/type
                        relative_path = yaml_file.relative_to(payloads_dir)
                        category = relative_path.parent.name if relative_path.parent.name != "payloads" else "general"
                        payload_type = yaml_file.stem
                        
                        key = f"{category}/{payload_type}"
                        
                        # Extract payloads list
                        if "payloads" in content:
                            payloads_list = content["payloads"]
                            self.payloads[key] = payloads_list
                            total_payloads += len(payloads_list)
                        else:
                            # Entire file is payload data
                            self.payloads[key] = [content]
                            total_payloads += 1
                            
            except Exception as e:
                self.logger.error(
                    "Failed to load payloads",
                    file=str(yaml_file),
                    error=str(e)
                )
        
        self.logger.info(
            "Payloads loaded",
            total_payloads=total_payloads,
            payload_files=len(self.payloads)
        )
    
    def _load_validators(self):
        """Load all validators from YAML files"""
        validators_dir = self.knowledge_base_path / "validators"
        
        # Expected validator files
        expected_validators = [
            "auth_indicators",
            "data-leak",
            "error-patterns",
            "reflection",
            "sql_errors",
            "status-codes",
            "xss_reflections"
        ]
        
        for yaml_file in validators_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                    
                    if content:
                        validator_type = yaml_file.stem
                        self.validators[validator_type] = content
                        
            except Exception as e:
                self.logger.error(
                    "Failed to load validator",
                    file=yaml_file.name,
                    error=str(e)
                )
        
        self.logger.info(
            "Validators loaded",
            total=len(self.validators)
        )
    
    def _load_metadata(self):
        """Load all metadata files"""
        metadata_dir = self.knowledge_base_path / "metadata"
        
        # Expected metadata files
        metadata_files = [
            "compliance",
            "confidence-scoring",
            "cvss",
            "cwe",
            "cwe_comprehensive",
            "owasp",
            "owasp_top10_2025",
            "owasp_comprehensive",
            "payload-safety",
            "response-comparison",
            "severity",
            "test-payload-binding"
        ]
        
        for yaml_file in metadata_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                    
                    if content:
                        metadata_type = yaml_file.stem
                        self.metadata[metadata_type] = content
                        
            except Exception as e:
                self.logger.error(
                    "Failed to load metadata",
                    file=yaml_file.name,
                    error=str(e)
                )
        
        self.logger.info(
            "Metadata loaded",
            total=len(self.metadata)
        )
    
    def _log_statistics(self):
        """Log comprehensive statistics about loaded data"""
        self.logger.info(
            "Knowledge base loaded successfully",
            test_case_categories=len(self.test_cases),
            total_test_files=sum(len(cases) for cases in self.test_cases.values()),
            payload_types=len(self.payloads),
            total_payloads=sum(len(p) if isinstance(p, list) else 1 for p in self.payloads.values()),
            validators=len(self.validators),
            metadata_types=len(self.metadata)
        )
    
    # === Getter Methods ===
    
    def get_test_cases_for_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all test cases for a specific OWASP category"""
        return self.test_cases.get(category, [])
    
    def get_all_test_cases(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all test cases organized by category"""
        return self.test_cases
    
    def get_payloads_for_type(self, payload_type: str) -> List[Dict[str, Any]]:
        """
        Get payloads for a specific type
        payload_type format: "category/type" (e.g., "injection/sql-injection")
        """
        return self.payloads.get(payload_type, [])
    
    def get_all_payloads(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all payloads organized by type"""
        return self.payloads
    
    def get_validator(self, validator_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific validator by name"""
        return self.validators.get(validator_name)
    
    def get_all_validators(self) -> Dict[str, Dict[str, Any]]:
        """Get all validators"""
        return self.validators
    
    def get_metadata(self, metadata_type: str) -> Optional[Dict[str, Any]]:
        """Get specific metadata"""
        return self.metadata.get(metadata_type)
    
    def get_all_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Get all metadata"""
        return self.metadata
    
    # === Utility Methods ===
    
    def get_owasp_mapping(self) -> Dict[str, Any]:
        """Get OWASP Top 10:2025 mapping"""
        return self.metadata.get("owasp_top10_2025", {})
    
    def get_cwe_mapping(self) -> Dict[str, Any]:
        """Get CWE mapping"""
        return self.metadata.get("cwe", {})
    
    def get_cvss_config(self) -> Dict[str, Any]:
        """Get CVSS scoring configuration"""
        return self.metadata.get("cvss", {})
    
    def get_severity_levels(self) -> Dict[str, Any]:
        """Get severity level definitions"""
        return self.metadata.get("severity", {})
    
    def search_payloads(self, 
                       vulnerability_type: Optional[str] = None,
                       tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Search for payloads matching criteria
        
        Args:
            vulnerability_type: Type of vulnerability (e.g., "sql-injection", "xss")
            tags: List of tags to match
        
        Returns:
            List of matching payloads
        """
        results = []
        
        for payload_key, payload_list in self.payloads.items():
            # Filter by vulnerability type
            if vulnerability_type and vulnerability_type not in payload_key:
                continue
            
            for payload in payload_list:
                # Filter by tags
                if tags:
                    payload_tags = payload.get("tags", [])
                    if not any(tag in payload_tags for tag in tags):
                        continue
                
                results.append({
                    **payload,
                    "_source": payload_key
                })
        
        return results
    
    def validate_loaded_data(self) -> Dict[str, bool]:
        """
        Validate that all essential data is loaded
        
        Returns:
            Dictionary with validation results
        """
        validation = {
            "test_cases_present": len(self.test_cases) > 0,
            "payloads_present": len(self.payloads) > 0,
            "validators_present": len(self.validators) >= 6,
            "owasp_metadata_present": "owasp_top10_2025" in self.metadata,
            "cwe_metadata_present": "cwe" in self.metadata,
            "cvss_metadata_present": "cvss" in self.metadata,
            "severity_metadata_present": "severity" in self.metadata
        }
        
        validation["all_valid"] = all(validation.values())
        
        return validation


# Singleton instance
_kb_loader_instance = None


def get_knowledge_base_loader(knowledge_base_path: str = "./knowledge-base") -> KnowledgeBaseLoader:
    """
    Get singleton instance of KnowledgeBaseLoader
    
    Args:
        knowledge_base_path: Path to knowledge base directory
    
    Returns:
        KnowledgeBaseLoader instance
    """
    global _kb_loader_instance
    
    if _kb_loader_instance is None:
        _kb_loader_instance = KnowledgeBaseLoader(knowledge_base_path)
    
    return _kb_loader_instance
