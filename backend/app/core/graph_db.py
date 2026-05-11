"""
Neo4j Graph Database Connection
Manages attack graph relationships and complex queries
"""

import logging
import os
from typing import Dict, Any, List, Optional
try:
    from neo4j import AsyncGraphDatabase, AsyncDriver  # type: ignore
except ImportError:
    AsyncGraphDatabase = None
    AsyncDriver = None

logger = logging.getLogger(__name__)


class GraphDatabase:
    """
    Neo4j connection and query manager for attack graphs
    
    Graph Schema:
    - Nodes: Scan, Endpoint, AttackNode, Finding, Object, AuthGate
    - Edges: DISCOVERED, TARGETS, REQUIRES_AUTH, ACCESSES, PRODUCED
    """
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "rakshaidb_graph_pass")
        self.driver: Optional[Any] = None
        
    async def connect(self):
        """Establish connection to Neo4j"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            
            # Verify connection
            await self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.uri}")
            
            # Create indexes for performance
            await self.create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    async def create_indexes(self):
        """Create indexes on commonly queried properties"""
        async with self.driver.session() as session:
            try:
                # Index on Scan ID
                await session.run(
                    "CREATE INDEX scan_id_idx IF NOT EXISTS FOR (s:Scan) ON (s.id)"
                )
                
                # Index on Endpoint URL
                await session.run(
                    "CREATE INDEX endpoint_url_idx IF NOT EXISTS FOR (e:Endpoint) ON (e.url)"
                )
                
                logger.info("Created Neo4j indexes")
            except Exception as e:
                logger.warning(f"Index creation warning: {e}")
    
    async def execute(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute Cypher query
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of result records
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")
        
        async with self.driver.session() as session:
            try:
                result = await session.run(query, parameters or {})
                records = await result.data()
                return records
            except Exception as e:
                logger.error(f"Query execution failed: {e}\nQuery: {query}")
                raise
    
    async def create_scan_node(self, scan_id: str, metadata: Dict[str, Any]) -> None:
        """Create a Scan node"""
        await self.execute(
            """
            CREATE (s:Scan {
                id: $scan_id,
                target: $target,
                created_at: datetime(),
                status: $status,
                metadata: $metadata
            })
            """,
            {
                "scan_id": scan_id,
                "target": metadata.get("target_url"),
                "status": metadata.get("status", "INITIALIZING"),
                "metadata": str(metadata)
            }
        )
    
    async def add_endpoint(
        self,
        scan_id: str,
        endpoint: Dict[str, Any]
    ) -> None:
        """Add discovered endpoint to graph"""
        await self.execute(
            """
            MATCH (s:Scan {id: $scan_id})
            MERGE (e:Endpoint {url: $url})
            SET e.method = $method,
                e.params = $params,
                e.discovered_at = datetime()
            MERGE (s)-[:DISCOVERED]->(e)
            """,
            {
                "scan_id": scan_id,
                "url": endpoint["url"],
                "method": endpoint.get("method", "GET"),
                "params": str(endpoint.get("params", {}))
            }
        )
    
    async def create_attack_node(
        self,
        scan_id: str,
        attack: Dict[str, Any]
    ) -> None:
        """Create attack node in graph"""
        await self.execute(
            """
            MATCH (s:Scan {id: $scan_id})
            CREATE (a:AttackNode {
                id: $attack_id,
                type: $type,
                status: 'PENDING',
                priority: $priority,
                tool: $tool,
                created_at: datetime()
            })
            MERGE (s)-[:PLANNED_ATTACK]->(a)
            
            WITH a
            MATCH (e:Endpoint {url: $target})
            MERGE (a)-[:TARGETS]->(e)
            """,
            {
                "scan_id": scan_id,
                "attack_id": attack["attack_id"],
                "type": attack["type"],
                "priority": attack.get("priority_score", 50),
                "tool": attack.get("tool", "unknown"),
                "target": attack["target"]
            }
        )
    
    async def update_attack_status(
        self,
        attack_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update attack node status"""
        await self.execute(
            """
            MATCH (a:AttackNode {id: $attack_id})
            SET a.status = $status,
                a.updated_at = datetime(),
                a.result = $result
            """,
            {
                "attack_id": attack_id,
                "status": status,
                "result": str(result) if result else None
            }
        )
    
    async def get_unexplored_endpoints(
        self,
        scan_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get endpoints not yet targeted by attacks"""
        results = await self.execute(
            """
            MATCH (s:Scan {id: $scan_id})-[:DISCOVERED]->(e:Endpoint)
            WHERE NOT EXISTS((s)-[:PLANNED_ATTACK]->(:AttackNode)-[:TARGETS]->(e))
            RETURN e.url AS url, e.method AS method, e.params AS params
            LIMIT $limit
            """,
            {"scan_id": scan_id, "limit": limit}
        )
        
        return [
            {
                "url": r["url"],
                "method": r["method"],
                "params": r["params"]
            }
            for r in results
        ]
    
    async def get_scan_statistics(self, scan_id: str) -> Dict[str, int]:
        """Get scan progress statistics"""
        results = await self.execute(
            """
            MATCH (s:Scan {id: $scan_id})
            OPTIONAL MATCH (s)-[:DISCOVERED]->(e:Endpoint)
            OPTIONAL MATCH (s)-[:PLANNED_ATTACK]->(a:AttackNode)
            OPTIONAL MATCH (a)-[:PRODUCED]->(f:Finding)
            RETURN 
                count(DISTINCT e) AS endpoints,
                count(DISTINCT a) AS attacks,
                count(DISTINCT f) AS findings
            """,
            {"scan_id": scan_id}
        )
        
        if results:
            return results[0]
        return {"endpoints": 0, "attacks": 0, "findings": 0}
    
    async def close(self):
        """Close database connection"""
        if self.driver:
            await self.driver.close()
            logger.info("Closed Neo4j connection")


# Singleton instance
_graph_db = None

async def get_graph_db() -> GraphDatabase:
    """Get global graph database instance"""
    global _graph_db
    if _graph_db is None:
        _graph_db = GraphDatabase()
        await _graph_db.connect()
    return _graph_db
