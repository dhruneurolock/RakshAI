"""
LLM Service - Intelligence Layer
Ollama + LangChain for autonomous reasoning
CRITICAL: LLM is used ONLY for analysis, NOT for direct execution
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    from langchain_community.llms import Ollama
except ImportError:
    Ollama = None
try:
    from langchain_community.vectorstores import Chroma
except ImportError:
    Chroma = None
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
except ImportError:
    HuggingFaceEmbeddings = None
try:
    from langchain_core.prompts import PromptTemplate
except ImportError:
    PromptTemplate = None
try:
    from langchain_core.language_models import LLMChain  # type: ignore
except ImportError:
    LLMChain = None
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    RecursiveCharacterTextSplitter = None
try:
    import chromadb  # type: ignore
except ImportError:
    chromadb = None

logger = logging.getLogger(__name__)


class LLMService:
    """
    LLM-powered intelligence for RakshAI
    
    Capabilities:
    - Strategic attack planning
    - Vulnerability analysis
    - PoC explanation generation
    - Knowledge base RAG (Retrieval Augmented Generation)
    - Adaptive re-prioritization
    
    Security:
    - No direct system access
    - No command execution
    - Output parsing and validation
    """
    
    def __init__(self):
        # LLM Configuration
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.chroma_url = os.getenv("CHROMA_URL", "http://localhost:8001")
        self.model_strategic = os.getenv(
            "OLLAMA_MODEL_STRATEGY",
            os.getenv("OLLAMA_MODEL", "")
        )
        self.model_analysis = os.getenv(
            "OLLAMA_MODEL_ANALYSIS",
            os.getenv("OLLAMA_MODEL", self.model_strategic)
        )
        
        # Initialize models
        self.llm_strategic = None  # Strategic planning model
        self.llm_analysis = None   # Detailed analysis model
        
        # Vector store for knowledge base
        self.vector_store = None
        self.embeddings = None
        
        logger.info(f"Initializing LLM Service with Ollama at {self.ollama_base_url}")
    
    async def initialize(self):
        """Initialize LLM models and vector database"""
        try:
            if not self.model_strategic:
                raise ValueError("OLLAMA_MODEL (or OLLAMA_MODEL_STRATEGY) is not configured")

            # Initialize strategic planning model
            self.llm_strategic = Ollama(
                base_url=self.ollama_base_url,
                model=self.model_strategic,
                temperature=0.3,  # More deterministic
                num_predict=2048
            )
            
            # Initialize detailed analysis model
            self.llm_analysis = Ollama(
                base_url=self.ollama_base_url,
                model=self.model_analysis,
                temperature=0.5,
                num_predict=4096
            )
            
            # Initialize embeddings for RAG
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            
            # Initialize ChromaDB for knowledge base
            await self.initialize_knowledge_base()
            
            logger.info("LLM Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM Service: {e}")
            # Fallback to mock mode for development
            logger.warning("Running in MOCK MODE - LLM responses will be simulated")
            self.llm_strategic = None
            self.llm_analysis = None
    
    async def initialize_knowledge_base(self):
        """Load knowledge base YAML files into vector database"""
        try:
            kb_path = Path("/app/knowledge-base")
            
            if not kb_path.exists():
                logger.warning(f"Knowledge base not found at {kb_path}")
                return
            
            # Load all YAML files from knowledge base
            documents = []
            
            for yaml_file in kb_path.rglob("*.yaml"):
                try:
                    with open(yaml_file, 'r') as f:
                        content = f.read()
                        documents.append({
                            "content": content,
                            "metadata": {
                                "source": str(yaml_file.relative_to(kb_path)),
                                "type": "knowledge_base"
                            }
                        })
                except Exception as e:
                    logger.error(f"Failed to load {yaml_file}: {e}")
            
            if documents:
                # Split documents into chunks
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200
                )
                
                texts = []
                metadatas = []
                
                for doc in documents:
                    chunks = text_splitter.split_text(doc["content"])
                    texts.extend(chunks)
                    metadatas.extend([doc["metadata"]] * len(chunks))
                
                # Create vector store
                chroma_client = chromadb.HttpClient(host="chromadb", port=8000)
                
                self.vector_store = Chroma(
                    client=chroma_client,
                    collection_name="rakshaidb_knowledge",
                    embedding_function=self.embeddings
                )
                
                # Add documents
                self.vector_store.add_texts(
                    texts=texts,
                    metadatas=metadatas
                )
                
                logger.info(f"Loaded {len(documents)} documents ({len(texts)} chunks) into knowledge base")
                
        except Exception as e:
            logger.error(f"Failed to initialize knowledge base: {e}")
    
    async def analyze(
        self,
        prompt: str,
        response_format: str = "text",
        use_knowledge_base: bool = True
    ) -> Any:
        """
        Analyze using LLM with optional RAG
        
        Args:
            prompt: Input prompt
            response_format: "text" or "json"
            use_knowledge_base: Whether to use RAG
            
        Returns:
            LLM response (text or parsed JSON)
        """
        try:
            # Add knowledge base context if requested
            if use_knowledge_base and self.vector_store:
                relevant_docs = self.vector_store.similarity_search(prompt, k=3)
                kb_context = "\n\n".join([doc.page_content for doc in relevant_docs])
                prompt = f"Knowledge Base Context:\n{kb_context}\n\nQuestion:\n{prompt}"
            
            # Use strategic model
            if self.llm_strategic:
                response = await self.llm_strategic.apredict(prompt)
            else:
                # Direct HTTP fallback
                import requests
                model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:latest")
                ollama_url = f"{self.ollama_base_url}/api/generate"
                logger.info(f"LangChain strategic model missing. Trying direct Ollama API to {ollama_url} with {model_name}")
                
                req_data = {
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 2048}
                }
                
                resp = requests.post(ollama_url, json=req_data, timeout=60)
                if resp.status_code == 200:
                    response = resp.json().get("response", "")
                else:
                    raise Exception(f"Ollama direct API failed: {resp.status_code} {resp.text}")
            
            # Parse JSON if requested
            if response_format == "json":
                try:
                    # Extract JSON from response (LLM might add extra text)
                    json_start = response.find("{")
                    json_end = response.rfind("}") + 1
                    if json_start != -1 and json_end != 0:
                        json_str = response[json_start:json_end]
                        return json.loads(json_str)
                    
                    # If we asked for json and couldn't parse it, throw exception
                    raise ValueError(f"Could not extract JSON from response: {response[:100]}...")
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON from LLM response: {response}")
                    raise
            
            return response
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            raise  # Do not swallow errors or return fake data
    
    async def generate_attack_plan(
        self,
        recon_data: Dict[str, Any],
        target_url: str
    ) -> Dict[str, Any]:
        """
        Generate attack plan based on reconnaissance data
        
        Args:
            recon_data: Discovered endpoints and technologies
            target_url: Target URL
            
        Returns:
            Attack plan with prioritized vectors
        """
        prompt = f"""
Analyze reconnaissance data and create attack plan.

Target: {target_url}

Discovered Data:
{json.dumps(recon_data, indent=2)}

Create a prioritized attack plan focusing on:
1. OWASP Top 10:2025 vulnerabilities
2. Business logic flaws
3. Common misconfigurations

Return JSON format:
{{
    "high_priority": [
        {{
            "attack_id": "unique_id",
            "type": "vulnerability_type",
            "target": "specific_endpoint",
            "rationale": "why_this_is_priority",
            "priority_score": 1-100,
            "tool": "recommended_tool",
            "estimated_time": "seconds"
        }}
    ],
    "medium_priority": [],
    "low_priority": []
}}
"""
        return await self.analyze(prompt, response_format="json")
    
    async def generate_poc_explanation(
        self,
        vulnerability: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable PoC explanation
        
        Args:
            vulnerability: Vulnerability details
            
        Returns:
            Detailed explanation string
        """
        prompt = f"""
Generate a detailed, professional proof-of-concept explanation for this vulnerability.

Vulnerability Details:
Type: {vulnerability.get('type')}
Endpoint: {vulnerability.get('endpoint')}
Severity: {vulnerability.get('severity')}
Evidence: {json.dumps(vulnerability.get('evidence', {}), indent=2)}

Include:
1. Executive Summary (2-3 sentences for non-technical audience)
2. Technical Description
3. Step-by-Step Exploitation
4. Business Impact
5. Remediation Recommendations (with code examples if applicable)
6. References (CWE, OWASP, CVE if applicable)

Format in Markdown.
"""
        
        if self.llm_analysis:
            return await self.llm_analysis.apredict(prompt)
        else:
            return self._mock_poc_explanation(vulnerability)
    
    async def reprioritize(
        self,
        unexplored_endpoints: List[Dict],
        current_findings: List[Dict]
    ) -> Dict[str, Any]:
        """
        Adaptive re-prioritization based on current findings
        
        Args:
            unexplored_endpoints: Endpoints not yet tested
            current_findings: Validated vulnerabilities found so far
            
        Returns:
            Updated priority strategy
        """
        prompt = f"""
Adaptive attack re-prioritization.

Current Findings:
{json.dumps(current_findings, indent=2)}

Unexplored Endpoints:
{json.dumps(unexplored_endpoints, indent=2)}

Based on patterns in current findings, re-prioritize unexplored endpoints.

If IDOR was found on /api/orders/{{id}}, similar patterns might exist on:
- /api/invoices/{{id}}
- /api/users/{{id}}
- /profile/{{id}}

Return JSON:
{{
    "recommended_tests": [
        {{
            "endpoint": "endpoint_url",
            "attack_type": "type",
            "priority": 1-100,
            "reason": "why_prioritized"
        }}
    ],
    "skip_tests": ["low_priority_endpoints"]
}}
"""
        return await self.analyze(prompt, response_format="json")
    
    async def analyze_false_positive(
        self,
        finding: Dict[str, Any],
        validation_results: List[Dict]
    ) -> Dict[str, Any]:
        """
        Analyze if a finding is a false positive
        
        Args:
            finding: Vulnerability finding
            validation_results: Multiple validation attempts
            
        Returns:
            Analysis with confidence score
        """
        prompt = f"""
Analyze if this is a false positive.

Finding:
{json.dumps(finding, indent=2)}

Validation Results (3 replays):
{json.dumps(validation_results, indent=2)}

Determine:
1. Is this a true positive or false positive?
2. Confidence level (0.0-1.0)
3. Reasoning

Return JSON:
{{
    "is_valid": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "detailed_explanation",
    "requires_manual_review": true/false
}}
"""
        return await self.analyze(prompt, response_format="json")
    
    async def generate_remediation(
        self,
        vulnerability: Dict[str, Any],
        target_technology: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive LLM-based remediation solution with point-wise steps."""
        prompt = f"""
You are a cybersecurity expert providing instant, clear remediation guidance for vulnerabilities.

VULNERABILITY DETAILS:
- Type: {vulnerability.get('type', '')}
- Title: {vulnerability.get('title', '')}
- Description: {vulnerability.get('description', '')}
- Severity: {vulnerability.get('severity', 'medium')}
- OWASP Category: {vulnerability.get('owasp_category', '')}
- Endpoint: {vulnerability.get('endpoint', '')}
- Method: {vulnerability.get('method', '')}
- Evidence: {vulnerability.get('evidence', '')}

TARGET TECHNOLOGY: {target_technology or 'PHP/General'}

GENERATE REMEDIATION WITH THESE EXACT SECTIONS (one per line, numbered):

## Executive Summary
[One paragraph summary]

## Root Cause Analysis
[Explain why this vulnerability exists]

## Remediation Steps
1. [First step - specific and actionable]
2. [Second step - specific and actionable]
3. [Third step - specific and actionable]
4. [Continue with more steps as needed - each one specific and actionable]

## Code Example
[Production-ready code snippet]

## Best Practices
1. [Best practice 1]
2. [Best practice 2]
3. [Best practice 3]

## Testing Instructions
1. [Test step 1]
2. [Test step 2]
3. [Test step 3]

## Timeline
[Implementation time estimate]

## Business Impact if Not Fixed
[Describe the risk]

CRITICAL: Each step must be on its own line starting with "1.", "2.", etc.
Make steps CLEAR, SPECIFIC, and ACTIONABLE for developers.
"""

        if self.llm_analysis:
            response = await self.llm_analysis.apredict(prompt)
        else:
            # Fallback to direct HTTP request to Ollama
            import requests
            try:
                model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:latest")
                ollama_url = f"{self.ollama_base_url}/api/generate"
                logger.info(f"LangChain analysis model missing. Trying direct Ollama API to {ollama_url} with {model_name}")
                
                req_data = {
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.5, "num_predict": 4096}
                }
                
                resp = requests.post(ollama_url, json=req_data, timeout=60)
                if resp.status_code == 200:
                    response = resp.json().get("response", "")
                    logger.info("Direct Ollama API generation successful")
                else:
                    raise Exception(f"Ollama direct API failed: {resp.status_code} {resp.text}")
            except Exception as e:
                logger.error(f"Failed direct Ollama call for remediation: {e}")
                raise

        if isinstance(response, dict):
            return response

        # Format the response for clear point-wise display
        return self._format_text_remediation_to_dict(response)
    
    def _format_text_remediation_to_dict(self, response: str) -> Dict[str, Any]:
        """Convert text-based remediation response into structured dict."""
        sections = self._parse_remediation_sections(response)
        
        # Build remediation dict from parsed sections
        remediation_dict = {
            "status": "success",
            "vulnerability_type": "Custom",
            "mode": "structured"
        }
        
        # Map sections to standard keys
        for section in sections:
            title_lower = section['title'].lower().replace(' ', '_')
            
            if 'executive' in title_lower:
                remediation_dict['executive_summary'] = section['content']
            elif 'root_cause' in title_lower:
                remediation_dict['root_cause'] = section['content']
            elif 'remediation' in title_lower and 'step' in title_lower:
                remediation_dict['remediation_steps'] = section['items'] if section['items'] else [section['content']]
            elif 'code' in title_lower:
                remediation_dict['code_example'] = section['content']
            elif 'best_practice' in title_lower:
                remediation_dict['best_practices'] = section['items'] if section['items'] else [section['content']]
            elif 'testing' in title_lower:
                remediation_dict['testing_instructions'] = section['items'] if section['items'] else [section['content']]
            elif 'timeline' in title_lower:
                remediation_dict['timeline'] = section['content']
            elif 'business' in title_lower or 'impact' in title_lower or 'risk' in title_lower:
                remediation_dict['business_impact'] = section['content']
        
        return remediation_dict
    
    def _parse_remediation_sections(self, text: str) -> List[Dict[str, Any]]:
        """Parse remediation text into structured sections."""
        sections = []
        current_section = None
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a section header (starts with ##)
            if line.startswith('##'):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    'title': line.replace('##', '').strip(),
                    'items': [],
                    'content': ''
                }
            elif current_section:
                # Check if this is a numbered item
                if line and line[0].isdigit() and '. ' in line:
                    try:
                        item_text = line.split('. ', 1)[1].strip()
                        current_section['items'].append(item_text)
                    except:
                        if current_section['content']:
                            current_section['content'] += '\n' + line
                        else:
                            current_section['content'] = line
                elif line:
                    # Regular content line
                    if current_section['content']:
                        current_section['content'] += '\n' + line
                    else:
                        current_section['content'] = line
        
        # Add the last section
        if current_section:
            sections.append(current_section)
        
        return sections

    def _mock_response(self, prompt: str, response_format: str) -> str:
        """Mock response for development without Ollama"""

        if response_format == "json":
            if "attack plan" in prompt.lower():
                return json.dumps({
                    "high_priority": [
                        {
                            "attack_id": "mock_001",
                            "type": "IDOR",
                            "target": "/api/orders/{id}",
                            "rationale": "Mock: Common access control issue",
                            "priority_score": 95,
                            "tool": "custom_idor_tester",
                            "estimated_time": "30"
                        }
                    ],
                    "medium_priority": [],
                    "low_priority": []
                })
            if "strategy" in prompt.lower():
                return json.dumps({
                    "app_type": "web_application",
                    "likely_auth": "JWT or session cookies",
                    "priority_categories": [
                        "A01-Broken-Access-Control",
                        "A03-Injection",
                        "A07-XSS"
                    ],
                    "recon_tools": ["httpx", "katana", "nuclei"],
                    "estimated_endpoints": 50,
                    "risk_level": "MEDIUM"
                })
            return json.dumps({"mock": True, "message": "Development mode"})

        return "Mock LLM response - Ollama not available"

    def _mock_poc_explanation(self, vulnerability: Dict[str, Any]) -> str:
        """Mock PoC explanation"""
        return f"""
# Proof of Concept: {vulnerability.get('type')}

## Executive Summary
A {vulnerability.get('severity')} severity {vulnerability.get('type')} vulnerability was discovered at {vulnerability.get('endpoint')}.

## Technical Description
[Mock PoC - Ollama not available in development mode]

## Exploitation Steps
1. Access endpoint: {vulnerability.get('endpoint')}
2. [Additional steps would be generated by LLM]

## Remediation
[Remediation recommendations would be generated by LLM]
"""

    def _mock_remediation_solution(
        self,
        vulnerability: Dict[str, Any],
        target_technology: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate mock remediation solution for development"""
        vuln_type = vulnerability.get('type', '').upper()

        solutions = {
            'MISSING_CSRF_TOKEN': {
                'executive_summary': 'The application lacks CSRF token protection on POST forms, allowing attackers to perform unauthorized actions on behalf of authenticated users.',
                'root_cause': 'Forms do not implement synchronized token pattern or SameSite cookie protection.',
                'remediation_steps': [
                    'Generate unique CSRF token per session using secure random bytes',
                    'Embed token in all forms as hidden input field',
                    'Validate token on form submission (POST/PUT/DELETE)',
                    'Regenerate token after successful validation',
                    'Set SameSite=Strict on session cookies',
                    'Use HTTPS only with Secure flag'
                ],
                'code_example': """<?php
session_start();
if (empty($_SESSION['csrf_token'])) {
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
}
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (empty($_POST['csrf_token']) || $_POST['csrf_token'] !== $_SESSION['csrf_token']) {
        http_response_code(403);
        die('CSRF token validation failed');
    }
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
}
?>""",
                'best_practices': [
                    'Use framework CSRF middleware',
                    'Implement token rotation on sensitive operations',
                    'Log CSRF token validation failures',
                    'Test with OWASP ZAP or Burp Suite',
                    'Document CSRF policy in security guidelines'
                ],
                'testing_instructions': [
                    'Submit form with invalid token and verify rejection',
                    'Confirm response returns 403 Forbidden',
                    'Test cross-site request behavior',
                    'Verify SameSite cookie behavior'
                ],
                'timeline': '2-4 hours implementation, 1 hour testing',
                'business_impact': 'CRITICAL - Attackers can perform unauthorized actions'
            }
        }

        solution = solutions.get(vuln_type, {
            'executive_summary': f'The {vuln_type} vulnerability requires immediate remediation.',
            'root_cause': 'Insecure coding practices or missing security controls.',
            'remediation_steps': ['Review affected code', 'Apply security best practices', 'Implement proper controls', 'Test remediation thoroughly'],
            'code_example': 'See OWASP guidelines for this vulnerability type',
            'best_practices': ['Follow OWASP Top 10 guidelines', 'Implement code review process', 'Use static analysis tools (SAST)', 'Conduct penetration testing'],
            'testing_instructions': ['Verify fix implementation', 'Retest vulnerability', 'Scan with automated tools'],
            'timeline': '2-4 hours estimated',
            'business_impact': 'Assess risk based on vulnerability severity'
        })

        return {
            'status': 'success',
            'vulnerability_type': vuln_type,
            **solution,
            'mode': 'mock_development'
        }

# Singleton instance
_llm_service = None

async def get_llm_service() -> LLMService:
    """Get global LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
        await _llm_service.initialize()
    return _llm_service
