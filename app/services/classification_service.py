"""Device Classification Service - Business logic layer"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..models.device_classifier import device_classifier
from ..core.database import DatabaseManager

logger = logging.getLogger(__name__)


class ClassificationService:
    """
    Service layer for device classification.
    Handles business logic, database interactions, and device inventory.
    """
    
    async def classify_and_store(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Classify device and update inventory"""
        result = device_classifier.classify(data)
        await self._update_device_inventory(result)
        
        if result["risk_level"] == "HIGH":
            await self._flag_high_risk_device(result)
        
        return result
    
    async def _update_device_inventory(self, result: Dict[str, Any]):
        """Update device in inventory database"""
        try:
            pool = DatabaseManager.get_pool()
            if not pool:
                logger.warning("Database not available for device inventory")
                return
            
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO device_inventory (
                        mac_address, ip_address, hostname, device_type,
                        vendor, risk_level, confidence, last_seen
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (mac_address) DO UPDATE SET
                        ip_address = EXCLUDED.ip_address,
                        hostname = EXCLUDED.hostname,
                        device_type = EXCLUDED.device_type,
                        vendor = EXCLUDED.vendor,
                        risk_level = EXCLUDED.risk_level,
                        confidence = EXCLUDED.confidence,
                        last_seen = EXCLUDED.last_seen
                """,
                    result["mac_address"],
                    result.get("ip_address"),
                    result.get("hostname"),
                    result["device_type"],
                    result["vendor"],
                    result["risk_level"],
                    result["confidence"],
                    datetime.now()
                )
        except Exception as e:
            logger.error(f"Failed to update device inventory: {e}")
    
    async def _flag_high_risk_device(self, result: Dict[str, Any]):
        """Flag high-risk device for review"""
        logger.warning(
            f"HIGH RISK DEVICE: {result['mac_address']} "
            f"({result['device_type']}) - {result['vendor']}"
        )
        # TODO: Send notification to admin
    
    async def get_device_inventory(
        self,
        risk_level: Optional[str] = None,
        device_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get device inventory from database"""
        try:
            pool = DatabaseManager.get_pool()
            if not pool:
                return []
            
            query = "SELECT * FROM device_inventory WHERE 1=1"
            params = []
            
            if risk_level:
                params.append(risk_level)
                query += f" AND risk_level = ${len(params)}"
            
            if device_type:
                params.append(device_type)
                query += f" AND device_type = ${len(params)}"
            
            query += " ORDER BY last_seen DESC"
            
            async with pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to fetch inventory: {e}")
            return []
    
    async def get_inventory_stats(self) -> Dict[str, Any]:
        """Get device inventory statistics"""
        try:
            pool = DatabaseManager.get_pool()
            if not pool:
                return {"error": "Database not available"}
            
            async with pool.acquire() as conn:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE risk_level = 'HIGH') as high_risk,
                        COUNT(*) FILTER (WHERE risk_level = 'MEDIUM') as medium_risk,
                        COUNT(*) FILTER (WHERE risk_level = 'LOW') as low_risk,
                        COUNT(*) FILTER (WHERE device_type = 'UNKNOWN') as unknown
                    FROM device_inventory
                """)
                
                type_counts = await conn.fetch("""
                    SELECT device_type, COUNT(*) as count
                    FROM device_inventory
                    GROUP BY device_type
                    ORDER BY count DESC
                """)
                
                return {
                    "total_devices": stats["total"],
                    "by_risk": {
                        "high": stats["high_risk"],
                        "medium": stats["medium_risk"],
                        "low": stats["low_risk"]
                    },
                    "unknown_devices": stats["unknown"],
                    "by_type": {row["device_type"]: row["count"] for row in type_counts}
                }
        except Exception as e:
            logger.error(f"Failed to get inventory stats: {e}")
            return {"error": str(e)}


# Singleton
classification_service = ClassificationService()
