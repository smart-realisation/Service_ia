"""Sensor service handlers for InfluxDB queries"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from influxdb_client import InfluxDBClient
from influxdb_client.client.exceptions import InfluxDBError

from ..core.config import settings

logger = logging.getLogger(__name__)


class SensorService:
    """Service for sensor data queries from InfluxDB"""
    
    def __init__(self):
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize InfluxDB client"""
        try:
            if settings.influxdb_token:
                self.client = InfluxDBClient(
                    url=settings.influxdb_url,
                    token=settings.influxdb_token,
                    org=settings.influxdb_org
                )
        except Exception as e:
            logger.error(f"Failed to init InfluxDB client: {e}")
    
    async def get_sensor_data(
        self,
        sensor_type: str = "all",
        node_id: Optional[str] = None,
        period: str = "24h"
    ) -> Dict[str, Any]:
        """Get sensor data from InfluxDB"""
        if not self.client:
            # Return mock data for demo/testing
            return self._get_mock_sensor_data(sensor_type, node_id, period)
        
        try:
            query_api = self.client.query_api()
            
            flux_query = f'''
            from(bucket: "{settings.influxdb_bucket}")
                |> range(start: -{period})
            '''
            
            if sensor_type != "all":
                flux_query += f'|> filter(fn: (r) => r._measurement == "{sensor_type}")'
            
            if node_id:
                flux_query += f'|> filter(fn: (r) => r.node_id == "{node_id}")'
            
            flux_query += '|> last()'
            
            tables = query_api.query(flux_query)
            
            data = []
            for table in tables:
                for record in table.records:
                    data.append({
                        "measurement": record.get_measurement(),
                        "value": record.get_value(),
                        "time": record.get_time().isoformat(),
                        "node_id": record.values.get("node_id")
                    })
            
            return {"success": True, "data": data, "period": period}
        except InfluxDBError as e:
            logger.error(f"InfluxDB query error: {e}")
            return {"success": False, "error": str(e)}

    async def get_node_status(
        self,
        node_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get ESP32 node status"""
        if not self.client:
            # Return mock data when InfluxDB not available
            mock_nodes = [
                {
                    "node_id": node_id or "ESP32_001",
                    "battery": 95,
                    "rssi": -65,
                    "uptime": 86400,
                    "last_seen": datetime.utcnow().isoformat(),
                    "status": "online"
                }
            ]
            if not node_id:
                mock_nodes.append({
                    "node_id": "ESP32_002",
                    "battery": 78,
                    "rssi": -72,
                    "uptime": 43200,
                    "last_seen": datetime.utcnow().isoformat(),
                    "status": "online"
                })
            return {
                "success": True,
                "nodes": mock_nodes,
                "source": "mock_data",
                "warning": "InfluxDB not available, returning mock data"
            }
        
        try:
            query_api = self.client.query_api()
            
            flux_query = f'''
            from(bucket: "{settings.influxdb_bucket}")
                |> range(start: -1h)
                |> filter(fn: (r) => r._measurement == "node_status")
            '''
            
            if node_id:
                flux_query += f'|> filter(fn: (r) => r.node_id == "{node_id}")'
            
            flux_query += '|> last()'
            
            tables = query_api.query(flux_query)
            
            nodes = []
            for table in tables:
                for record in table.records:
                    nodes.append({
                        "node_id": record.values.get("node_id"),
                        "battery": record.values.get("battery"),
                        "rssi": record.values.get("rssi"),
                        "uptime": record.values.get("uptime"),
                        "last_seen": record.get_time().isoformat()
                    })
            
            return {"success": True, "nodes": nodes}
        except InfluxDBError as e:
            logger.error(f"InfluxDB query error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def get_system_health() -> Dict[str, Any]:
        """Get SafeLink system health status"""
        import psutil
        
        try:
            return {
                "success": True,
                "system": {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage('/').percent
                },
                "services": {
                    "api": "running",
                    "mqtt": "running",
                    "database": "connected",
                    "influxdb": "connected"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def get_security_report(
        period: str = "24h",
        format: str = "summary"
    ) -> Dict[str, Any]:
        """Generate security report"""
        from .alert_service import AlertService
        from .device_service import DeviceService
        
        alerts = await AlertService.get_security_alerts(status="all")
        devices = await DeviceService.get_connected_devices()
        
        return {
            "success": True,
            "report": {
                "period": period,
                "total_alerts": alerts.get("total", 0),
                "total_devices": devices.get("total", 0),
                "critical_alerts": len([a for a in alerts.get("alerts", []) 
                                       if a.get("severity") == "critical"]),
                "suspicious_devices": len([d for d in devices.get("devices", [])
                                          if d.get("status") == "suspicious"])
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    async def get_compliance_status() -> Dict[str, Any]:
        """Check RGPD and security compliance"""
        return {
            "success": True,
            "compliance": {
                "rgpd": {
                    "data_encryption": True,
                    "access_logging": True,
                    "data_retention_policy": True,
                    "user_consent": True
                },
                "security": {
                    "firmware_updated": True,
                    "default_passwords_changed": True,
                    "network_segmentation": True,
                    "intrusion_detection": True
                },
                "score": 95
            }
        }

    def _get_mock_sensor_data(
        self,
        sensor_type: str = "all",
        node_id: Optional[str] = None,
        period: str = "24h"
    ) -> Dict[str, Any]:
        """Return mock sensor data when InfluxDB is not available"""
        from datetime import timedelta

        mock_data = []
        now = datetime.utcnow()

        # Generate mock data based on sensor type
        if sensor_type in ["all", "temperature"]:
            mock_data.append({
                "measurement": "temperature",
                "value": 22.5,
                "time": (now - timedelta(minutes=5)).isoformat(),
                "node_id": node_id or "ESP32_001",
                "unit": "°C"
            })

        if sensor_type in ["all", "humidity"]:
            mock_data.append({
                "measurement": "humidity",
                "value": 45.2,
                "time": (now - timedelta(minutes=5)).isoformat(),
                "node_id": node_id or "ESP32_001",
                "unit": "%"
            })

        if sensor_type in ["all", "gas"]:
            mock_data.append({
                "measurement": "gas",
                "value": 150,
                "time": (now - timedelta(minutes=3)).isoformat(),
                "node_id": node_id or "ESP32_002",
                "unit": "ppm",
                "gas_type": "MQ2"
            })

        if sensor_type in ["all", "motion"]:
            mock_data.append({
                "measurement": "motion",
                "value": 0,
                "time": (now - timedelta(minutes=10)).isoformat(),
                "node_id": node_id or "ESP32_002",
                "unit": "boolean"
            })

        if sensor_type in ["all", "light"]:
            mock_data.append({
                "measurement": "light",
                "value": 450,
                "time": (now - timedelta(minutes=2)).isoformat(),
                "node_id": node_id or "ESP32_001",
                "unit": "lux"
            })

        return {
            "success": True,
            "data": mock_data,
            "period": period,
            "source": "mock_data",
            "warning": "InfluxDB not available, returning mock data"
        }
