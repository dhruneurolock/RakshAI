"""Core configuration module"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Project
    PROJECT_NAME: str = "RakshAI"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database - SQLite for local, PostgreSQL for production
    DATABASE_URL: str = "postgresql://rakshaiuser:root@localhost:5432/rakshaidb"
    
    # Feature Flags (disable services for local development)
    REDIS_ENABLED: bool = True
    CELERY_ENABLED: bool = True
    OLLAMA_ENABLED: bool = True
    NEO4J_ENABLED: bool = True
    MINIO_ENABLED: bool = True
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:latest"
    
    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "RakshAI123"
    
    # Storage
    STORAGE_TYPE: str = "minio"  # minio or local
    STORAGE_PATH: str = "./storage"  # For local storage
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "rakshaidb"
    MINIO_SECURE: bool = False
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    CORS_ORIGIN_REGEX: str = r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3})(:\d+)?$"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Knowledge Base
    KNOWLEDGE_BASE_PATH: str = "./knowledge-base"
    
    # WebSocket
    WS_MAX_CONNECTIONS: int = 100
    
    # Scan Settings
    MAX_CONCURRENT_SCANS: int = 5
    SCAN_TIMEOUT_SECONDS: int = 3600
    MAX_PAYLOADS_PER_TEST: int = 50
    
    # Safety Settings
    ENABLE_SAFETY_ENFORCER: bool = True
    BLOCK_DESTRUCTIVE_PAYLOADS: bool = True
    
    # Report Settings
    REPORT_STORAGE_PATH: str = "./reports"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


def get_settings() -> Settings:
    return settings
