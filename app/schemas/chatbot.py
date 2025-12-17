"""Request/Response models for chatbot"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    IT_MANAGER = "IT_MANAGER"
    HOME_USER = "HOME_USER"
    FACILITY_MANAGER = "FACILITY_MANAGER"


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ChatbotQueryRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    user_id: str
    user_role: Optional[UserRole] = UserRole.HOME_USER
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Intent(BaseModel):
    name: str
    confidence: float = Field(ge=0.0, le=1.0)
    entities: Dict[str, Any] = Field(default_factory=dict)


class NavigationInfo(BaseModel):
    path: str
    description: str
    params: Optional[Dict[str, Any]] = None


class FunctionCall(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ChatbotResponse(BaseModel):
    message: str
    intent: Optional[Intent] = None
    suggestions: List[str] = Field(default_factory=list)
    data: Optional[Dict[str, Any]] = None
    navigation: Optional[NavigationInfo] = None
    severity: Optional[AlertSeverity] = None
    requires_human: bool = False
    function_called: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_enabled: bool
    database_connected: bool
    redis_connected: bool
    mqtt_connected: bool


class ConversationMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    function_call: Optional[FunctionCall] = None
