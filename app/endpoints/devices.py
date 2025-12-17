"""Device Classification API endpoints"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..models.device_classifier import device_classifier

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/devices", tags=["devices"])
limiter = Limiter(key_func=get_remote_address)


class DeviceInput(BaseModel):
    """Input schema for device classification"""
    mac_address: str = Field(..., description="MAC address (e.g., 00:1A:2B:3C:4D:5E)")
    ip_address: Optional[str] = Field(default=None, description="IP address")
    hostname: Optional[str] = Field(default=None, description="Device hostname")
    
    # Behavioral data (optional)
    avg_bytes_in: Optional[int] = Field(default=0, description="Average bytes received")
    avg_bytes_out: Optional[int] = Field(default=0, description="Average bytes sent")
    ports_used: Optional[List[int]] = Field(default=[], description="Ports used by device")
    connection_frequency: Optional[int] = Field(default=0, description="Connections per hour")
    active_hours: Optional[int] = Field(default=24, description="Hours active per day")


class DeviceClassification(BaseModel):
    """Output schema for device classification"""
    device_type: str
    vendor: str
    risk_level: str
    confidence: float
    mac_address: str
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    recommendations: List[str]
    classified_at: str


class BatchClassifyRequest(BaseModel):
    """Batch classification request"""
    devices: List[DeviceInput]


class BatchClassifyResponse(BaseModel):
    """Batch classification response"""
    results: List[DeviceClassification]
    total: int
    high_risk_count: int
    unknown_count: int


@router.post("/classify", response_model=DeviceClassification)
@limiter.limit("100/minute")
async def classify_device(request: Request, device: DeviceInput) -> DeviceClassification:
    """
    Classify a device based on MAC, IP, and behavior patterns.
    
    Called by Backend Ktor when a new device is detected on the network.
    Returns device type, vendor, risk level and security recommendations.
    """
    try:
        result = device_classifier.classify(device.model_dump())
        return DeviceClassification(**result)
    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify/batch", response_model=BatchClassifyResponse)
@limiter.limit("20/minute")
async def classify_batch(request: Request, batch: BatchClassifyRequest) -> BatchClassifyResponse:
    """
    Classify multiple devices in batch.
    
    Useful for network scanning results or periodic device inventory.
    """
    try:
        devices_data = [d.model_dump() for d in batch.devices]
        results = device_classifier.batch_classify(devices_data)
        
        high_risk = sum(1 for r in results if r["risk_level"] == "HIGH")
        unknown = sum(1 for r in results if r["device_type"] == "UNKNOWN")
        
        return BatchClassifyResponse(
            results=[DeviceClassification(**r) for r in results],
            total=len(results),
            high_risk_count=high_risk,
            unknown_count=unknown
        )
    except Exception as e:
        logger.error(f"Batch classification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-levels")
async def get_risk_levels():
    """Get device type risk level mappings"""
    from ..models.device_classifier import DEVICE_RISK_LEVELS
    return {
        "risk_levels": DEVICE_RISK_LEVELS,
        "description": {
            "LOW": "Appareil de confiance, risque minimal",
            "MEDIUM": "Surveillance recommandée",
            "HIGH": "Isolation et surveillance requises"
        }
    }


@router.get("/known-vendors")
async def get_known_vendors():
    """Get list of known device vendors from OUI database"""
    from ..models.device_classifier import OUI_DATABASE
    vendors = {}
    for oui, info in OUI_DATABASE.items():
        vendor = info["vendor"]
        if vendor not in vendors:
            vendors[vendor] = []
        vendors[vendor].append({"oui": oui, "type": info["type"]})
    return {"vendors": vendors, "total_oui": len(OUI_DATABASE)}
