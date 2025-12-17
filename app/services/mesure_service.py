"""Service pour la gestion des mesures de capteurs"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..core.database import get_db

logger = logging.getLogger(__name__)


class MesureService:
    """Service pour les opérations sur les mesures"""
    
    @staticmethod
    async def get_types_mesure() -> Dict[str, Any]:
        """Récupère tous les types de mesure"""
        try:
            async with get_db() as conn:
                rows = await conn.fetch(
                    "SELECT id, code, unite, description FROM types_mesure ORDER BY id"
                )
                return {
                    "success": True,
                    "types": [dict(row) for row in rows]
                }
        except Exception as e:
            logger.error(f"Erreur récupération types mesure: {e}")
            return {"success": False, "error": str(e), "types": []}
    
    @staticmethod
    async def create_mesure(type_mesure_id: int, valeur: float) -> Dict[str, Any]:
        """Crée une nouvelle mesure"""
        try:
            async with get_db() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO mesures (type_mesure_id, valeur)
                    VALUES ($1, $2)
                    RETURNING id, type_mesure_id, valeur, mesure_at
                    """,
                    type_mesure_id, valeur
                )
                return {
                    "success": True,
                    "mesure": dict(row)
                }
        except Exception as e:
            logger.error(f"Erreur création mesure: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def get_mesures(
        type_code: Optional[str] = None,
        period: str = "24h",
        limit: int = 100
    ) -> Dict[str, Any]:
        """Récupère les mesures avec filtres optionnels"""
        intervals = {"1h": "1 hour", "6h": "6 hours", "24h": "1 day", "7d": "7 days", "30d": "30 days"}
        interval = intervals.get(period, "1 day")
        
        try:
            async with get_db() as conn:
                query = """
                    SELECT m.id, m.valeur, m.mesure_at,
                           t.code as type_code, t.unite, t.description
                    FROM mesures m
                    JOIN types_mesure t ON m.type_mesure_id = t.id
                    WHERE m.mesure_at > NOW() - INTERVAL '""" + interval + "'"
                
                params = []
                if type_code:
                    params.append(type_code)
                    query += f" AND t.code = ${len(params)}"
                
                query += " ORDER BY m.mesure_at DESC"
                params.append(limit)
                query += f" LIMIT ${len(params)}"
                
                rows = await conn.fetch(query, *params)
                mesures = [dict(row) for row in rows]
                
                return {
                    "success": True,
                    "total": len(mesures),
                    "period": period,
                    "mesures": mesures
                }
        except Exception as e:
            logger.error(f"Erreur récupération mesures: {e}")
            return {"success": False, "error": str(e), "mesures": []}
    
    @staticmethod
    async def get_latest_mesures() -> Dict[str, Any]:
        """Récupère la dernière mesure de chaque type"""
        try:
            async with get_db() as conn:
                rows = await conn.fetch("""
                    SELECT DISTINCT ON (t.code)
                           m.id, m.valeur, m.mesure_at,
                           t.code as type_code, t.unite, t.description
                    FROM mesures m
                    JOIN types_mesure t ON m.type_mesure_id = t.id
                    ORDER BY t.code, m.mesure_at DESC
                """)
                return {
                    "success": True,
                    "mesures": [dict(row) for row in rows],
                    "timestamp": datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error(f"Erreur récupération dernières mesures: {e}")
            return {"success": False, "error": str(e), "mesures": []}
    
    @staticmethod
    async def get_stats(period: str = "24h") -> Dict[str, Any]:
        """Calcule les statistiques par type de mesure"""
        intervals = {"1h": "1 hour", "6h": "6 hours", "24h": "1 day", "7d": "7 days", "30d": "30 days"}
        interval = intervals.get(period, "1 day")
        
        try:
            async with get_db() as conn:
                rows = await conn.fetch(f"""
                    SELECT t.code as type_code, t.unite,
                           COUNT(m.id) as count,
                           MIN(m.valeur) as min_value,
                           MAX(m.valeur) as max_value,
                           AVG(m.valeur) as avg_value,
                           (SELECT valeur FROM mesures 
                            WHERE type_mesure_id = t.id 
                            ORDER BY mesure_at DESC LIMIT 1) as last_value,
                           (SELECT mesure_at FROM mesures 
                            WHERE type_mesure_id = t.id 
                            ORDER BY mesure_at DESC LIMIT 1) as last_mesure_at
                    FROM types_mesure t
                    LEFT JOIN mesures m ON m.type_mesure_id = t.id 
                        AND m.mesure_at > NOW() - INTERVAL '{interval}'
                    GROUP BY t.id, t.code, t.unite
                    ORDER BY t.id
                """)
                
                stats = []
                for row in rows:
                    stats.append({
                        "type_code": row["type_code"],
                        "unite": row["unite"],
                        "count": row["count"] or 0,
                        "min_value": float(row["min_value"]) if row["min_value"] else None,
                        "max_value": float(row["max_value"]) if row["max_value"] else None,
                        "avg_value": round(float(row["avg_value"]), 2) if row["avg_value"] else None,
                        "last_value": float(row["last_value"]) if row["last_value"] else None,
                        "last_mesure_at": row["last_mesure_at"].isoformat() if row["last_mesure_at"] else None
                    })
                
                return {
                    "success": True,
                    "period": period,
                    "stats": stats
                }
        except Exception as e:
            logger.error(f"Erreur calcul statistiques: {e}")
            return {"success": False, "error": str(e), "stats": []}
    
    @staticmethod
    async def check_alerts() -> Dict[str, Any]:
        """Vérifie les seuils d'alerte sur les dernières mesures"""
        thresholds = {
            "TEMPERATURE": {"warning": 35, "critical": 45, "low_warning": 5, "low_critical": 0},
            "HUMIDITE": {"warning": 80, "critical": 90, "low_warning": 20, "low_critical": 10},
            "GAZ": {"warning": 100, "critical": 500}
        }
        
        try:
            latest = await MesureService.get_latest_mesures()
            if not latest.get("success"):
                return latest
            
            alerts = []
            for mesure in latest.get("mesures", []):
                type_code = mesure["type_code"]
                valeur = float(mesure["valeur"])
                threshold = thresholds.get(type_code, {})
                
                # Vérification seuils hauts
                if threshold.get("critical") and valeur >= threshold["critical"]:
                    alerts.append({
                        "type": type_code,
                        "severity": "CRITICAL",
                        "valeur": valeur,
                        "seuil": threshold["critical"],
                        "message": f"{type_code} critique: {valeur} {mesure['unite']}"
                    })
                elif threshold.get("warning") and valeur >= threshold["warning"]:
                    alerts.append({
                        "type": type_code,
                        "severity": "WARNING",
                        "valeur": valeur,
                        "seuil": threshold["warning"],
                        "message": f"{type_code} élevé: {valeur} {mesure['unite']}"
                    })
                
                # Vérification seuils bas (température et humidité)
                if threshold.get("low_critical") is not None and valeur <= threshold["low_critical"]:
                    alerts.append({
                        "type": type_code,
                        "severity": "CRITICAL",
                        "valeur": valeur,
                        "seuil": threshold["low_critical"],
                        "message": f"{type_code} critique (bas): {valeur} {mesure['unite']}"
                    })
                elif threshold.get("low_warning") is not None and valeur <= threshold["low_warning"]:
                    alerts.append({
                        "type": type_code,
                        "severity": "WARNING",
                        "valeur": valeur,
                        "seuil": threshold["low_warning"],
                        "message": f"{type_code} bas: {valeur} {mesure['unite']}"
                    })
            
            return {
                "success": True,
                "alerts": alerts,
                "has_critical": any(a["severity"] == "CRITICAL" for a in alerts),
                "has_warning": any(a["severity"] == "WARNING" for a in alerts),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur vérification alertes: {e}")
            return {"success": False, "error": str(e), "alerts": []}
