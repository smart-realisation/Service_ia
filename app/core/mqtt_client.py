"""MQTT client for IoT device communication"""
import json
import logging
from typing import Callable, Dict, Any, Optional
import paho.mqtt.client as mqtt

from .config import settings

logger = logging.getLogger(__name__)


class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="safelink-ai")
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        self._handlers: Dict[str, Callable] = {}
        self._connected = False
    
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self._connected = True
            logger.info("Connected to MQTT broker")
            # Subscribe to SafeLink topics
            topics = [
                "safelink/devices/#",
                "safelink/alerts/#",
                "safelink/sensors/#",
                "safelink/nodes/#"
            ]
            for topic in topics:
                client.subscribe(topic)
                logger.info(f"Subscribed to {topic}")
        else:
            logger.error(f"MQTT connection failed with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc, properties=None):
        self._connected = False
        logger.warning(f"Disconnected from MQTT broker (rc={rc})")
    
    def _on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            logger.debug(f"MQTT message on {topic}: {payload}")
            
            # Route to appropriate handler
            for pattern, handler in self._handlers.items():
                if topic.startswith(pattern.replace("#", "")):
                    handler(topic, payload)
                    break
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON on topic {msg.topic}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def register_handler(self, topic_pattern: str, handler: Callable):
        """Register a handler for a topic pattern"""
        self._handlers[topic_pattern] = handler
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            if settings.mqtt_user and settings.mqtt_password:
                self.client.username_pw_set(settings.mqtt_user, settings.mqtt_password)
            
            self.client.connect(settings.mqtt_broker, settings.mqtt_port, keepalive=60)
            self.client.loop_start()
            logger.info(f"Connecting to MQTT broker at {settings.mqtt_broker}:{settings.mqtt_port}")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Disconnected from MQTT broker")
    
    def publish(self, topic: str, payload: Dict[str, Any]):
        """Publish message to topic"""
        if self._connected:
            self.client.publish(topic, json.dumps(payload))
        else:
            logger.warning("Cannot publish: not connected to MQTT broker")
    
    @property
    def is_connected(self) -> bool:
        return self._connected


mqtt_client = MQTTClient()
