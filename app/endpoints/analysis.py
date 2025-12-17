"""Analysis API endpoints - Anomaly Detection"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..models.anomaly_detector import anomaly_detector

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])
limiter = Limiter(key_func=get_remote_address)


class SensorData(BaseModel):
    """Input schema for sensor data analysis"""
    device_id: Optional[str] = None
    sensor_id: Optional[str] = None
    timestamp: Optional[str] = None
    
    # Mesures capteurs (nouveau schéma)
    temperature: Optional[float] = Field(default=25.0, description="Température en Celsius")
    humidity: Optional[float] = Field(default=50.0, description="Humidité en pourcentage")
    gas_level: Optional[float] = Field(default=0.0, description="Niveau de gaz en PPM")
    motion: Optional[bool] = Field(default=False, description="Mouvement détecté")
    light_level: Optional[float] = Field(default=500.0, description="Niveau de lumière en lux")
    
    # Métriques réseau (optionnel)
    bytes_in: Optional[int] = Field(default=0, description="Octets reçus")
    bytes_out: Optional[int] = Field(default=0, description="Octets envoyés")
    connection_count: Optional[int] = Field(default=0, description="Connexions actives")
    unique_destinations: Optional[int] = Field(default=0, description="IPs destination uniques")


class AnomalyResult(BaseModel):
    """Output schema for anomaly detection"""
    is_anomaly: bool
    anomaly_score: float
    alert_type: str
    severity: str
    details: dict
    timestamp: str
    device_id: Optional[str] = None
    sensor_id: Optional[str] = None


class BatchAnalysisRequest(BaseModel):
    """Batch analysis request"""
    data: List[SensorData]


class BatchAnalysisResponse(BaseModel):
    """Batch analysis response"""
    results: List[AnomalyResult]
    total: int
    anomalies_found: int
    critical_count: int
    high_count: int


class TrainingRequest(BaseModel):
    """Training data request"""
    data: List[SensorData]


@router.post("/analyze", response_model=AnomalyResult)
@limiter.limit("100/minute")
async def analyze_data(request: Request, data: SensorData) -> AnomalyResult:
    """
    Analyze sensor/network data for anomalies.
    
    Called by Backend Ktor when new sensor data arrives.
    Returns anomaly score and alert type if detected.
    """
    try:
        result = anomaly_detector.detect(data.model_dump())
        return AnomalyResult(**result)
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/batch", response_model=BatchAnalysisResponse)
@limiter.limit("20/minute")
async def analyze_batch(request: Request, batch: BatchAnalysisRequest) -> BatchAnalysisResponse:
    """
    Analyze multiple sensor readings in batch.
    
    Useful for historical analysis or bulk processing.
    """
    try:
        data_list = [d.model_dump() for d in batch.data]
        results = anomaly_detector.batch_detect(data_list)
        
        anomalies = [r for r in results if r["is_anomaly"]]
        critical = sum(1 for r in results if r["severity"] == "CRITICAL")
        high = sum(1 for r in results if r["severity"] == "HIGH")
        
        return BatchAnalysisResponse(
            results=[AnomalyResult(**r) for r in results],
            total=len(results),
            anomalies_found=len(anomalies),
            critical_count=critical,
            high_count=high
        )
    except Exception as e:
        logger.error(f"Batch analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train")
@limiter.limit("5/hour")
async def train_model(request: Request, training: TrainingRequest):
    """
    Train the anomaly detection model on historical data.
    
    Requires at least 10 samples of normal behavior.
    """
    try:
        data_list = [d.model_dump() for d in training.data]
        result = anomaly_detector.train(data_list)
        return result
    except Exception as e:
        logger.error(f"Training error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/thresholds")
async def get_thresholds():
    """Get current anomaly detection thresholds"""
    return {
        "TEMPERATURE": {
            "unite": "CELSIUS",
            "warning_min": 5,
            "warning_max": 45,
            "critical_min": 0,
            "critical_max": 60
        },
        "HUMIDITE": {
            "unite": "POURCENT",
            "warning_min": 20,
            "warning_max": 80,
            "critical_min": 10,
            "critical_max": 90
        },
        "GAZ": {
            "unite": "PPM",
            "warning": 100,
            "critical": 500
        },
        "network": {
            "bytes_out": {"warning": 10_000_000, "critical": 50_000_000},
            "connection_count": {"warning": 100, "critical": 500}
        }
    }
