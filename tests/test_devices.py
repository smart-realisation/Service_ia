"""Tests fonctionnels pour l'API Device Classification"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.device_classifier import DeviceClassifier, device_classifier


client = TestClient(app)


class TestDeviceClassifierModel:
    """Tests unitaires du modèle de classification"""
    
    def test_classify_raspberry_pi(self):
        """Raspberry Pi doit être reconnu par OUI"""
        data = {
            "mac_address": "B8:27:EB:12:34:56",
            "ip_address": "192.168.1.100"
        }
        result = device_classifier.classify(data)
        
        assert result["device_type"] == "IOT_DEVICE"
        assert result["vendor"] == "Raspberry Pi"
        assert result["risk_level"] == "HIGH"
        assert result["confidence"] >= 0.9
    
    def test_classify_esp32(self):
        """ESP32 (Espressif) doit être reconnu"""
        data = {
            "mac_address": "24:0A:C4:AA:BB:CC",
            "hostname": "esp32-sensor"
        }
        result = device_classifier.classify(data)
        
        assert result["device_type"] == "IOT_DEVICE"
        assert result["vendor"] == "Espressif"
        assert result["risk_level"] == "HIGH"
    
    def test_classify_amazon_echo(self):
        """Amazon Echo doit être reconnu"""
        data = {
            "mac_address": "68:A4:0E:11:22:33",
            "hostname": "echo-dot"
        }
        result = device_classifier.classify(data)
        
        assert result["device_type"] == "SMART_SPEAKER"
        assert result["vendor"] == "Amazon"
        assert result["risk_level"] == "MEDIUM"
    
    def test_classify_philips_hue(self):
        """Philips Hue doit être reconnu"""
        data = {
            "mac_address": "00:17:88:AA:BB:CC"
        }
        result = device_classifier.classify(data)
        
        assert result["device_type"] == "SMART_LIGHT"
        assert result["vendor"] == "Philips Hue"
        assert result["risk_level"] == "LOW"
    
    def test_classify_unknown_device(self):
        """Appareil inconnu doit avoir risque HIGH"""
        data = {
            "mac_address": "AA:BB:CC:DD:EE:FF"
        }
        result = device_classifier.classify(data)
        
        assert result["device_type"] == "UNKNOWN"
        assert result["vendor"] == "Unknown"
        assert result["risk_level"] == "HIGH"
        assert result["confidence"] < 0.5
    
    def test_classify_by_hostname_android(self):
        """Android doit être reconnu par hostname"""
        data = {
            "mac_address": "11:22:33:44:55:66",
            "hostname": "android-phone-john"
        }
        result = device_classifier.classify(data)
        
        assert result["device_type"] == "SMARTPHONE"
        assert result["risk_level"] == "LOW"
    
    def test_classify_by_hostname_iphone(self):
        """iPhone doit être reconnu par hostname"""
        data = {
            "mac_address": "11:22:33:44:55:67",
            "hostname": "iPhone-de-Marie"
        }
        result = device_classifier.classify(data)
        
        assert result["device_type"] == "SMARTPHONE"
    
    def test_classify_by_hostname_camera(self):
        """Caméra doit être reconnue par hostname"""
        data = {
            "mac_address": "11:22:33:44:55:68",
            "hostname": "camera-front-door"
        }
        result = device_classifier.classify(data)
        
        assert result["device_type"] == "CAMERA"
        assert result["risk_level"] == "HIGH"
    
    def test_classify_by_hostname_tv(self):
        """Smart TV doit être reconnue par hostname"""
        data = {
            "mac_address": "11:22:33:44:55:69",
            "hostname": "samsung-tv-salon"
        }
        result = device_classifier.classify(data)
        
        assert result["device_type"] == "SMART_TV"
        assert result["risk_level"] == "MEDIUM"
    
    def test_recommendations_high_risk(self):
        """Appareil HIGH risk doit avoir des recommandations"""
        data = {
            "mac_address": "AA:BB:CC:DD:EE:FF"
        }
        result = device_classifier.classify(data)
        
        assert len(result["recommendations"]) > 0
        assert any("VLAN" in r or "Isoler" in r for r in result["recommendations"])
    
    def test_recommendations_camera(self):
        """Caméra doit avoir recommandations spécifiques"""
        data = {
            "mac_address": "11:22:33:44:55:70",
            "hostname": "ip-camera-garage"
        }
        result = device_classifier.classify(data)
        
        assert any("firmware" in r.lower() for r in result["recommendations"])
    
    def test_batch_classify(self):
        """Test classification en batch"""
        devices = [
            {"mac_address": "B8:27:EB:11:11:11"},
            {"mac_address": "24:0A:C4:22:22:22"},
            {"mac_address": "AA:BB:CC:33:33:33"}
        ]
        results = device_classifier.batch_classify(devices)
        
        assert len(results) == 3
        assert results[0]["vendor"] == "Raspberry Pi"
        assert results[1]["vendor"] == "Espressif"
        assert results[2]["vendor"] == "Unknown"
    
    def test_mac_address_formats(self):
        """Test différents formats MAC"""
        # Format avec tirets
        result1 = device_classifier.classify({"mac_address": "B8-27-EB-12-34-56"})
        assert result1["vendor"] == "Raspberry Pi"
        
        # Format minuscules
        result2 = device_classifier.classify({"mac_address": "b8:27:eb:12:34:56"})
        assert result2["vendor"] == "Raspberry Pi"


class TestDevicesAPI:
    """Tests fonctionnels de l'API /devices"""
    
    def test_classify_endpoint(self):
        """POST /classify"""
        response = client.post("/api/v1/devices/classify", json={
            "mac_address": "B8:27:EB:12:34:56",
            "ip_address": "192.168.1.100",
            "hostname": "raspberrypi"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "device_type" in data
        assert "vendor" in data
        assert "risk_level" in data
        assert "confidence" in data
        assert "recommendations" in data
        assert "classified_at" in data
    
    def test_classify_endpoint_minimal(self):
        """POST /classify avec MAC uniquement"""
        response = client.post("/api/v1/devices/classify", json={
            "mac_address": "24:0A:C4:AA:BB:CC"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["vendor"] == "Espressif"
    
    def test_classify_endpoint_unknown(self):
        """POST /classify appareil inconnu"""
        response = client.post("/api/v1/devices/classify", json={
            "mac_address": "AA:BB:CC:DD:EE:FF"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["device_type"] == "UNKNOWN"
        assert data["risk_level"] == "HIGH"
    
    def test_classify_batch_endpoint(self):
        """POST /classify/batch"""
        response = client.post("/api/v1/devices/classify/batch", json={
            "devices": [
                {"mac_address": "B8:27:EB:11:11:11"},
                {"mac_address": "24:0A:C4:22:22:22"},
                {"mac_address": "AA:BB:CC:33:33:33", "hostname": "camera-front"}
            ]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert "high_risk_count" in data
        assert "unknown_count" in data
        assert len(data["results"]) == 3
    
    def test_risk_levels_endpoint(self):
        """GET /risk-levels"""
        response = client.get("/api/v1/devices/risk-levels")
        
        assert response.status_code == 200
        data = response.json()
        assert "risk_levels" in data
        assert "description" in data
        assert "IOT_DEVICE" in data["risk_levels"]
        assert data["risk_levels"]["IOT_DEVICE"] == "HIGH"
    
    def test_known_vendors_endpoint(self):
        """GET /known-vendors"""
        response = client.get("/api/v1/devices/known-vendors")
        
        assert response.status_code == 200
        data = response.json()
        assert "vendors" in data
        assert "total_oui" in data
        assert "Raspberry Pi" in data["vendors"]
        assert "Espressif" in data["vendors"]
    
    def test_classify_with_behavioral_data(self):
        """POST /classify avec données comportementales"""
        response = client.post("/api/v1/devices/classify", json={
            "mac_address": "11:22:33:44:55:66",
            "avg_bytes_in": 50000,
            "avg_bytes_out": 10000,
            "ports_used": [80, 443, 1883],
            "connection_frequency": 100,
            "active_hours": 24
        })
        
        assert response.status_code == 200
        data = response.json()
        # MQTT port suggests IoT
        assert data["device_type"] == "IOT_DEVICE"
    
    def test_classify_missing_mac(self):
        """POST /classify sans MAC doit échouer"""
        response = client.post("/api/v1/devices/classify", json={
            "ip_address": "192.168.1.100"
        })
        
        assert response.status_code == 422  # Validation error
