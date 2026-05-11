"""
Local Development Configuration

For running RakshAI locally without Docker
- Uses SQLite (no PostgreSQL needed)
- Uses file-based cache (no Redis needed)
- Uses mock LLM (no Ollama needed)
- Uses local storage (no MinIO needed)
"""

from pydantic_settings import BaseSettings
from typing import List


class LocalSettings(BaseSettings):
    """Local development settings"""
    
    # Project
    PROJECT_NAME: str = "RakshAI"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "local-dev-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database - SQLite (local file)
    DATABASE_URL: str = "sqlite:///./rakshaidb_local.db"
    
    # Redis - Disabled (uses file fallback)
    REDIS_ENABLED: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery - Disabled
    CELERY_ENABLED: bool = False
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Ollama - Mock mode
    OLLAMA_ENABLED: bool = False
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = ""
    
    # Neo4j - Disabled
    NEO4J_ENABLED: bool = False
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    
    # MinIO - Disabled, use local storage
    MINIO_ENABLED: bool = False
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "rakshaidb"
    MINIO_SECRET_KEY: str = "rakshaidb_minio_pass"
    STORAGE_TYPE: str = "local"
    STORAGE_PATH: str = "./storage"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    CORS_ORIGIN_REGEX: str = r"^https?://192\.168\.\d{1,3}\.\d{1,3}(:\d+)?$"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 1000  # Higher for local dev
    
    # Logging
    LOG_LEVEL: str = "DEBUG"
    
    # Knowledge Base
    KNOWLEDGE_BASE_PATH: str = "./knowledge-base"
    
    # WebSocket
    WS_MAX_CONNECTIONS: int = 100
    
    # Scan Settings
    MAX_CONCURRENT_SCANS: int = 5
    SCAN_TIMEOUT_SECONDS: int = 3600
    MAX_PAYLOADS_PER_TEST: int = 50


settings = LocalSettings()
