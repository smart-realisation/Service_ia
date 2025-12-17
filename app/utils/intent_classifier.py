"""Regex-based intent classifier fallback"""
import re
from typing import Optional, Dict, Any, List, Tuple
from ..schemas.chatbot import Intent


class IntentClassifier:
    """Fallback intent classifier using regex patterns"""
    
    PATTERNS: List[Tuple[str, str, List[str]]] = [
        # (intent_name, pattern, entity_keys)
        ("get_connected_devices", r"(appareils?|devices?|objets?)\s*(connectés?|en ligne)", []),
        ("get_security_alerts", r"(alertes?|alarmes?)\s*(sécurité|critiques?)?", ["severity"]),
        ("get_anomalies", r"(anomalies?|comportements?\s*suspects?|activités?\s*suspectes?)", []),
        ("get_sensor_data", r"(capteurs?|température|humidité|gaz|mouvement)", ["sensor_type"]),
        ("get_node_status", r"(nœuds?|nodes?|esp32)\s*(statut|état)?", ["node_id"]),
        ("get_system_health", r"(état|santé|status)\s*(système|safelink)?", []),
        ("get_security_report", r"(rapport|résumé)\s*(sécurité)?", ["period"]),
        ("get_compliance_status", r"(conformité|rgpd|compliance)", []),
        ("get_security_tips", r"(conseils?|tips?|recommandations?)\s*(sécurité)?", ["topic"]),
        ("navigate_to", r"(aller|naviguer|voir|afficher)\s*(dashboard|alertes|devices)", ["page"]),
        ("get_new_devices", r"(nouveaux?)\s*(appareils?|devices?)", ["since"]),
        ("get_network_traffic", r"(trafic|traffic)\s*(réseau|network)?", ["period"]),
    ]
    
    ENTITY_PATTERNS = {
        "severity": {
            "critical": r"critiques?|urgentes?|graves?",
            "warning": r"warnings?|attention|moyennes?",
            "info": r"info|informations?"
        },
        "sensor_type": {
            "temperature": r"température|temp",
            "humidity": r"humidité",
            "gas": r"gaz|fumée|co",
            "motion": r"mouvement|présence",
            "light": r"lumière|luminosité"
        },
        "period": {
            "1h": r"1\s*h|une?\s*heure",
            "24h": r"24\s*h|aujourd'?hui|journée",
            "7d": r"7\s*j|semaine|7\s*jours",
            "30d": r"30\s*j|mois"
        },
        "page": {
            "dashboard": r"dashboard|tableau\s*de\s*bord|accueil",
            "devices": r"devices?|appareils?",
            "alerts": r"alertes?",
            "sensors": r"capteurs?",
            "settings": r"paramètres?|config"
        }
    }

    @classmethod
    def classify(cls, text: str) -> Optional[Intent]:
        """Classify user intent from text"""
        text_lower = text.lower().strip()
        
        for intent_name, pattern, entity_keys in cls.PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                entities = {}
                
                # Extract entities
                for key in entity_keys:
                    if key in cls.ENTITY_PATTERNS:
                        for value, entity_pattern in cls.ENTITY_PATTERNS[key].items():
                            if re.search(entity_pattern, text_lower, re.IGNORECASE):
                                entities[key] = value
                                break
                
                return Intent(
                    name=intent_name,
                    confidence=0.7,  # Regex-based = lower confidence
                    entities=entities
                )
        
        return None
    
    @classmethod
    def extract_device_id(cls, text: str) -> Optional[str]:
        """Extract device ID or MAC address from text"""
        # MAC address pattern
        mac_pattern = r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})"
        mac_match = re.search(mac_pattern, text)
        if mac_match:
            return mac_match.group(0)
        
        # Device ID pattern (e.g., DEV-001, device_123)
        id_pattern = r"(DEV[-_]?\d+|device[-_]?\d+)"
        id_match = re.search(id_pattern, text, re.IGNORECASE)
        if id_match:
            return id_match.group(0)
        
        return None
    
    @classmethod
    def extract_alert_id(cls, text: str) -> Optional[str]:
        """Extract alert ID from text"""
        pattern = r"(ALR[-_]?\d+|alert[-_]?\d+|#\d+)"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(0) if match else None
    
    @classmethod
    def is_greeting(cls, text: str) -> bool:
        """Check if text is a greeting"""
        greetings = r"^(bonjour|salut|hello|hi|hey|coucou|bonsoir)"
        return bool(re.match(greetings, text.lower().strip()))
    
    @classmethod
    def is_help_request(cls, text: str) -> bool:
        """Check if user is asking for help"""
        help_patterns = r"(aide|help|comment|qu'?est-?ce que|c'?est quoi|explique)"
        return bool(re.search(help_patterns, text.lower()))
