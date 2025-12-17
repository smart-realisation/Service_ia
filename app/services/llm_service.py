"""Groq API integration for LLM using official SDK"""
import json
import logging
import re
from typing import Optional, Dict, Any, List

from groq import AsyncGroq
import httpx

from ..core.config import settings
from ..schemas.chatbot import UserRole
from .prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)

FUNCTIONS_PROMPT = """
🔧 FONCTIONS DISPONIBLES:
Pour exécuter une fonction, réponds UNIQUEMENT avec le format JSON suivant (sans autre texte):
{"function": "nom_fonction", "arguments": {...}}

📊 FONCTIONS MESURES (CAPTEURS):
1. get_mesures(type_code="TEMPERATURE"|"HUMIDITE"|"GAZ"|null, period="24h", limit=100) - Récupère les mesures
2. get_latest_mesures() - Dernière mesure de chaque type
3. get_mesures_stats(period="24h") - Statistiques (min, max, moyenne) par type
4. check_mesures_alerts() - Vérifie les alertes sur les mesures actuelles
5. get_temperature(period="24h", limit=50) - Mesures de température (°C)
6. get_humidity(period="24h", limit=50) - Mesures d'humidité (%)
7. get_gas_level(period="24h", limit=50) - Mesures de gaz (PPM)

🔌 FONCTIONS APPAREILS:
8. get_connected_devices(status="all"|"online"|"offline"|"suspicious", zone=null) - Liste les appareils
9. get_device_details(device_id) - Détails d'un appareil
10. get_network_traffic(device_id=null, period="24h") - Trafic réseau
11. get_new_devices(since="24h") - Nouveaux appareils

🚨 FONCTIONS ALERTES:
12. get_security_alerts(severity="all"|"critical"|"warning"|"info", status="active", limit=20) - Alertes sécurité
13. get_anomalies(type="all"|"network"|"physical"|"environmental", period="24h") - Anomalies
14. explain_alert(alert_id) - Explication d'une alerte
15. get_environmental_alerts(severity="all") - Alertes environnementales

📈 FONCTIONS SYSTÈME:
16. get_sensor_data(sensor_type="all"|"temperature"|"humidity"|"gas", node_id=null, period="24h") - Données capteurs
17. get_node_status(node_id=null) - Statut des nœuds ESP32
18. get_system_health() - État de santé du système
19. get_security_report(period="24h", format="summary") - Rapport de sécurité
20. get_compliance_status() - Conformité RGPD
21. get_security_tips(topic="general"|"iot"|"network"|"physical"|"passwords") - Conseils sécurité
22. navigate_to(page) - Navigation (dashboard, devices, alerts, sensors, nodes, settings, reports)

⚠️ RÈGLES IMPORTANTES:
- N'appelle une fonction QUE si l'utilisateur demande des DONNÉES SPÉCIFIQUES du système
- Pour ces questions, réponds DIRECTEMENT en texte SANS appeler de fonction:
  * Questions sur tes capacités: "Que sais-tu faire?", "Qu'est-ce que tu peux faire?", "Aide-moi"
  * Salutations: "Bonjour", "Salut", "Merci", "Au revoir"
  * Questions générales sur SafeLink ou la sécurité IoT
  * Demandes d'explications ou de conseils généraux
- Appelle une fonction SEULEMENT pour:
  * "Quelle est la température?" → get_temperature ou get_latest_mesures
  * "Montre les mesures" → get_mesures
  * "Y a-t-il des alertes?" → check_mesures_alerts ou get_security_alerts
  * "Statistiques des capteurs" → get_mesures_stats
  * etc.
- Réponds toujours en français
"""


class LLMService:
    def __init__(self):
        self.api_key = settings.groq_api_key
        self.model = settings.llm_model
        self.enabled = settings.llm_enabled and bool(self.api_key)

        # Configure httpx client with longer timeouts
        if self.enabled:
            http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=30.0,  # 30 seconds for connection
                    read=120.0,     # 2 minutes for reading response
                    write=30.0,     # 30 seconds for writing
                    pool=10.0       # 10 seconds for pool
                )
            )
            self.client = AsyncGroq(api_key=self.api_key, http_client=http_client)
        else:
            self.client = None

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        user_role: UserRole,
        use_tools: bool = True
    ) -> Dict[str, Any]:
        """Call Groq API for chat completion"""
        if not self.enabled or not self.client:
            return {"error": "LLM service disabled", "message": "Service LLM non disponible"}
        
        system_prompt = PromptBuilder.build_system_prompt(user_role)
        if use_tools:
            system_prompt += "\n\n" + FUNCTIONS_PROMPT
        
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        
        try:
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature
            )
            
            content = completion.choices[0].message.content or ""
            return {"choices": [{"message": {"content": content, "tool_calls": None}}]}
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return {"error": str(e)}
    
    def parse_function_call(self, response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract function call from LLM response"""
        try:
            choices = response.get("choices", [])
            if not choices:
                return None
            
            content = choices[0].get("message", {}).get("content", "")
            if not content:
                return None
            
            # Try to parse JSON function call
            # Pattern 1: {"function": "name", "arguments": {...}}
            json_match = re.search(r'\{[^{}]*"function"[^{}]*\}', content, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    if "function" in data:
                        return {
                            "name": data["function"],
                            "arguments": data.get("arguments", {})
                        }
                except json.JSONDecodeError:
                    pass
            
            # Pattern 2: Full JSON with nested arguments
            try:
                # Find JSON that spans multiple lines
                json_pattern = r'\{\s*"function"\s*:\s*"(\w+)"\s*,\s*"arguments"\s*:\s*(\{[^}]*\})\s*\}'
                match = re.search(json_pattern, content, re.DOTALL)
                if match:
                    return {
                        "name": match.group(1),
                        "arguments": json.loads(match.group(2))
                    }
            except (json.JSONDecodeError, AttributeError):
                pass
            
            return None
        except Exception as e:
            logger.error(f"Error parsing function call: {e}")
            return None
    
    def get_message_content(self, response: Dict[str, Any]) -> str:
        """Extract message content from LLM response"""
        try:
            choices = response.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content") or ""
                # Remove JSON function calls from displayed content
                content = re.sub(r'\{[^{}]*"function"[^{}]*\}', '', content).strip()
                return content
            return ""
        except (KeyError, IndexError):
            return ""
