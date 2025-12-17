"""Anomaly Detection Service - Business logic layer"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..models.anomaly_detector import anomaly_detector
from ..core.database import DatabaseManager

logger = logging.getLogger(__name__)


class AnomalyService:
    """
    Service layer for anomaly detection.
    Handles business logic, database interactions, and alert generation.
    """
    
    async def analyze_and_store(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data and store result if anomaly detected"""
        result = anomaly_detector.detect(data)
        
        if result["is_anomaly"]:
            await self._store_alert(result)
            await self._notify_if_critical(result)
        
        return result
    
    async def _store_alert(self, result: Dict[str, Any]):
        """Store alert in database"""
        try:
            pool = DatabaseManager.get_pool()
            if not pool:
                logger.warning("Database not available for alert storage")
                return
            
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO alerts (
                        device_id, sensor_id, alert_type, severity,
                        anomaly_score, details, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                    result.get("device_id"),
                    result.get("sensor_id"),
                    result["alert_type"],
                    result["severity"],
                    result["anomaly_score"],
                    str(result["details"]),
                    datetime.now()
                )
        except Exception as e:
            logger.error(f"Failed to store alert: {e}")
    
    async def _notify_if_critical(self, result: Dict[str, Any]):
        """Send notification for critical alerts"""
        if result["severity"] in ["CRITICAL", "HIGH"]:
            logger.warning(
                f"ALERT [{result['severity']}]: {result['alert_type']} "
                f"on device {result.get('device_id', 'unknown')}"
            )
            # TODO: Integrate with notification service (FCM, email, etc.)
    
    async def get_recent_anomalies(
        self, 
        hours: int = 24, 
        device_id: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent anomalies from database"""
        try:
            pool = DatabaseManager.get_pool()
            if not pool:
                return []
            
            query = """
                SELECT * FROM alerts 
                WHERE created_at > $1
            """
            params = [datetime.now() - timedelta(hours=hours)]
            
            if device_id:
                query += " AND device_id = $2"
                params.append(device_id)
            
            if severity:
                query += f" AND severity = ${len(params) + 1}"
                params.append(severity)
            
            query += " ORDER BY created_at DESC LIMIT 100"
            
            async with pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to fetch anomalies: {e}")
            return []
    
    async def get_anomaly_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get anomaly statistics"""
        try:
            pool = DatabaseManager.get_pool()
            if not pool:
                return {"error": "Database not available"}
            
            since = datetime.now() - timedelta(hours=hours)
            
            async with pool.acquire() as conn:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE severity = 'CRITICAL') as critical,
                        COUNT(*) FILTER (WHERE severity = 'HIGH') as high,
                        COUNT(*) FILTER (WHERE severity = 'MEDIUM') as medium,
                        COUNT(*) FILTER (WHERE severity = 'LOW') as low
                    FROM alerts
                    WHERE created_at > $1
                """, since)
                
                return {
                    "period_hours": hours,
                    "total_anomalies": stats["total"],
                    "by_severity": {
                        "critical": stats["critical"],
                        "high": stats["high"],
                        "medium": stats["medium"],
                        "low": stats["low"]
                    }
                }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}


# Singleton
anomaly_service = AnomalyService()
