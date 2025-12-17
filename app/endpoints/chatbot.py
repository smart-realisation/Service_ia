"""Chatbot API endpoints"""
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..core.config import settings
from ..core.database import DatabaseManager
from ..core.mqtt_client import mqtt_client
from ..schemas.chatbot import (
    ChatbotQueryRequest, ChatbotResponse, HealthResponse
)
from ..services.chatbot_function_calling import ChatbotService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["chatbot"])

limiter = Limiter(key_func=get_remote_address)
chatbot_service: Optional[ChatbotService] = None


async def get_chatbot_service() -> ChatbotService:
    global chatbot_service
    if chatbot_service is None:
        chatbot_service = ChatbotService()
        await chatbot_service.init_redis()
    return chatbot_service


@router.post("/query", response_model=ChatbotResponse)
@limiter.limit(f"{settings.rate_limit_requests}/minute")
async def query_chatbot(
    request: Request,
    query: ChatbotQueryRequest,
    service: ChatbotService = Depends(get_chatbot_service)
) -> ChatbotResponse:
    """
    Process a chatbot query with function calling.
    
    - **message**: User's question or command
    - **user_id**: Unique user identifier
    - **user_role**: User role (IT_MANAGER, HOME_USER, FACILITY_MANAGER, ADMIN)
    - **conversation_id**: Optional conversation ID for context
    """
    try:
        return await service.process_query(query)
    except Exception as e:
        logger.error(f"Query processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Check system health status.
    
    Returns status of all connected services:
    - Database (PostgreSQL)
    - Redis (sessions/cache)
    - MQTT broker
    - LLM service
    """
    db_connected = False
    redis_connected = False
    
    # Check database
    try:
        pool = DatabaseManager.get_pool()
        if pool:
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                db_connected = True
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
    
    # Check Redis
    try:
        service = await get_chatbot_service()
        if service.redis_client:
            await service.redis_client.ping()
            redis_connected = True
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
    
    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        version="1.0.0",
        llm_enabled=settings.llm_enabled and bool(settings.groq_api_key),
        database_connected=db_connected,
        redis_connected=redis_connected,
        mqtt_connected=mqtt_client.is_connected
    )


@router.get("/suggestions")
async def get_suggestions(user_role: str = "HOME_USER") -> Dict[str, Any]:
    """Get suggested queries based on user role"""
    suggestions = {
        "IT_MANAGER": [
            "Montre-moi les alertes critiques",
            "Quel est l'état de conformité RGPD?",
            "Analyse le trafic réseau des dernières 24h",
            "Génère un rapport de sécurité hebdomadaire"
        ],
        "HOME_USER": [
            "Quels appareils sont connectés?",
            "Y a-t-il des activités suspectes?",
            "Montre les données de température",
            "Donne-moi des conseils de sécurité"
        ],
        "FACILITY_MANAGER": [
            "Y a-t-il des alertes importantes?",
            "Les caméras fonctionnent-elles?",
            "Quel est l'état du système?",
            "Montre les alertes environnementales"
        ],
        "ADMIN": [
            "État de santé du système",
            "Tous les appareils suspects",
            "Rapport de conformité complet",
            "Nouveaux appareils détectés"
        ]
    }
    
    return {
        "role": user_role,
        "suggestions": suggestions.get(user_role, suggestions["HOME_USER"])
    }


