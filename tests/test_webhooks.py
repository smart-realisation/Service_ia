"""Tests fonctionnels pour l'API Webhooks"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestWebhooksAPI:
    """Tests fonctionnels des webhooks MQTT"""
    
    def test_device_webhook(self):
        """POST /webhooks/mqtt/device"""
        response = client.post("/api/v1/webhooks/mqtt/device", json={
            "topic": "safelink/devices/esp32-001",
            "payload": {
                "device_id": "esp32-001",
                "status": "online",
                "ip_address": "192.168.1.100"
            },
            "timestamp": "2025-12-15T10:00:00Z"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "message" in data
    
    def test_device_webhook_suspicious(self):
        """POST /webhooks/mqtt/device avec status suspicious"""
        response = client.post("/api/v1/webhooks/mqtt/device", json={
            "topic": "safelink/devices/unknown-001",
            "payload": {
                "device_id": "unknown-001",
                "status": "suspicious"
            },
            "timestamp": "2025-12-15T10:00:00Z"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_alert_webhook(self):
        """POST /webhooks/mqtt/alert"""
        response = client.post("/api/v1/webhooks/mqtt/alert", json={
            "topic": "safelink/alerts",
            "payload": {
                "severity": "warning",
                "message": "Unusual network activity detected",
                "device_id": "esp32-001"
            },
            "timestamp": "2025-12-15T10:00:00Z"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_alert_webhook_critical(self):
        """POST /webhooks/mqtt/alert avec severity critical"""
        response = client.post("/api/v1/webhooks/mqtt/alert", json={
            "topic": "safelink/alerts/critical",
            "payload": {
                "severity": "critical",
                "message": "Intrusion detected",
                "device_id": "camera-001"
            },
            "timestamp": "2025-12-15T10:00:00Z"
        })
        
        assert response.status_code == 200
    
    def test_sensor_webhook(self):
        """POST /webhooks/mqtt/sensor"""
        response = client.post("/api/v1/webhooks/mqtt/sensor", json={
            "topic": "safelink/sensors/temperature",
            "payload": {
                "sensor_id": "temp-01",
                "value": 22.5,
                "unit": "celsius"
            },
            "timestamp": "2025-12-15T10:00:00Z"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_sensor_webhook_humidity(self):
        """POST /webhooks/mqtt/sensor pour humidité"""
        response = client.post("/api/v1/webhooks/mqtt/sensor", json={
            "topic": "safelink/sensors/humidity",
            "payload": {
                "sensor_id": "hum-01",
                "value": 45.0,
                "unit": "percent"
            },
            "timestamp": "2025-12-15T10:00:00Z"
        })
        
        assert response.status_code == 200
    
    def test_webhook_invalid_payload(self):
        """POST webhook avec payload invalide"""
        response = client.post("/api/v1/webhooks/mqtt/device", json={
            "topic": "safelink/devices/test",
            # Missing payload
            "timestamp": "2025-12-15T10:00:00Z"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_webhook_empty_payload(self):
        """POST webhook avec payload vide"""
        response = client.post("/api/v1/webhooks/mqtt/device", json={
            "topic": "safelink/devices/test",
            "payload": {},
            "timestamp": "2025-12-15T10:00:00Z"
        })
        
        assert response.status_code == 200


class TestHealthAPI:
    """Tests de l'endpoint health"""
    
    def test_root_endpoint(self):
        """GET /"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "SafeLink AI"
        assert data["status"] == "running"
        assert "version" in data
    
    def test_health_endpoint(self):
        """GET /api/v1/health"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "llm_enabled" in data
        assert "database_connected" in data
        assert "redis_connected" in data
        assert "mqtt_connected" in data
    
    def test_suggestions_endpoint(self):
        """GET /api/v1/suggestions"""
        response = client.get("/api/v1/suggestions?user_role=IT_MANAGER")
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "IT_MANAGER"
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0
    
    def test_suggestions_default_role(self):
        """GET /api/v1/suggestions sans rôle"""
        response = client.get("/api/v1/suggestions")
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "HOME_USER"
