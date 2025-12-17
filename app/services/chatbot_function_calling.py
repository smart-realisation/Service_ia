"""Main chatbot service with function calling"""
import json
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

import redis.asyncio as redis

from ..core.config import settings
from ..schemas.chatbot import (
    ChatbotQueryRequest, ChatbotResponse, UserRole,
    Intent, NavigationInfo, AlertSeverity
)
from .llm_service import LLMService
from .device_service import DeviceService
from .alert_service import AlertService
from .sensor_service import SensorService
from .prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class ChatbotService:
    def __init__(self):
        self.llm = LLMService()
        self.device_service = DeviceService()
        self.alert_service = AlertService()
        self.sensor_service = SensorService()
        self.redis_client: Optional[redis.Redis] = None
    
    async def init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(settings.redis_url)
            await self.redis_client.ping()
            logger.info("Redis connected")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.redis_client = None

    async def get_conversation_history(
        self, conversation_id: str
    ) -> List[Dict[str, str]]:
        """Get conversation history from Redis"""
        if not self.redis_client:
            return []
        
        try:
            history = await self.redis_client.get(f"conv:{conversation_id}")
            if history:
                return json.loads(history)
            return []
        except Exception as e:
            logger.error(f"Error getting conversation: {e}")
            return []
    
    async def save_conversation(
        self, conversation_id: str, messages: List[Dict[str, str]]
    ):
        """Save conversation history to Redis"""
        if not self.redis_client:
            return
        
        try:
            # Keep last 20 messages
            messages = messages[-20:]
            await self.redis_client.setex(
                f"conv:{conversation_id}",
                settings.conversation_ttl,
                json.dumps(messages)
            )
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
    
    async def execute_function(
        self, function_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a function and return results"""
        handlers = {
            "get_connected_devices": lambda: DeviceService.get_connected_devices(
                arguments.get("status", "all"),
                arguments.get("zone")
            ),
            "get_device_details": lambda: DeviceService.get_device_details(
                arguments["device_id"]
            ),
            "get_network_traffic": lambda: DeviceService.get_network_traffic(
                arguments.get("device_id"),
                arguments.get("period", "24h")
            ),
            "get_new_devices": lambda: DeviceService.get_new_devices(
                arguments.get("since", "24h")
            ),
            "get_security_alerts": lambda: AlertService.get_security_alerts(
                arguments.get("severity", "all"),
                arguments.get("status", "active"),
                arguments.get("limit", 20)
            ),
            "get_anomalies": lambda: AlertService.get_anomalies(
                arguments.get("type", "all"),
                arguments.get("period", "24h")
            ),
            "explain_alert": lambda: AlertService.explain_alert(
                arguments["alert_id"]
            ),
            "get_environmental_alerts": lambda: AlertService.get_environmental_alerts(
                arguments.get("severity", "all")
            ),
            "get_sensor_data": lambda: self.sensor_service.get_sensor_data(
                arguments.get("sensor_type", "all"),
                arguments.get("node_id"),
                arguments.get("period", "24h")
            ),
            "get_node_status": lambda: self.sensor_service.get_node_status(
                arguments.get("node_id")
            ),
            "get_system_health": lambda: SensorService.get_system_health(),
            "get_security_report": lambda: SensorService.get_security_report(
                arguments.get("period", "24h"),
                arguments.get("format", "summary")
            ),
            "get_compliance_status": lambda: SensorService.get_compliance_status(),
            "get_security_tips": lambda: self._get_security_tips(
                arguments.get("topic", "general")
            ),
            "navigate_to": lambda: self._navigate_to(arguments["page"]),
            "request_clarification": lambda: self._request_clarification(
                arguments["ambiguity_reason"],
                arguments["options"]
            )
        }
        
        handler = handlers.get(function_name)
        if handler:
            return await handler()
        return {"error": f"Unknown function: {function_name}"}

    async def _get_security_tips(self, topic: str) -> Dict[str, Any]:
        """Get security tips by topic"""
        tips = {
            "general": [
                "🔐 Changez les mots de passe par défaut de tous vos appareils IoT",
                "📡 Segmentez votre réseau: créez un VLAN dédié aux objets connectés",
                "🔄 Mettez à jour régulièrement le firmware de vos appareils"
            ],
            "iot": [
                "🏠 Désactivez les fonctionnalités non utilisées sur vos devices",
                "🔒 Utilisez WPA3 pour votre réseau WiFi IoT",
                "📊 Surveillez le trafic sortant de vos appareils"
            ],
            "network": [
                "🛡️ Activez le pare-feu sur votre routeur",
                "🔍 Auditez régulièrement les appareils connectés",
                "⚡ Bloquez les connexions sortantes non nécessaires"
            ],
            "physical": [
                "📹 Positionnez les caméras pour couvrir les points d'entrée",
                "🚨 Testez régulièrement vos détecteurs de mouvement",
                "🔋 Vérifiez les batteries des capteurs sans fil"
            ],
            "passwords": [
                "🔑 Utilisez des mots de passe uniques pour chaque appareil",
                "📝 Stockez vos mots de passe dans un gestionnaire sécurisé",
                "🔄 Changez les mots de passe tous les 6 mois"
            ]
        }
        return {"success": True, "tips": tips.get(topic, tips["general"]), "topic": topic}
    
    async def _navigate_to(self, page: str) -> Dict[str, Any]:
        """Generate navigation info"""
        pages = {
            "dashboard": {"path": "/dashboard", "description": "Tableau de bord principal"},
            "devices": {"path": "/devices", "description": "Liste des appareils connectés"},
            "alerts": {"path": "/alerts", "description": "Centre d'alertes de sécurité"},
            "sensors": {"path": "/sensors", "description": "Données des capteurs"},
            "nodes": {"path": "/nodes", "description": "Gestion des nœuds ESP32"},
            "settings": {"path": "/settings", "description": "Paramètres du système"},
            "reports": {"path": "/reports", "description": "Rapports de sécurité"}
        }
        return {"success": True, "navigation": pages.get(page, pages["dashboard"])}
    
    async def _request_clarification(
        self, reason: str, options: List[str]
    ) -> Dict[str, Any]:
        """Request clarification from user"""
        return {
            "success": True,
            "clarification_needed": True,
            "reason": reason,
            "options": options
        }
    
    def _is_simple_message(self, message: str) -> bool:
        """Check if message is a simple greeting or doesn't need tools"""
        import re
        simple_patterns = [
            r"^(bonjour|salut|hello|hi|hey|coucou|bonsoir|bonne nuit)[\s!?.]*$",
            r"^(merci|thanks|ok|d'accord|super|parfait)[\s!?.]*$",
            r"^(oui|non|yes|no)[\s!?.]*$",
            r"^(au revoir|bye|à bientôt|ciao)[\s!?.]*$"
        ]
        msg_lower = message.lower().strip()
        return any(re.match(p, msg_lower, re.IGNORECASE) for p in simple_patterns)
    
    async def process_query(
        self, request: ChatbotQueryRequest
    ) -> ChatbotResponse:
        """Process a chatbot query with function calling"""
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Get conversation history
        history = await self.get_conversation_history(conversation_id)
        
        # Add user message
        history.append({"role": "user", "content": request.message})
        
        # Check if simple message (no tools needed)
        use_tools = not self._is_simple_message(request.message)
        
        # Call LLM
        llm_response = await self.llm.chat_completion(history, request.user_role, use_tools)
        
        if "error" in llm_response:
            return ChatbotResponse(
                message=f"⚠️ Erreur: {llm_response.get('error', 'Service indisponible')}",
                requires_human=True
            )
        
        # Check for function call
        function_call = self.llm.parse_function_call(llm_response)
        
        if function_call:
            # Execute function
            func_result = await self.execute_function(
                function_call["name"],
                function_call["arguments"]
            )
            
            # Add function result to history and get final response
            history.append({
                "role": "assistant",
                "content": f"[Function: {function_call['name']}]"
            })
            history.append({
                "role": "user", 
                "content": f"Résultat de {function_call['name']}: {json.dumps(func_result, default=str)}"
            })
            
            final_response = await self.llm.chat_completion(history, request.user_role, use_tools=False)
            message = self.llm.get_message_content(final_response)
            
            # Build response
            response = ChatbotResponse(
                message=message or "Voici les informations demandées.",
                function_called=function_call["name"],
                data=func_result
            )
            
            # Handle navigation
            if function_call["name"] == "navigate_to":
                nav = func_result.get("navigation", {})
                response.navigation = NavigationInfo(
                    path=nav.get("path", "/"),
                    description=nav.get("description", "")
                )
            
            # Handle clarification
            if func_result.get("clarification_needed"):
                response.suggestions = func_result.get("options", [])
        else:
            message = self.llm.get_message_content(llm_response)
            response = ChatbotResponse(message=message or "Comment puis-je vous aider?")
        
        # Save conversation
        history.append({"role": "assistant", "content": response.message})
        await self.save_conversation(conversation_id, history)
        
        return response
