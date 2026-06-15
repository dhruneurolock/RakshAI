"""
Graph Database Abstraction Layer using Apache AGE via psycopg2
"""

import logging
from typing import Dict, Any, List, Optional
import json
import psycopg2

logger = logging.getLogger(__name__)


class GraphDatabase:
    """
    Apache AGE backed Graph Database manager.
    Connects to the agedb Docker container.
    """

    def __init__(self):
        self._connected = False
        # Uses docker-compose exposed port 5433
        self.conn_str = "postgresql://neuropent:neuropent_graph_pass@127.0.0.1:5433/neuropent_graph"
        self.graph_name = "neuropent_graph"
        logger.info("GraphDatabase initialized (Apache AGE Backend)")

    async def connect(self):
        """Initialize AGE connection and graph"""
        try:
            self._ensure_graph()
            self._connected = True
            logger.info("✅ Connected to Apache AGE backend")
        except Exception as e:
            logger.error(f"Failed to connect to Apache AGE: {e}")

    def _ensure_graph(self):
        """Ensures the AGE extension is loaded and the graph exists"""
        try:
            with psycopg2.connect(self.conn_str) as conn:
                with conn.cursor() as cur:
                    cur.execute("LOAD 'age';")
                    cur.execute("SET search_path = ag_catalog, \"$user\", public;")
                    try:
                        cur.execute(f"SELECT create_graph('{self.graph_name}');")
                        conn.commit()
                    except Exception:
                        conn.rollback()  # Graph already exists
        except Exception as e:
            raise Exception(f"Failed to ensure graph: {e}")

    async def ensure_connected(self):
        """Ensure connection is alive"""
        if not self._connected:
            await self.connect()
        return self._connected

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def create_indexes(self):
        pass

    async def execute(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Raw cypher execution"""
        return self._run_cypher(query, parameters)

    def _run_cypher(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Helper to run a Cypher query using AGE SQL wrapper"""
        # DO NOT escape single quotes when using $$ in postgres
        sql = f"SELECT * FROM cypher('{self.graph_name}', $$ {cypher} $$) AS (res agtype);"
        
        try:
            with psycopg2.connect(self.conn_str) as conn:
                with conn.cursor() as cur:
                    cur.execute("LOAD 'age';")
                    cur.execute("SET search_path = ag_catalog, \"$user\", public;")
                    cur.execute(sql)
                    try:
                        results = cur.fetchall()
                        conn.commit()
                        return results
                    except Exception:
                        conn.commit()
                        return []
        except Exception as e:
            logger.error(f"Cypher execution failed: {e} | Query: {cypher}")
            return []

    async def create_scan_node(self, scan_id: str, metadata: Dict[str, Any]) -> None:
        """Create or update a Scan in AGE"""
        target_url = metadata.get("target_url", "")
        status = metadata.get("status", "running")
        cypher = f"MERGE (s:Scan {{scan_id: '{scan_id}'}}) SET s.target_url = '{target_url}', s.status = '{status}' RETURN s"
        self._run_cypher(cypher)

    async def add_endpoint(self, scan_id: str, endpoint: Dict[str, Any]) -> None:
        """Add discovered endpoint to AGE graph"""
        url = endpoint.get("url", "")
        method = endpoint.get("method", "GET")
        cypher = f"""
        MATCH (s:Scan {{scan_id: '{scan_id}'}})
        MERGE (e:Endpoint {{url: '{url}', method: '{method}'}})
        MERGE (s)-[:HAS_ENDPOINT]->(e)
        RETURN e
        """
        self._run_cypher(cypher)

    async def create_attack_node(self, scan_id: str, attack: Dict[str, Any]) -> None:
        """Create attack node in AGE graph"""
        attack_id = attack.get("id", "")
        title = attack.get("title", "")
        cypher = f"""
        MATCH (s:Scan {{scan_id: '{scan_id}'}})
        MERGE (a:Attack {{attack_id: '{attack_id}'}})
        SET a.title = '{title}', a.status = 'pending'
        MERGE (s)-[:HAS_ATTACK]->(a)
        RETURN a
        """
        self._run_cypher(cypher)

    async def update_attack_status(
        self,
        attack_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update attack node status in AGE"""
        cypher = f"""
        MATCH (a:Attack {{attack_id: '{attack_id}'}})
        SET a.status = '{status}'
        RETURN a
        """
        self._run_cypher(cypher)

    async def get_unexplored_endpoints(
        self,
        scan_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        return []

    async def get_scan_endpoints(self, scan_id: str) -> List[Dict[str, Any]]:
        return []

    async def get_scan_statistics(self, scan_id: str) -> Dict[str, int]:
        return {"endpoints": 0, "attacks": 0, "findings": 0}

    async def close(self):
        """Close database connection"""
        self._connected = False
        logger.info("Closed AGE connection")


async def get_graph_db() -> GraphDatabase:
    """Get an Apache AGE graph database instance"""
    db = GraphDatabase()
    await db.connect()
    return db
