"""API endpoints pour les mesures de capteurs"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Query
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..schemas.mesure import (
    MesureCreate, MesureResponse, MesuresListResponse,
    StatsResponse, TypeMesure
)
from ..services.mesure_service import MesureService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/mesures", tags=["mesures"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/types")
async def get_types_mesure():
    """
    Récupère tous les types de mesure disponibles.
    
    Retourne: TEMPERATURE, HUMIDITE, GAZ avec leurs unités
    """
    result = await MesureService.get_types_mesure()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.post("/", response_model=dict)
@limiter.limit("100/minute")
async def create_mesure(request: Request, mesure: MesureCreate):
    """
    Enregistre une nouvelle mesure de capteur.
    
    - **type_mesure_id**: 1=TEMPERATURE, 2=HUMIDITE, 3=GAZ
    - **valeur**: Valeur numérique de la mesure
    """
    result = await MesureService.create_mesure(mesure.type_mesure_id, mesure.valeur)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.get("/")
async def get_mesures(
    type_code: Optional[str] = Query(None, description="Type: TEMPERATURE, HUMIDITE, GAZ"),
    period: str = Query("24h", description="Période: 1h, 6h, 24h, 7d, 30d"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre max de résultats")
):
    """
    Récupère les mesures avec filtres optionnels.
    
    - **type_code**: Filtrer par type (optionnel)
    - **period**: Période de temps
    - **limit**: Nombre maximum de résultats
    """
    result = await MesureService.get_mesures(type_code, period, limit)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.get("/latest")
async def get_latest_mesures():
    """
    Récupère la dernière mesure de chaque type.
    
    Utile pour afficher l'état actuel des capteurs.
    """
    result = await MesureService.get_latest_mesures()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.get("/stats")
async def get_stats(
    period: str = Query("24h", description="Période: 1h, 6h, 24h, 7d, 30d")
):
    """
    Calcule les statistiques par type de mesure.
    
    Retourne min, max, moyenne, dernière valeur pour chaque type.
    """
    result = await MesureService.get_stats(period)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.get("/alerts")
async def check_alerts():
    """
    Vérifie les seuils d'alerte sur les dernières mesures.
    
    Seuils:
    - Température: warning > 35°C, critical > 45°C
    - Humidité: warning > 80%, critical > 90%
    - Gaz: warning > 100 PPM, critical > 500 PPM
    """
    result = await MesureService.check_alerts()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.get("/thresholds")
async def get_thresholds():
    """Retourne les seuils d'alerte configurés"""
    return {
        "thresholds": {
            "TEMPERATURE": {
                "unite": "CELSIUS",
                "low_critical": 0,
                "low_warning": 5,
                "warning": 35,
                "critical": 45
            },
            "HUMIDITE": {
                "unite": "POURCENT",
                "low_critical": 10,
                "low_warning": 20,
                "warning": 80,
                "critical": 90
            },
            "GAZ": {
                "unite": "PPM",
                "warning": 100,
                "critical": 500
            }
        }
    }
