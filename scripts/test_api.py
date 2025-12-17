"""
Script de test des APIs SafeLink AI

Usage:
    python scripts/test_api.py              # Teste toutes les APIs
    python scripts/test_api.py --chatbot    # Teste uniquement le chatbot
    python scripts/test_api.py --analysis   # Teste uniquement l'analyse
    python scripts/test_api.py --devices    # Teste uniquement la classification
"""
import argparse
import httpx
import json
from typing import Optional

BASE_URL = "http://localhost:8000"


def print_result(name: str, response: httpx.Response):
    """Affiche le résultat d'un test"""
    status = "✅" if response.status_code == 200 else "❌"
    print(f"\n{status} {name}")
    print(f"   Status: {response.status_code}")
    try:
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2, default=str)[:500]}")
    except:
        print(f"   Response: {response.text[:200]}")


def test_health():
    """Test health endpoint"""
    print("\n" + "="*50)
    print("🏥 TEST HEALTH CHECK")
    print("="*50)
    
    r = httpx.get(f"{BASE_URL}/")
    print_result("Root endpoint", r)
    
    r = httpx.get(f"{BASE_URL}/api/v1/health")
    print_result("Health check", r)


def test_chatbot():
    """Test chatbot endpoints"""
    print("\n" + "="*50)
    print("🤖 TEST CHATBOT")
    print("="*50)
    
    # Test simple greeting
    r = httpx.post(f"{BASE_URL}/api/v1/query", json={
        "message": "Bonjour",
        "user_id": "test-user",
        "user_role": "HOME_USER"
    }, timeout=30)
    print_result("Simple greeting", r)
    
    # Test device query
    r = httpx.post(f"{BASE_URL}/api/v1/query", json={
        "message": "Quels appareils sont connectés?",
        "user_id": "test-user",
        "user_role": "IT_MANAGER"
    }, timeout=30)
    print_result("Device query", r)
    
    # Test alert query
    r = httpx.post(f"{BASE_URL}/api/v1/query", json={
        "message": "Y a-t-il des alertes de sécurité?",
        "user_id": "test-user",
        "user_role": "ADMIN"
    }, timeout=30)
    print_result("Alert query", r)
    
    # Test suggestions
    r = httpx.get(f"{BASE_URL}/api/v1/suggestions?user_role=IT_MANAGER")
    print_result("Get suggestions", r)


def test_analysis():
    """Test anomaly detection endpoints"""
    print("\n" + "="*50)
    print("🔍 TEST ANOMALY DETECTION")
    print("="*50)
    
    # Test normal data
    r = httpx.post(f"{BASE_URL}/api/v1/analysis/analyze", json={
        "device_id": "esp32-001",
        "sensor_id": "temp-01",
        "temperature": 22.5,
        "humidity": 45.0,
        "gas_level": 5,
        "motion": False,
        "bytes_in": 50000,
        "bytes_out": 10000,
        "connection_count": 5,
        "unique_destinations": 3
    })
    print_result("Normal data analysis", r)
    
    # Test temperature anomaly
    r = httpx.post(f"{BASE_URL}/api/v1/analysis/analyze", json={
        "device_id": "esp32-002",
        "temperature": 65.0,  # CRITICAL
        "humidity": 45.0,
        "gas_level": 5,
        "motion": False,
        "bytes_in": 50000,
        "bytes_out": 10000,
        "connection_count": 5,
        "unique_destinations": 3
    })
    print_result("Temperature anomaly (65°C)", r)
    
    # Test gas leak
    r = httpx.post(f"{BASE_URL}/api/v1/analysis/analyze", json={
        "device_id": "esp32-003",
        "temperature": 22.0,
        "humidity": 45.0,
        "gas_level": 600,  # CRITICAL
        "motion": False,
        "bytes_in": 50000,
        "bytes_out": 10000,
        "connection_count": 5,
        "unique_destinations": 3
    })
    print_result("Gas leak (600 ppm)", r)
    
    # Test data exfiltration
    r = httpx.post(f"{BASE_URL}/api/v1/analysis/analyze", json={
        "device_id": "esp32-004",
        "temperature": 22.0,
        "humidity": 45.0,
        "gas_level": 5,
        "motion": False,
        "bytes_in": 50000,
        "bytes_out": 60000000,  # 60MB - suspicious
        "connection_count": 5,
        "unique_destinations": 3
    })
    print_result("Data exfiltration (60MB out)", r)
    
    # Test batch analysis
    r = httpx.post(f"{BASE_URL}/api/v1/analysis/analyze/batch", json={
        "data": [
            {"temperature": 22, "humidity": 50, "gas_level": 5},
            {"temperature": 55, "humidity": 50, "gas_level": 5},
            {"temperature": 22, "humidity": 50, "gas_level": 300}
        ]
    })
    print_result("Batch analysis (3 samples)", r)
    
    # Test thresholds
    r = httpx.get(f"{BASE_URL}/api/v1/analysis/thresholds")
    print_result("Get thresholds", r)


def test_devices():
    """Test device classification endpoints"""
    print("\n" + "="*50)
    print("📱 TEST DEVICE CLASSIFICATION")
    print("="*50)
    
    # Test Raspberry Pi (known OUI)
    r = httpx.post(f"{BASE_URL}/api/v1/devices/classify", json={
        "mac_address": "B8:27:EB:12:34:56",
        "ip_address": "192.168.1.100",
        "hostname": "raspberrypi"
    })
    print_result("Raspberry Pi classification", r)
    
    # Test ESP32 (Espressif)
    r = httpx.post(f"{BASE_URL}/api/v1/devices/classify", json={
        "mac_address": "24:0A:C4:AA:BB:CC",
        "ip_address": "192.168.1.101",
        "hostname": "esp32-sensor"
    })
    print_result("ESP32 classification", r)
    
    # Test unknown device
    r = httpx.post(f"{BASE_URL}/api/v1/devices/classify", json={
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "ip_address": "192.168.1.102"
    })
    print_result("Unknown device classification", r)
    
    # Test smart speaker (Amazon Echo)
    r = httpx.post(f"{BASE_URL}/api/v1/devices/classify", json={
        "mac_address": "68:A4:0E:11:22:33",
        "hostname": "echo-dot"
    })
    print_result("Amazon Echo classification", r)
    
    # Test by hostname pattern
    r = httpx.post(f"{BASE_URL}/api/v1/devices/classify", json={
        "mac_address": "11:22:33:44:55:66",
        "hostname": "android-phone-john"
    })
    print_result("Android phone (by hostname)", r)
    
    # Test batch classification
    r = httpx.post(f"{BASE_URL}/api/v1/devices/classify/batch", json={
        "devices": [
            {"mac_address": "B8:27:EB:11:11:11"},
            {"mac_address": "24:0A:C4:22:22:22"},
            {"mac_address": "AA:BB:CC:33:33:33", "hostname": "camera-front"}
        ]
    })
    print_result("Batch classification (3 devices)", r)
    
    # Test risk levels
    r = httpx.get(f"{BASE_URL}/api/v1/devices/risk-levels")
    print_result("Get risk levels", r)
    
    # Test known vendors
    r = httpx.get(f"{BASE_URL}/api/v1/devices/known-vendors")
    print_result("Get known vendors", r)


def test_webhooks():
    """Test webhook endpoints"""
    print("\n" + "="*50)
    print("🔗 TEST WEBHOOKS")
    print("="*50)
    
    # Device event
    r = httpx.post(f"{BASE_URL}/api/v1/webhooks/mqtt/device", json={
        "topic": "safelink/devices/esp32-001",
        "payload": {"device_id": "esp32-001", "status": "online"},
        "timestamp": "2025-12-15T10:00:00Z"
    })
    print_result("Device webhook", r)
    
    # Alert event
    r = httpx.post(f"{BASE_URL}/api/v1/webhooks/mqtt/alert", json={
        "topic": "safelink/alerts",
        "payload": {"severity": "critical", "message": "Intrusion detected"},
        "timestamp": "2025-12-15T10:00:00Z"
    })
    print_result("Alert webhook", r)
    
    # Sensor event
    r = httpx.post(f"{BASE_URL}/api/v1/webhooks/mqtt/sensor", json={
        "topic": "safelink/sensors/temp",
        "payload": {"sensor_id": "temp-01", "value": 22.5},
        "timestamp": "2025-12-15T10:00:00Z"
    })
    print_result("Sensor webhook", r)


def main():
    parser = argparse.ArgumentParser(description="Test SafeLink AI APIs")
    parser.add_argument("--chatbot", action="store_true", help="Test chatbot only")
    parser.add_argument("--analysis", action="store_true", help="Test analysis only")
    parser.add_argument("--devices", action="store_true", help="Test devices only")
    parser.add_argument("--webhooks", action="store_true", help="Test webhooks only")
    parser.add_argument("--url", type=str, default="http://localhost:8000", help="Base URL")
    
    args = parser.parse_args()
    
    global BASE_URL
    BASE_URL = args.url
    
    print(f"🚀 Testing SafeLink AI at {BASE_URL}")
    
    # Check if server is running
    try:
        httpx.get(f"{BASE_URL}/", timeout=5)
    except httpx.ConnectError:
        print(f"❌ Cannot connect to {BASE_URL}")
        print("   Start the server with: uvicorn app.main:app --reload")
        return
    
    if args.chatbot:
        test_chatbot()
    elif args.analysis:
        test_analysis()
    elif args.devices:
        test_devices()
    elif args.webhooks:
        test_webhooks()
    else:
        # Test all
        test_health()
        test_analysis()
        test_devices()
        test_webhooks()
        test_chatbot()
    
    print("\n" + "="*50)
    print("✅ Tests terminés!")
    print("="*50)


if __name__ == "__main__":
    main()
