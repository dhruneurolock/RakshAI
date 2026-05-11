"""
Base Agent Class
All specialized agents inherit from this class
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.redis_client import get_redis
try:
    from app.services.llm_service import LLMService
except Exception:
    LLMService = None
try:
    from app.services.storage_service import StorageService
except Exception:
    StorageService = None
from app.core.graph_db import get_graph_db

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all RakshAI agents
    
    Responsibilities:
    - Event-driven communication via message bus
    - State management
    - Logging and monitoring
    - Error handling and recovery
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.llm_service = None  # Lazy load
        self.storage_service = None
        self.graph_db = None
        self.redis_client = None
        self.start_time = None
        
    async def initialize(self):
        """Initialize agent resources"""
        logger.info(f"Initializing {self.__class__.__name__} (ID: {self.agent_id})")
        self.llm_service = LLMService() if LLMService is not None else None
        self.storage_service = StorageService() if StorageService is not None else None
        
        # Lazy-load graph_db: only connect when actually needed at runtime
        try:
            self.graph_db = await get_graph_db()
        except Exception as e:
            logger.warning(f"Graph DB not available: {e} (will retry on first use)")
            self.graph_db = None
        
        try:
            self.redis_client = await get_redis()
        except Exception as e:
            logger.warning(f"Redis not available: {e} (will retry on first use)")
            self.redis_client = None
        
        self.start_time = datetime.utcnow()
        
    async def emit_progress(self, scan_id: str, event: Dict[str, Any]):
        """
        Emit progress event to message bus
        
        Args:
            scan_id: Scan identifier
            event: Progress event data
        """
        try:
            await self.redis_client.publish(
                f"scan:{scan_id}:progress",
                {
                    "agent": self.agent_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "event": event
                }
            )
        except Exception as e:
            logger.error(f"Failed to emit progress: {e}")
    
    async def log_action(self, scan_id: str, action: str, details: Dict[str, Any]):
        """Log agent action to database"""
        try:
            # Store in Redis for real-time access
            await self.redis_client.lpush(
                f"scan:{scan_id}:log",
                {
                    "agent": self.agent_id,
                    "action": action,
                    "details": details,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to log action: {e}")
    
    @abstractmethod
    async def run(self, scan_id: str, **kwargs) -> Dict[str, Any]:
        """
        Main agent execution method - must be implemented by subclasses
        
        Args:
            scan_id: Scan identifier
            **kwargs: Agent-specific parameters
            
        Returns:
            Dict containing agent execution results
        """
        pass
    
    async def handle_error(self, scan_id: str, error: Exception):
        """Centralized error handling"""
        logger.error(
            f"{self.__class__.__name__} error in scan {scan_id}: {error}",
            exc_info=True
        )
        
        await self.emit_progress(scan_id, {
            "status": "ERROR",
            "error": str(error),
            "agent": self.agent_id
        })
        
    async def cleanup(self):
        """Cleanup agent resources"""
        logger.info(f"Cleaning up {self.__class__.__name__}")
        # Close connections, release resources
        if self.graph_db:
            await self.graph_db.close()
