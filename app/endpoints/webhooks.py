"""MQTT event webhooks"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


class MQTTEvent(BaseModel):
    topic: str
    payload: Dict[str, Any]
    timestamp: str


class WebhookResponse(BaseModel):
    status: str
    message: str


@router.post("/mqtt/device", response_model=WebhookResponse)
async def handle_device_event(event: MQTTEvent) -> WebhookResponse:
    """Handle device status change events from MQTT"""
    logger.info(f"Device event: {event.topic} - {event.payload}")
    
    # Process device event (new device, status change, etc.)
    device_id = event.payload.get("device_id")
    status = event.payload.get("status")
    
    if status == "suspicious":
        logger.warning(f"Suspicious device detected: {device_id}")
    
    return WebhookResponse(status="ok", message="Device event processed")


@router.post("/mqtt/alert", response_model=WebhookResponse)
async def handle_alert_event(event: MQTTEvent) -> WebhookResponse:
    """Handle security alert events from MQTT"""
    logger.info(f"Alert event: {event.topic} - {event.payload}")
    
    severity = event.payload.get("severity", "info")
    if severity == "critical":
        logger.critical(f"Critical alert: {event.payload}")
    
    return WebhookResponse(status="ok", message="Alert event processed")


@router.post("/mqtt/sensor", response_model=WebhookResponse)
async def handle_sensor_event(event: MQTTEvent) -> WebhookResponse:
    """Handle sensor data events from MQTT"""
    logger.debug(f"Sensor event: {event.topic} - {event.payload}")
    return WebhookResponse(status="ok", message="Sensor event processed")
