"""Tests fonctionnels pour l'API Anomaly Detection"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.anomaly_detector import AnomalyDetector, anomaly_detector


client = TestClient(app)


class TestAnomalyDetectorModel:
    """Tests unitaires du modèle de détection d'anomalies"""
    
    def test_detect_normal_data(self):
        """Données normales ne doivent pas déclencher d'alerte"""
        data = {
            "device_id": "esp32-001",
            "temperature": 22.5,
            "humidity": 45.0,
            "gas_level": 5,
            "motion": False,
            "bytes_in": 50000,
            "bytes_out": 10000,
            "connection_count": 5,
            "unique_destinations": 3
        }
        result = anomaly_detector.detect(data)
        
        assert "is_anomaly" in result
        assert "anomaly_score" in result
        assert "severity" in result
        assert result["severity"] in ["NONE", "LOW"]
    
    def test_detect_temperature_critical(self):
        """Température > 60°C doit déclencher alerte CRITICAL"""
        data = {
            "device_id": "esp32-001",
            "temperature": 65.0,
            "humidity": 45.0,
            "gas_level": 5
        }
        result = anomaly_detector.detect(data)
        
        assert result["is_anomaly"] is True
        assert result["severity"] == "CRITICAL"
        assert "TEMPERATURE" in result["alert_type"]
    
    def test_detect_temperature_warning(self):
        """Température 45-60°C doit déclencher alerte HIGH"""
        data = {
            "device_id": "esp32-001",
            "temperature": 50.0,
            "humidity": 45.0,
            "gas_level": 5
        }
        result = anomaly_detector.detect(data)
        
        assert result["is_anomaly"] is True
        assert result["severity"] in ["HIGH", "CRITICAL"]
    
    def test_detect_gas_leak_critical(self):
        """Gaz > 500 ppm doit déclencher alerte CRITICAL"""
        data = {
            "device_id": "esp32-001",
            "temperature": 22.0,
            "humidity": 45.0,
            "gas_level": 600
        }
        result = anomaly_detector.detect(data)
        
        assert result["is_anomaly"] is True
        assert result["severity"] == "CRITICAL"
        assert "GAS" in result["alert_type"]
    
    def test_detect_gas_leak_warning(self):
        """Gaz 100-500 ppm doit déclencher alerte HIGH"""
        data = {
            "device_id": "esp32-001",
            "temperature": 22.0,
            "gas_level": 200
        }
        result = anomaly_detector.detect(data)
        
        assert result["is_anomaly"] is True
        assert result["severity"] in ["HIGH", "CRITICAL"]
    
    def test_detect_data_exfiltration(self):
        """Bytes out > 10MB doit déclencher alerte"""
        data = {
            "device_id": "esp32-001",
            "temperature": 22.0,
            "bytes_out": 60_000_000  # 60MB
        }
        result = anomaly_detector.detect(data)
        
        assert result["is_anomaly"] is True
        assert result["severity"] in ["HIGH", "CRITICAL"]
    
    def test_detect_suspicious_connections(self):
        """Connexions > 100 doit déclencher alerte"""
        data = {
            "device_id": "esp32-001",
            "temperature": 22.0,
            "connection_count": 200
        }
        result = anomaly_detector.detect(data)
        
        assert result["is_anomaly"] is True
    
    def test_batch_detect(self):
        """Test détection en batch"""
        data_list = [
            {"temperature": 22.0, "gas_level": 5},
            {"temperature": 65.0, "gas_level": 5},
            {"temperature": 22.0, "gas_level": 600}
        ]
        results = anomaly_detector.batch_detect(data_list)
        
        assert len(results) == 3
        assert results[0]["is_anomaly"] is False or results[0]["severity"] == "LOW"
        assert results[1]["is_anomaly"] is True  # Temp critique
        assert results[2]["is_anomaly"] is True  # Gaz critique


class TestAnalysisAPI:
    """Tests fonctionnels de l'API /analysis"""
    
    def test_analyze_endpoint_normal(self):
        """POST /analyze avec données normales"""
        response = client.post("/api/v1/analysis/analyze", json={
            "device_id": "esp32-test",
            "temperature": 22.5,
            "humidity": 45.0,
            "gas_level": 5,
            "motion": False,
            "bytes_in": 50000,
            "bytes_out": 10000,
            "connection_count": 5,
            "unique_destinations": 3
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "is_anomaly" in data
        assert "anomaly_score" in data
        assert "alert_type" in data
        assert "severity" in data
    
    def test_analyze_endpoint_anomaly(self):
        """POST /analyze avec anomalie température"""
        response = client.post("/api/v1/analysis/analyze", json={
            "device_id": "esp32-test",
            "temperature": 70.0,
            "humidity": 45.0,
            "gas_level": 5
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_anomaly"] is True
        assert data["severity"] == "CRITICAL"
    
    def test_analyze_batch_endpoint(self):
        """POST /analyze/batch"""
        response = client.post("/api/v1/analysis/analyze/batch", json={
            "data": [
                {"temperature": 22.0, "humidity": 50},
                {"temperature": 55.0, "humidity": 50},
                {"temperature": 22.0, "gas_level": 300}
            ]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert "anomalies_found" in data
        assert "critical_count" in data
        assert "results" in data
        assert len(data["results"]) == 3
    
    def test_thresholds_endpoint(self):
        """GET /thresholds"""
        response = client.get("/api/v1/analysis/thresholds")
        
        assert response.status_code == 200
        data = response.json()
        assert "temperature" in data
        assert "gas_level" in data
        assert "bytes_out" in data
    
    def test_analyze_minimal_data(self):
        """POST /analyze avec données minimales"""
        response = client.post("/api/v1/analysis/analyze", json={
            "temperature": 22.0
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "is_anomaly" in data
    
    def test_analyze_with_timestamp(self):
        """POST /analyze avec timestamp"""
        response = client.post("/api/v1/analysis/analyze", json={
            "device_id": "esp32-test",
            "temperature": 22.0,
            "timestamp": "2025-12-15T14:30:00Z"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == "esp32-test"
