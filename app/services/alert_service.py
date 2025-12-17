"""Alert service handlers"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.database import get_db

logger = logging.getLogger(__name__)


class AlertService:
    """Service for security alerts queries"""
    
    @staticmethod
    async def get_security_alerts(
        severity: str = "all",
        status: str = "active",
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get security alerts"""
        try:
            async with get_db() as conn:
                query = "SELECT * FROM alerts WHERE 1=1"
                params = []
                
                if severity != "all":
                    params.append(severity)
                    query += f" AND severity = ${len(params)}"
                
                if status != "all":
                    params.append(status)
                    query += f" AND status = ${len(params)}"
                
                params.append(limit)
                query += f" ORDER BY created_at DESC LIMIT ${len(params)}"
                
                rows = await conn.fetch(query, *params)
                alerts = [dict(row) for row in rows]
                
                return {
                    "success": True,
                    "total": len(alerts),
                    "alerts": alerts,
                    "timestamp": datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error(f"Error fetching alerts: {e}")
            return {"success": False, "error": str(e), "alerts": []}

    @staticmethod
    async def get_anomalies(
        anomaly_type: str = "all",
        period: str = "24h"
    ) -> Dict[str, Any]:
        """Get detected anomalies"""
        intervals = {"24h": "1 day", "7d": "7 days", "30d": "30 days"}
        interval = intervals.get(period, "1 day")
        
        try:
            async with get_db() as conn:
                query = f"""
                    SELECT * FROM anomalies 
                    WHERE detected_at > NOW() - INTERVAL '{interval}'
                """
                params = []
                if anomaly_type != "all":
                    params.append(anomaly_type)
                    query += f" AND type = ${len(params)}"
                query += " ORDER BY detected_at DESC"
                
                rows = await conn.fetch(query, *params)
                return {
                    "success": True,
                    "anomalies": [dict(row) for row in rows],
                    "period": period
                }
        except Exception as e:
            logger.error(f"Error fetching anomalies: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def explain_alert(alert_id: str) -> Dict[str, Any]:
        """Get detailed explanation for an alert"""
        try:
            async with get_db() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM alerts WHERE id = $1", alert_id
                )
                if not row:
                    return {"success": False, "error": "Alert not found"}
                
                alert = dict(row)
                explanations = {
                    "intrusion": "Tentative d'accès non autorisé détectée",
                    "anomaly": "Comportement inhabituel sur le réseau",
                    "gas": "Détection de gaz potentiellement dangereux",
                    "motion": "Mouvement détecté dans une zone surveillée"
                }
                
                alert["explanation"] = explanations.get(
                    alert.get("type", ""), 
                    "Alerte de sécurité"
                )
                return {"success": True, "alert": alert}
        except Exception as e:
            logger.error(f"Error explaining alert: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def get_environmental_alerts(
        severity: str = "all"
    ) -> Dict[str, Any]:
        """Get environmental alerts (gas, temperature, motion)"""
        try:
            async with get_db() as conn:
                query = """
                    SELECT * FROM alerts 
                    WHERE type IN ('gas', 'temperature', 'motion', 'humidity')
                    AND status = 'active'
                """
                params = []
                if severity != "all":
                    params.append(severity)
                    query += f" AND severity = ${len(params)}"
                query += " ORDER BY created_at DESC"
                
                rows = await conn.fetch(query, *params)
                return {
                    "success": True,
                    "alerts": [dict(row) for row in rows]
                }
        except Exception as e:
            logger.error(f"Error fetching environmental alerts: {e}")
            return {"success": False, "error": str(e)}
