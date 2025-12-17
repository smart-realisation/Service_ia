"""Unit tests for SafeLink chatbot"""
import pytest
from unittest.mock import AsyncMock, patch

from app.schemas.chatbot import (
    ChatbotQueryRequest, UserRole, ChatbotResponse
)
from app.services.chatbot_function_calling import ChatbotService
from app.utils.intent_classifier import IntentClassifier


class TestIntentClassifier:
    """Tests for regex-based intent classifier"""
    
    def test_classify_devices_intent(self):
        intent = IntentClassifier.classify("Montre-moi les appareils connectés")
        assert intent is not None
        assert intent.name == "get_connected_devices"
    
    def test_classify_alerts_intent(self):
        intent = IntentClassifier.classify("Y a-t-il des alertes critiques?")
        assert intent is not None
        assert intent.name == "get_security_alerts"
    
    def test_classify_sensor_intent(self):
        intent = IntentClassifier.classify("Quelle est la température?")
        assert intent is not None
        assert intent.name == "get_sensor_data"
        assert intent.entities.get("sensor_type") == "temperature"
    
    def test_extract_mac_address(self):
        text = "Détails du device AA:BB:CC:DD:EE:FF"
        mac = IntentClassifier.extract_device_id(text)
        assert mac == "AA:BB:CC:DD:EE:FF"
    
    def test_is_greeting(self):
        assert IntentClassifier.is_greeting("Bonjour!")
        assert IntentClassifier.is_greeting("Salut")
        assert not IntentClassifier.is_greeting("Montre les alertes")
    
    def test_is_help_request(self):
        assert IntentClassifier.is_help_request("Comment ça marche?")
        assert IntentClassifier.is_help_request("Aide-moi")
        assert not IntentClassifier.is_help_request("Alertes critiques")


class TestChatbotService:
    """Tests for chatbot service"""
    
    @pytest.fixture
    def service(self):
        return ChatbotService()
    
    @pytest.mark.asyncio
    async def test_get_security_tips(self, service):
        result = await service._get_security_tips("iot")
        assert result["success"] is True
        assert "tips" in result
        assert len(result["tips"]) > 0
    
    @pytest.mark.asyncio
    async def test_navigate_to(self, service):
        result = await service._navigate_to("dashboard")
        assert result["success"] is True
        assert result["navigation"]["path"] == "/dashboard"
    
    @pytest.mark.asyncio
    async def test_request_clarification(self, service):
        result = await service._request_clarification(
            "Requête ambiguë",
            ["Option 1", "Option 2"]
        )
        assert result["clarification_needed"] is True
        assert len(result["options"]) == 2


class TestSchemas:
    """Tests for Pydantic schemas"""
    
    def test_chatbot_query_request(self):
        request = ChatbotQueryRequest(
            message="Test message",
            user_id="user123",
            user_role=UserRole.HOME_USER
        )
        assert request.message == "Test message"
        assert request.user_role == UserRole.HOME_USER
    
    def test_chatbot_response(self):
        response = ChatbotResponse(
            message="Test response",
            suggestions=["Suggestion 1", "Suggestion 2"]
        )
        assert response.message == "Test response"
        assert len(response.suggestions) == 2
        assert response.requires_human is False


@pytest.mark.asyncio
async def test_execute_function_security_tips():
    """Test function execution"""
    service = ChatbotService()
    result = await service.execute_function(
        "get_security_tips",
        {"topic": "network"}
    )
    assert result["success"] is True
    assert "tips" in result


@pytest.mark.asyncio
async def test_execute_function_navigate():
    """Test navigation function"""
    service = ChatbotService()
    result = await service.execute_function(
        "navigate_to",
        {"page": "alerts"}
    )
    assert result["success"] is True
    assert result["navigation"]["path"] == "/alerts"
