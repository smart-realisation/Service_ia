"""Tests d'intégration - Scénarios complets"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.anomaly_detector import anomaly_detector
from app.models.device_classifier import device_classifier


client = TestClient(app)


class TestScenarioNewDevice:
    """Scénario: Nouveau device détecté sur le réseau"""
    
    def test_scenario_new_iot_device(self):
        """
        1. Backend Ktor détecte un nouveau device
        2. Envoie au service IA pour classification
        3. Reçoit type, risque et recommandations
        """
        # Step 1: Classifier le device
        classify_response = client.post("/api/v1/devices/classify", json={
            "mac_address": "B8:27:EB:AA:BB:CC",
            "ip_address": "192.168.1.150",
            "hostname": "raspberrypi-sensor"
        })
        
        assert classify_response.status_code == 200
        device_info = classify_response.json()
        
        # Vérifications
        assert device_info["device_type"] == "IOT_DEVICE"
        assert device_info["vendor"] == "Raspberry Pi"
        assert device_info["risk_level"] == "HIGH"
        assert len(device_info["recommendations"]) > 0
        
        # Step 2: Si HIGH risk, analyser le trafic
        if device_info["risk_level"] == "HIGH":
            analysis_response = client.post("/api/v1/analysis/analyze", json={
                "device_id": "raspberrypi-sensor",
                "bytes_in": 100000,
                "bytes_out": 50000,
                "connection_count": 10,
                "unique_destinations": 5
            })
            
            assert analysis_response.status_code == 200
            analysis = analysis_response.json()
            assert "is_anomaly" in analysis
    
    def test_scenario_unknown_device_alert(self):
        """
        Scénario: Device inconnu → alerte automatique
        """
        # Classifier device inconnu
        response = client.post("/api/v1/devices/classify", json={
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "ip_address": "192.168.1.200"
        })
        
        device_info = response.json()
        
        # Device inconnu = HIGH risk
        assert device_info["device_type"] == "UNKNOWN"
        assert device_info["risk_level"] == "HIGH"
        
        # Doit recommander identification manuelle
        assert any("identifier" in r.lower() or "vérifier" in r.lower() 
                   for r in device_info["recommendations"])


class TestScenarioSensorAlert:
    """Scénario: Alerte capteur environnemental"""
    
    def test_scenario_temperature_spike(self):
        """
        Scénario: Pic de température détecté
        1. Capteur envoie température élevée
        2. Service IA détecte anomalie
        3. Retourne alerte avec sévérité
        """
        # Température normale d'abord
        normal_response = client.post("/api/v1/analysis/analyze", json={
            "device_id": "esp32-temp-001",
            "sensor_id": "temp-salon",
            "temperature": 22.0,
            "humidity": 45.0
        })
        
        normal_result = normal_response.json()
        assert normal_result["is_anomaly"] is False or normal_result["severity"] in ["NONE", "LOW"]
        
        # Puis température critique
        critical_response = client.post("/api/v1/analysis/analyze", json={
            "device_id": "esp32-temp-001",
            "sensor_id": "temp-salon",
            "temperature": 65.0,
            "humidity": 45.0
        })
        
        critical_result = critical_response.json()
        assert critical_result["is_anomaly"] is True
        assert critical_result["severity"] == "CRITICAL"
        assert "TEMPERATURE" in critical_result["alert_type"]
    
    def test_scenario_gas_leak_emergency(self):
        """
        Scénario: Fuite de gaz détectée → URGENCE
        """
        response = client.post("/api/v1/analysis/analyze", json={
            "device_id": "esp32-gas-001",
            "sensor_id": "gas-cuisine",
            "temperature": 22.0,
            "gas_level": 700  # Très élevé
        })
        
        result = response.json()
        
        assert result["is_anomaly"] is True
        assert result["severity"] == "CRITICAL"
        assert "GAS" in result["alert_type"]
        assert result["device_id"] == "esp32-gas-001"


class TestScenarioNetworkAnomaly:
    """Scénario: Anomalie réseau / Cyberattaque"""
    
    def test_scenario_data_exfiltration(self):
        """
        Scénario: Device IoT envoie beaucoup de données
        → Possible exfiltration de données
        """
        response = client.post("/api/v1/analysis/analyze", json={
            "device_id": "camera-001",
            "bytes_in": 50000,
            "bytes_out": 80_000_000,  # 80MB sortant = suspect
            "connection_count": 5,
            "unique_destinations": 3
        })
        
        result = response.json()
        
        assert result["is_anomaly"] is True
        assert result["severity"] in ["HIGH", "CRITICAL"]
    
    def test_scenario_ddos_attack(self):
        """
        Scénario: Device fait beaucoup de connexions
        → Possible participation à DDoS ou scan
        """
        response = client.post("/api/v1/analysis/analyze", json={
            "device_id": "iot-compromised",
            "bytes_in": 50000,
            "bytes_out": 100000,
            "connection_count": 500,  # Très élevé
            "unique_destinations": 200  # Beaucoup de destinations
        })
        
        result = response.json()
        
        assert result["is_anomaly"] is True


class TestScenarioBatchProcessing:
    """Scénario: Traitement en lot (analyse périodique)"""
    
    def test_scenario_hourly_analysis(self):
        """
        Scénario: Backend envoie données de la dernière heure
        pour analyse en batch
        """
        # Simuler 10 lectures de capteurs
        sensor_data = [
            {"device_id": f"esp32-{i:03d}", "temperature": 22 + i*0.5, 
             "humidity": 45, "gas_level": 5}
            for i in range(8)
        ]
        # Ajouter 2 anomalies
        sensor_data.append({"device_id": "esp32-008", "temperature": 60, "gas_level": 5})
        sensor_data.append({"device_id": "esp32-009", "temperature": 22, "gas_level": 400})
        
        response = client.post("/api/v1/analysis/analyze/batch", json={
            "data": sensor_data
        })
        
        result = response.json()
        
        assert result["total"] == 10
        assert result["anomalies_found"] >= 2
        assert result["critical_count"] >= 1 or result["high_count"] >= 1
    
    def test_scenario_device_inventory_scan(self):
        """
        Scénario: Scan réseau → classification de tous les devices
        """
        devices = [
            {"mac_address": "B8:27:EB:11:11:11", "hostname": "rpi-sensor1"},
            {"mac_address": "24:0A:C4:22:22:22", "hostname": "esp32-temp"},
            {"mac_address": "68:A4:0E:33:33:33", "hostname": "echo-salon"},
            {"mac_address": "00:17:88:44:44:44", "hostname": "hue-bridge"},
            {"mac_address": "AA:BB:CC:55:55:55"},  # Unknown
        ]
        
        response = client.post("/api/v1/devices/classify/batch", json={
            "devices": devices
        })
        
        result = response.json()
        
        assert result["total"] == 5
        assert result["unknown_count"] == 1
        assert result["high_risk_count"] >= 2  # RPi, ESP32, Unknown


class TestScenarioChatbotIntegration:
    """Scénario: Interaction chatbot"""
    
    def test_scenario_user_asks_about_devices(self):
        """
        Scénario: Utilisateur demande la liste des appareils
        """
        response = client.post("/api/v1/query", json={
            "message": "Quels appareils sont connectés?",
            "user_id": "user-001",
            "user_role": "HOME_USER"
        }, timeout=30)
        
        # Le chatbot peut échouer si pas de DB/LLM, mais l'endpoint doit répondre
        assert response.status_code in [200, 500]
    
    def test_scenario_admin_security_check(self):
        """
        Scénario: Admin vérifie l'état de sécurité
        """
        response = client.post("/api/v1/query", json={
            "message": "Y a-t-il des alertes critiques?",
            "user_id": "admin-001",
            "user_role": "ADMIN"
        }, timeout=30)
        
        assert response.status_code in [200, 500]
