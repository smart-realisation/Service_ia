"""Device Classifier Model using XGBoost"""
import logging
import pickle
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

import numpy as np

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent / "trained"
MODEL_PATH.mkdir(exist_ok=True)

# Known device patterns (OUI database simplified)
OUI_DATABASE = {
    "00:1A:2B": {"vendor": "Cisco", "type": "ROUTER"},
    "00:50:56": {"vendor": "VMware", "type": "VIRTUAL_MACHINE"},
    "B8:27:EB": {"vendor": "Raspberry Pi", "type": "IOT_DEVICE"},
    "DC:A6:32": {"vendor": "Raspberry Pi", "type": "IOT_DEVICE"},
    "18:FE:34": {"vendor": "Espressif", "type": "IOT_DEVICE"},
    "24:0A:C4": {"vendor": "Espressif", "type": "IOT_DEVICE"},
    "5C:CF:7F": {"vendor": "Espressif", "type": "IOT_DEVICE"},
    "AC:67:B2": {"vendor": "Espressif", "type": "IOT_DEVICE"},
    "00:0C:29": {"vendor": "VMware", "type": "VIRTUAL_MACHINE"},
    "00:1C:42": {"vendor": "Parallels", "type": "VIRTUAL_MACHINE"},
    "00:03:FF": {"vendor": "Microsoft", "type": "COMPUTER"},
    "00:15:5D": {"vendor": "Microsoft Hyper-V", "type": "VIRTUAL_MACHINE"},
    "F4:F5:D8": {"vendor": "Google", "type": "SMART_SPEAKER"},
    "44:07:0B": {"vendor": "Google", "type": "SMART_DEVICE"},
    "68:A4:0E": {"vendor": "Amazon", "type": "SMART_SPEAKER"},
    "FC:65:DE": {"vendor": "Amazon", "type": "SMART_DEVICE"},
    "00:17:88": {"vendor": "Philips Hue", "type": "SMART_LIGHT"},
    "00:1E:C0": {"vendor": "Microchip", "type": "IOT_DEVICE"},
    "B0:BE:76": {"vendor": "TP-Link", "type": "SMART_PLUG"},
    "50:C7:BF": {"vendor": "TP-Link", "type": "ROUTER"},
    "14:CC:20": {"vendor": "TP-Link", "type": "SMART_DEVICE"},
    "78:8A:20": {"vendor": "Ubiquiti", "type": "NETWORK_DEVICE"},
    "00:27:22": {"vendor": "Ubiquiti", "type": "NETWORK_DEVICE"},
}

# Device type risk levels
DEVICE_RISK_LEVELS = {
    "ROUTER": "LOW",
    "COMPUTER": "LOW",
    "SMARTPHONE": "LOW",
    "TABLET": "LOW",
    "SMART_TV": "MEDIUM",
    "SMART_SPEAKER": "MEDIUM",
    "SMART_LIGHT": "LOW",
    "SMART_PLUG": "MEDIUM",
    "SMART_DEVICE": "MEDIUM",
    "IOT_DEVICE": "HIGH",
    "CAMERA": "HIGH",
    "THERMOSTAT": "MEDIUM",
    "NETWORK_DEVICE": "LOW",
    "VIRTUAL_MACHINE": "MEDIUM",
    "UNKNOWN": "HIGH",
}


class DeviceClassifier:
    """
    Classifieur d'appareils IoT pour SafeLink.
    Utilise patterns MAC, comportement réseau et ML pour classifier.
    """
    
    def __init__(self):
        self.model = None
        self.label_encoder = None
        self._load_or_create_model()
    
    def _load_or_create_model(self):
        """Load existing model or prepare for rule-based classification"""
        model_file = MODEL_PATH / "device_classifier.pkl"
        
        if model_file.exists():
            try:
                with open(model_file, "rb") as f:
                    saved = pickle.load(f)
                    self.model = saved.get("model")
                    self.label_encoder = saved.get("label_encoder")
                logger.info("Loaded existing device classifier model")
                return
            except Exception as e:
                logger.warning(f"Failed to load classifier: {e}")
        
        logger.info("Using rule-based device classification")
    
    def _get_oui_prefix(self, mac_address: str) -> str:
        """Extract OUI prefix from MAC address"""
        mac = mac_address.upper().replace("-", ":").replace(".", ":")
        parts = mac.split(":")
        if len(parts) >= 3:
            return ":".join(parts[:3])
        return ""
    
    def _extract_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract classification features from device data"""
        features = {
            "has_hostname": bool(data.get("hostname")),
            "hostname_pattern": self._analyze_hostname(data.get("hostname", "")),
            "avg_bytes_in": data.get("avg_bytes_in", 0),
            "avg_bytes_out": data.get("avg_bytes_out", 0),
            "connection_frequency": data.get("connection_frequency", 0),
            "unique_ports": len(data.get("ports_used", [])),
            "uses_https": 443 in data.get("ports_used", []),
            "uses_mqtt": 1883 in data.get("ports_used", []) or 8883 in data.get("ports_used", []),
            "uses_coap": 5683 in data.get("ports_used", []),
            "active_hours": data.get("active_hours", 24),
        }
        return features
    
    def _analyze_hostname(self, hostname: str) -> str:
        """Analyze hostname pattern"""
        hostname = hostname.lower()
        
        patterns = {
            "android": "SMARTPHONE",
            "iphone": "SMARTPHONE",
            "ipad": "TABLET",
            "macbook": "COMPUTER",
            "windows": "COMPUTER",
            "desktop": "COMPUTER",
            "laptop": "COMPUTER",
            "tv": "SMART_TV",
            "roku": "SMART_TV",
            "chromecast": "SMART_TV",
            "echo": "SMART_SPEAKER",
            "alexa": "SMART_SPEAKER",
            "google-home": "SMART_SPEAKER",
            "nest": "THERMOSTAT",
            "hue": "SMART_LIGHT",
            "camera": "CAMERA",
            "cam": "CAMERA",
            "esp": "IOT_DEVICE",
            "arduino": "IOT_DEVICE",
            "raspberry": "IOT_DEVICE",
            "sensor": "IOT_DEVICE",
        }
        
        for pattern, device_type in patterns.items():
            if pattern in hostname:
                return device_type
        
        return "UNKNOWN"
    
    def classify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a device based on MAC, IP, and behavior patterns.
        
        Input:
            - mac_address: str
            - ip_address: str (optional)
            - hostname: str (optional)
            - avg_bytes_in: int (optional)
            - avg_bytes_out: int (optional)
            - ports_used: List[int] (optional)
            - connection_frequency: int (optional)
        
        Returns:
            - device_type: str
            - vendor: str
            - risk_level: str (LOW, MEDIUM, HIGH)
            - confidence: float
            - recommendations: List[str]
        """
        mac = data.get("mac_address", "")
        oui = self._get_oui_prefix(mac)
        
        # Check OUI database first
        oui_info = OUI_DATABASE.get(oui, {})
        vendor = oui_info.get("vendor", "Unknown")
        device_type = oui_info.get("type")
        confidence = 0.9 if device_type else 0.0
        
        # Hostname analysis
        if not device_type:
            hostname = data.get("hostname", "")
            device_type = self._analyze_hostname(hostname)
            if device_type != "UNKNOWN":
                confidence = 0.7
        
        # Behavioral analysis
        if device_type == "UNKNOWN" or confidence < 0.7:
            features = self._extract_features(data)
            behavioral_type = self._behavioral_classification(features)
            if behavioral_type != "UNKNOWN":
                device_type = behavioral_type
                confidence = max(confidence, 0.5)
        
        if not device_type:
            device_type = "UNKNOWN"
            confidence = 0.3
        
        risk_level = DEVICE_RISK_LEVELS.get(device_type, "HIGH")
        recommendations = self._get_recommendations(device_type, risk_level, data)
        
        return {
            "device_type": device_type,
            "vendor": vendor,
            "risk_level": risk_level,
            "confidence": confidence,
            "mac_address": mac,
            "ip_address": data.get("ip_address"),
            "hostname": data.get("hostname"),
            "recommendations": recommendations,
            "classified_at": datetime.now().isoformat()
        }
    
    def _behavioral_classification(self, features: Dict[str, Any]) -> str:
        """Classify based on behavioral patterns"""
        # MQTT usage suggests IoT
        if features.get("uses_mqtt"):
            return "IOT_DEVICE"
        
        # CoAP usage suggests IoT
        if features.get("uses_coap"):
            return "IOT_DEVICE"
        
        # High bandwidth, many ports = computer
        if features.get("avg_bytes_in", 0) > 1_000_000 and features.get("unique_ports", 0) > 10:
            return "COMPUTER"
        
        # Low bandwidth, few ports, always on = IoT
        if features.get("avg_bytes_in", 0) < 10_000 and features.get("active_hours", 0) == 24:
            return "IOT_DEVICE"
        
        return "UNKNOWN"
    
    def _get_recommendations(
        self, device_type: str, risk_level: str, data: Dict[str, Any]
    ) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        if risk_level == "HIGH":
            recommendations.append("Isoler cet appareil sur un VLAN dédié IoT")
            recommendations.append("Surveiller le trafic réseau de cet appareil")
        
        if device_type == "UNKNOWN":
            recommendations.append("Identifier manuellement cet appareil")
            recommendations.append("Vérifier si cet appareil est autorisé sur le réseau")
        
        if device_type == "CAMERA":
            recommendations.append("Vérifier que le firmware est à jour")
            recommendations.append("Désactiver l'accès cloud si non nécessaire")
            recommendations.append("Changer les identifiants par défaut")
        
        if device_type == "IOT_DEVICE":
            recommendations.append("Mettre à jour le firmware régulièrement")
            recommendations.append("Limiter les connexions sortantes")
        
        if not recommendations:
            recommendations.append("Aucune action requise")
        
        return recommendations
    
    def batch_classify(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify multiple devices"""
        return [self.classify(d) for d in devices]
    
    def train(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Train classifier on labeled data (future enhancement)"""
        # Placeholder for XGBoost training
        logger.info(f"Training data received: {len(training_data)} samples")
        return {
            "success": True,
            "message": "Rule-based classification active. ML training coming soon.",
            "samples": len(training_data)
        }


# Singleton instance
device_classifier = DeviceClassifier()
