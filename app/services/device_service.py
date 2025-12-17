"""Device and network service handlers"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..core.database import get_db

logger = logging.getLogger(__name__)


class DeviceService:
    """Service for device and network related queries"""
    
    @staticmethod
    async def get_connected_devices(
        status: str = "all",
        zone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get list of connected devices"""
        try:
            async with get_db() as conn:
                query = "SELECT * FROM devices WHERE 1=1"
                params = []
                
                if status != "all":
                    params.append(status)
                    query += f" AND status = ${len(params)}"
                
                if zone:
                    params.append(zone)
                    query += f" AND zone = ${len(params)}"
                
                rows = await conn.fetch(query, *params)
                devices = [dict(row) for row in rows]
                
                return {
                    "success": True,
                    "total": len(devices),
                    "devices": devices,
                    "timestamp": datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error(f"Error fetching devices: {e}")
            return {"success": False, "error": str(e), "devices": []}

    @staticmethod
    async def get_device_details(device_id: str) -> Dict[str, Any]:
        """Get detailed info for a specific device"""
        try:
            async with get_db() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM devices WHERE id = $1 OR mac_address = $1",
                    device_id
                )
                if row:
                    return {"success": True, "device": dict(row)}
                return {"success": False, "error": "Device not found"}
        except Exception as e:
            logger.error(f"Error fetching device details: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def get_network_traffic(
        device_id: Optional[str] = None,
        period: str = "24h"
    ) -> Dict[str, Any]:
        """Get network traffic analysis"""
        try:
            async with get_db() as conn:
                query = """
                    SELECT device_id, SUM(bytes_in) as total_in, 
                           SUM(bytes_out) as total_out,
                           COUNT(DISTINCT destination) as unique_destinations
                    FROM network_traffic
                    WHERE timestamp > NOW() - INTERVAL '1 day'
                """
                params = []
                if device_id:
                    params.append(device_id)
                    query += f" AND device_id = ${len(params)}"
                query += " GROUP BY device_id"
                
                rows = await conn.fetch(query, *params)
                return {
                    "success": True,
                    "traffic": [dict(row) for row in rows],
                    "period": period
                }
        except Exception as e:
            logger.error(f"Error fetching traffic: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def get_new_devices(since: str = "24h") -> Dict[str, Any]:
        """Get newly detected devices"""
        intervals = {"1h": "1 hour", "24h": "1 day", "7d": "7 days"}
        interval = intervals.get(since, "1 day")
        
        try:
            async with get_db() as conn:
                rows = await conn.fetch(
                    f"""SELECT * FROM devices 
                        WHERE first_seen > NOW() - INTERVAL '{interval}'
                        ORDER BY first_seen DESC"""
                )
                return {
                    "success": True,
                    "new_devices": [dict(row) for row in rows],
                    "since": since
                }
        except Exception as e:
            logger.error(f"Error fetching new devices: {e}")
            return {"success": False, "error": str(e)}
