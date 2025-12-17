"""Configuration settings using Pydantic"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = Field(default="SafeLink AI")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    
    # LLM (Groq)
    groq_api_key: str = Field(default="")
    llm_model: str = Field(default="llama-3.1-70b-versatile")
    llm_enabled: bool = Field(default=True)
    llm_max_tokens: int = Field(default=1024)
    llm_temperature: float = Field(default=0.3)
    
    # Database
    database_url: str = Field(default="postgresql://safelink:password@localhost:5432/safelink")
    
    # InfluxDB
    influxdb_url: str = Field(default="http://localhost:8086")
    influxdb_token: str = Field(default="")
    influxdb_org: str = Field(default="safelink")
    influxdb_bucket: str = Field(default="sensors")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379")
    conversation_ttl: int = Field(default=3600)  # 1 hour
    
    # MQTT
    mqtt_broker: str = Field(default="localhost")
    mqtt_port: int = Field(default=1883)
    mqtt_user: Optional[str] = Field(default=None)
    mqtt_password: Optional[str] = Field(default=None)
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=10)
    rate_limit_window: int = Field(default=60)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
