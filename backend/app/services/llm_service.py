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
    from langchain_ollama import OllamaLLM as Ollama
except ImportError:
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
except Exception:
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
        """Load knowledge base YAML files into vector database.
        
        The existing knowledge-base lives at the PROJECT ROOT level
        (e.g. ``knowledge-base/payloads/injection/xss.yaml``).

        Payload YAML files use a deeply-nested structure::

            payload_category: "xss"
            basic_payloads:
              - "<script>alert('XSS')</script>"
              - "<svg onload=alert('XSS')>"
            filter_bypass:
              no_script_tag:
                - "<img src=x onerror=alert('XSS')>"

        This loader walks the entire YAML tree, extracts every leaf
        string that looks like a payload, and inserts it into ChromaDB
        with a rich semantic description built from:
          • the file-level ``payload_category`` and ``owasp_2025``
          • the YAML key path (e.g. ``filter_bypass > no_script_tag``)

        This enables Agentic RAG: vector search → LLM selection.
        """
        try:
            import yaml
            import os
            
            # ── Resolve KB path ────────────────────────────────────────────
            # The KB is at the PROJECT ROOT, one level above backend/
            backend_dir = Path(__file__).resolve().parents[2]  # .../backend
            project_root = backend_dir.parent                  # .../NeuroPentWeb
            candidates = [
                project_root / os.getenv("KNOWLEDGE_BASE_PATH", "knowledge-base"),
                project_root / "knowledge-base",
                backend_dir / "knowledge-base",                # legacy fallback
                Path("/app/knowledge-base"),                   # Docker fallback
            ]
            kb_path = next((p for p in candidates if p.exists()), None)
            
            if kb_path is None:
                logger.warning(f"Knowledge base not found in any of: {[str(c) for c in candidates]}")
                return

            logger.info(f"Loading knowledge base from: {kb_path}")

            # ── Recursive payload extractor ────────────────────────────────
            def _extract_payloads(node, key_path: list, category: str, owasp: str):
                """Walk the YAML tree and yield (description, payload_str) tuples."""
                if isinstance(node, str):
                    # Leaf string — this is a payload
                    path_label = " > ".join(key_path) if key_path else "general"
                    desc = (
                        f"{category} {path_label} payload"
                        f"{' (OWASP ' + owasp + ')' if owasp else ''}"
                    )
                    yield (desc, node, category)

                elif isinstance(node, list):
                    for idx, item in enumerate(node):
                        yield from _extract_payloads(item, key_path, category, owasp)

                elif isinstance(node, dict):
                    for key, value in node.items():
                        # Skip non-payload metadata keys
                        if key in (
                            "payload_category", "owasp_2025", "cwe", "severity",
                            "version", "description", "prevention", "tools",
                            "references", "testing_steps", "note", "comment",
                            "csp_bypass",
                        ):
                            continue
                        yield from _extract_payloads(
                            value, key_path + [str(key)], category, owasp
                        )

            # ── Walk all YAML files under payloads/ ────────────────────────
            payload_texts = []
            payload_metadatas = []
            general_documents = []

            payloads_dir = kb_path / "payloads"
            all_yaml_files = list(kb_path.rglob("*.yaml"))

            for yaml_file in all_yaml_files:
                try:
                    with open(yaml_file, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)

                    if not isinstance(data, dict):
                        continue

                    # Check if this is a payload/test-case file
                    test_cases_dir = kb_path / "test-cases"
                    is_payload_file = (
                        "payload_category" in data
                        or "test_category" in data
                        or "test_cases" in data
                        or str(yaml_file).startswith(str(payloads_dir))
                        or str(yaml_file).startswith(str(test_cases_dir))
                    )

                    if is_payload_file:
                        category = (
                            data.get("payload_category")
                            or data.get("test_category")
                            or data.get("subcategory")
                            or yaml_file.stem
                        )
                        owasp = data.get("owasp_2025", "")

                        count = 0
                        for desc, payload_str, cat in _extract_payloads(data, [], category, owasp):
                            # Skip very short strings that are probably labels
                            if len(payload_str) < 2:
                                continue
                            payload_texts.append(desc)
                            payload_metadatas.append({
                                "source": str(yaml_file.relative_to(kb_path)),
                                "type": "payload",
                                "payload": payload_str,
                                "category": cat.upper(),
                            })
                            count += 1

                        logger.info(
                            f"Extracted {count} payloads from "
                            f"{yaml_file.relative_to(kb_path)} "
                            f"(category={category})"
                        )
                    else:
                        # General KB document — chunk as text
                        with open(yaml_file, "r", encoding="utf-8") as f:
                            content = f.read()
                        general_documents.append({
                            "content": content,
                            "metadata": {
                                "source": str(yaml_file.relative_to(kb_path)),
                                "type": "knowledge_base",
                            },
                        })

                except Exception as e:
                    logger.error(f"Failed to load {yaml_file}: {e}")

            # ── Build text + metadata lists for ChromaDB ───────────────────
            texts = list(payload_texts)
            metadatas = list(payload_metadatas)

            if general_documents and RecursiveCharacterTextSplitter:
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                )
                for doc in general_documents:
                    chunks = text_splitter.split_text(doc["content"])
                    texts.extend(chunks)
                    metadatas.extend([doc["metadata"]] * len(chunks))

            if texts:
                # Create vector store (in-memory fallback if server unavailable)
                try:
                    chroma_client = chromadb.HttpClient(host="chromadb", port=8000)
                    self.vector_store = Chroma(
                        client=chroma_client,
                        collection_name="rakshaidb_knowledge",
                        embedding_function=self.embeddings,
                    )
                except Exception:
                    logger.warning("ChromaDB server unavailable — using in-memory vector store")
                    self.vector_store = Chroma(
                        collection_name="rakshaidb_knowledge",
                        embedding_function=self.embeddings,
                    )

                # Add documents
                self.vector_store.add_texts(
                    texts=texts,
                    metadatas=metadatas,
                )

                logger.info(
                    f"Loaded {len(payload_texts)} payloads + "
                    f"{len(texts) - len(payload_texts)} KB chunks into vector store"
                )
                
        except Exception as e:
            logger.error(f"Failed to initialize knowledge base: {e}")

    # ── Agentic RAG: Retrieve → Think → Select ──────────────────────────

    async def get_agentic_rag_payloads(
        self,
        context: str,
        k_retrieve: int = 10,
        k_select: int = 3,
    ) -> List[str]:
        """Agentic RAG payload selection.

        Phase 1 — Retrieve:
            Fast vector similarity search pulls the top *k_retrieve* payload
            descriptions from ChromaDB and returns their exact payload strings.

        Phase 2 — Think (Agentic):
            The LLM reviews those candidates against the concrete endpoint
            context and picks the best *k_select* payloads to actually fire.

        Falls back to pure vector results when the LLM is unavailable.
        """
        if not self.vector_store:
            logger.warning("Vector store not initialized — cannot perform Agentic RAG")
            return []

        try:
            # ── Phase 1: Retrieve (vector math — milliseconds) ──────────
            docs = self.vector_store.similarity_search(
                context,
                k=k_retrieve,
                filter={"type": "payload"},  # only search payload entries
            )
            retrieved = [
                {
                    "payload": doc.metadata.get("payload", ""),
                    "description": doc.page_content,
                    "category": doc.metadata.get("category", ""),
                }
                for doc in docs
                if "payload" in doc.metadata
            ]

            if not retrieved:
                logger.info(f"[agentic-rag] No payloads found for context: {context[:80]}")
                return []

            logger.info(
                f"[agentic-rag] Retrieved {len(retrieved)} candidate payloads "
                f"for context: {context[:80]}"
            )

            # ── Phase 2: Think (LLM reasoning — seconds) ────────────────
            if self.llm_strategic or self.llm_analysis:
                selection_prompt = f"""You are an expert penetration tester selecting exploit payloads.

TARGET CONTEXT:
{context}

CANDIDATE PAYLOADS (retrieved from your validated arsenal):
{json.dumps(retrieved, indent=2)}

INSTRUCTIONS:
1. Analyze the target context (parameter name, type, technology hints).
2. Select exactly {k_select} payloads from the candidates that are most
   likely to succeed against this specific target.
3. Prefer payloads that match the parameter type (string vs integer),
   the likely database engine, and the injection context.

Return ONLY a JSON array of the selected payload strings, nothing else.
Example: ["payload1", "payload2", "payload3"]
"""
                try:
                    result = await self.analyze(
                        selection_prompt,
                        response_format="json",
                        use_knowledge_base=False,  # don't re-RAG the prompt
                    )
                    if isinstance(result, list):
                        logger.info(f"[agentic-rag] LLM selected {len(result)} payloads")
                        return result
                except Exception as llm_err:
                    logger.warning(f"[agentic-rag] LLM selection failed, using vector results: {llm_err}")

            # ── Fallback: return top-k from vector search directly ──────
            fallback = [r["payload"] for r in retrieved[:k_select]]
            logger.info(f"[agentic-rag] Falling back to top-{k_select} vector results")
            return fallback

        except Exception as e:
            logger.error(f"[agentic-rag] Agentic RAG failed: {e}")
            return []
    
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
                model_name = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
                ollama_url = f"{self.ollama_base_url}/api/generate"
                logger.info(f"LangChain strategic model missing. Trying direct Ollama API to {ollama_url} with {model_name}")
                
                req_data = {
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 2048}
                }
                
                if response_format == "json":
                    req_data["format"] = "json"
                
                resp = requests.post(ollama_url, json=req_data, timeout=None)
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
            raise RuntimeError("LLM analysis model not available — cannot generate PoC explanation")
    
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
                model_name = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
                ollama_url = f"{self.ollama_base_url}/api/generate"
                logger.info(f"LangChain analysis model missing. Trying direct Ollama API to {ollama_url} with {model_name}")
                
                req_data = {
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.5, "num_predict": 4096}
                }
                
                resp = requests.post(ollama_url, json=req_data, timeout=None)
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


# Singleton instance
_llm_service = None

async def get_llm_service() -> LLMService:
    """Get global LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
        await _llm_service.initialize()
    return _llm_service
