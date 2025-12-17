"""Tests fonctionnels pour l'API Mesures"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app


client = TestClient(app)


class TestMesuresAPI:
    """Tests fonctionnels de l'API /mesures"""
    
    def test_get_types_mesure(self):
        """GET /mesures/types - Liste des types de mesure"""
        with patch('app.services.mesure_service.get_db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetch.return_value = [
                {"id": 1, "code": "TEMPERATURE", "unite": "CELSIUS", "description": "Température ambiante"},
                {"id": 2, "code": "HUMIDITE", "unite": "POURCENT", "description": "Humidité relative"},
                {"id": 3, "code": "GAZ", "unite": "PPM", "description": "Concentration de gaz"}
            ]
            mock_db.return_value.__aenter__.return_value = mock_conn
            
            response = client.get("/api/v1/mesures/types")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["types"]) == 3
    
    def test_get_thresholds(self):
        """GET /mesures/thresholds - Seuils d'alerte"""
        response = client.get("/api/v1/mesures/thresholds")
        
        assert response.status_code == 200
        data = response.json()
        assert "thresholds" in data
        assert "TEMPERATURE" in data["thresholds"]
        assert "HUMIDITE" in data["thresholds"]
        assert "GAZ" in data["thresholds"]
        
        # Vérifier les seuils température
        temp = data["thresholds"]["TEMPERATURE"]
        assert temp["unite"] == "CELSIUS"
        assert temp["warning"] == 35
        assert temp["critical"] == 45
        
        # Vérifier les seuils gaz
        gaz = data["thresholds"]["GAZ"]
        assert gaz["unite"] == "PPM"
        assert gaz["warning"] == 100
        assert gaz["critical"] == 500
    
    def test_create_mesure_temperature(self):
        """POST /mesures - Créer une mesure de température"""
        with patch('app.services.mesure_service.get_db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchrow.return_value = {
                "id": 1,
                "type_mesure_id": 1,
                "valeur": 22.5,
                "mesure_at": "2025-12-17T10:00:00"
            }
            mock_db.return_value.__aenter__.return_value = mock_conn
            
            response = client.post("/api/v1/mesures/", json={
                "type_mesure_id": 1,
                "valeur": 22.5
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["mesure"]["valeur"] == 22.5
    
    def test_create_mesure_humidity(self):
        """POST /mesures - Créer une mesure d'humidité"""
        with patch('app.services.mesure_service.get_db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchrow.return_value = {
                "id": 2,
                "type_mesure_id": 2,
                "valeur": 55.0,
                "mesure_at": "2025-12-17T10:00:00"
            }
            mock_db.return_value.__aenter__.return_value = mock_conn
            
            response = client.post("/api/v1/mesures/", json={
                "type_mesure_id": 2,
                "valeur": 55.0
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_create_mesure_gas(self):
        """POST /mesures - Créer une mesure de gaz"""
        with patch('app.services.mesure_service.get_db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchrow.return_value = {
                "id": 3,
                "type_mesure_id": 3,
                "valeur": 25.0,
                "mesure_at": "2025-12-17T10:00:00"
            }
            mock_db.return_value.__aenter__.return_value = mock_conn
            
            response = client.post("/api/v1/mesures/", json={
                "type_mesure_id": 3,
                "valeur": 25.0
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


class TestWebhookMesure:
    """Tests pour le webhook de mesure MQTT"""
    
    def test_webhook_mesure_temperature(self):
        """POST /webhooks/mqtt/mesure - Température"""
        with patch('app.services.mesure_service.MesureService.create_mesure') as mock_create:
            with patch('app.services.mesure_service.MesureService.check_alerts') as mock_alerts:
                mock_create.return_value = {
                    "success": True,
                    "mesure": {"id": 1, "type_mesure_id": 1, "valeur": 22.5}
                }
                mock_alerts.return_value = {
                    "success": True,
                    "alerts": [],
                    "has_critical": False,
                    "has_warning": False
                }
                
                response = client.post("/api/v1/webhooks/mqtt/mesure", json={
                    "type_code": "TEMPERATURE",
                    "valeur": 22.5
                })
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "ok"
    
    def test_webhook_mesure_invalid_type(self):
        """POST /webhooks/mqtt/mesure - Type invalide"""
        response = client.post("/api/v1/webhooks/mqtt/mesure", json={
            "type_code": "INVALID",
            "valeur": 22.5
        })
        
        assert response.status_code == 400
    
    def test_webhook_mesure_gas_alert(self):
        """POST /webhooks/mqtt/mesure - Gaz avec alerte"""
        with patch('app.services.mesure_service.MesureService.create_mesure') as mock_create:
            with patch('app.services.mesure_service.MesureService.check_alerts') as mock_alerts:
                mock_create.return_value = {
                    "success": True,
                    "mesure": {"id": 1, "type_mesure_id": 3, "valeur": 600}
                }
                mock_alerts.return_value = {
                    "success": True,
                    "alerts": [{"type": "GAZ", "severity": "CRITICAL", "valeur": 600}],
                    "has_critical": True,
                    "has_warning": False
                }
                
                response = client.post("/api/v1/webhooks/mqtt/mesure", json={
                    "type_code": "GAZ",
                    "valeur": 600
                })
                
                assert response.status_code == 200
