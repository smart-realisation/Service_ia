"""MQTT event webhooks"""
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.mesure_service import MesureService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


class MQTTEvent(BaseModel):
    topic: str
    payload: Dict[str, Any]
    timestamp: str


class MesureEvent(BaseModel):
    """Event pour une nouvelle mesure de capteur"""
    type_code: str = Field(..., description="TEMPERATURE, HUMIDITE ou GAZ")
    valeur: float = Field(..., description="Valeur de la mesure")


class WebhookResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None


# Mapping type_code vers type_mesure_id
TYPE_MESURE_IDS = {
    "TEMPERATURE": 1,
    "HUMIDITE": 2,
    "GAZ": 3
}


@router.post("/mqtt/mesure", response_model=WebhookResponse)
async def handle_mesure_event(event: MesureEvent) -> WebhookResponse:
    """
    Reçoit une nouvelle mesure de capteur via MQTT.
    
    - **type_code**: TEMPERATURE, HUMIDITE ou GAZ
    - **valeur**: Valeur numérique de la mesure
    """
    type_code = event.type_code.upper()
    type_mesure_id = TYPE_MESURE_IDS.get(type_code)
    
    if not type_mesure_id:
        raise HTTPException(
            status_code=400,
            detail=f"Type de mesure invalide: {type_code}. Valeurs acceptées: TEMPERATURE, HUMIDITE, GAZ"
        )
    
    result = await MesureService.create_mesure(type_mesure_id, event.valeur)
    
    if result.get("success"):
        logger.info(f"Mesure enregistrée: {type_code} = {event.valeur}")
        
        # Vérifier les alertes
        alerts = await MesureService.check_alerts()
        if alerts.get("has_critical"):
            logger.critical(f"ALERTE CRITIQUE détectée: {alerts.get('alerts')}")
        elif alerts.get("has_warning"):
            logger.warning(f"Alerte warning détectée: {alerts.get('alerts')}")
        
        return WebhookResponse(
            status="ok",
            message=f"Mesure {type_code} enregistrée",
            data=result.get("mesure")
        )
    else:
        raise HTTPException(status_code=500, detail=result.get("error"))


@router.post("/mqtt/device", response_model=WebhookResponse)
async def handle_device_event(event: MQTTEvent) -> WebhookResponse:
    """Handle device status change events from MQTT"""
    logger.info(f"Device event: {event.topic} - {event.payload}")
    
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
    """Handle sensor data events from MQTT (legacy)"""
    logger.debug(f"Sensor event: {event.topic} - {event.payload}")
    return WebhookResponse(status="ok", message="Sensor event processed")
