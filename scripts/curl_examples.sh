#!/bin/bash
# Exemples de requêtes curl pour tester SafeLink AI
# Usage: bash scripts/curl_examples.sh

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "🚀 SafeLink AI - Exemples curl"
echo "=========================================="

# ==========================================
# HEALTH CHECK
# ==========================================
echo -e "\n📍 Health Check"
curl -s "$BASE_URL/api/v1/health" | jq .

# ==========================================
# ANOMALY DETECTION
# ==========================================
echo -e "\n\n🔍 ANOMALY DETECTION"
echo "----------------------------------------"

echo -e "\n1. Analyse données normales:"
curl -s -X POST "$BASE_URL/api/v1/analysis/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "esp32-001",
    "temperature": 22.5,
    "humidity": 45,
    "gas_level": 5,
    "motion": false,
    "bytes_in": 50000,
    "bytes_out": 10000,
    "connection_count": 5,
    "unique_destinations": 3
  }' | jq .

echo -e "\n2. Détection température critique (65°C):"
curl -s -X POST "$BASE_URL/api/v1/analysis/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "esp32-002",
    "temperature": 65,
    "humidity": 45,
    "gas_level": 5
  }' | jq .

echo -e "\n3. Détection fuite de gaz (600 ppm):"
curl -s -X POST "$BASE_URL/api/v1/analysis/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "esp32-003",
    "temperature": 22,
    "gas_level": 600
  }' | jq .

echo -e "\n4. Détection exfiltration données (60MB):"
curl -s -X POST "$BASE_URL/api/v1/analysis/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "esp32-004",
    "temperature": 22,
    "bytes_out": 60000000
  }' | jq .

echo -e "\n5. Analyse batch:"
curl -s -X POST "$BASE_URL/api/v1/analysis/analyze/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"temperature": 22, "humidity": 50},
      {"temperature": 55, "humidity": 50},
      {"temperature": 22, "gas_level": 300}
    ]
  }' | jq .

# ==========================================
# DEVICE CLASSIFICATION
# ==========================================
echo -e "\n\n📱 DEVICE CLASSIFICATION"
echo "----------------------------------------"

echo -e "\n1. Classifier Raspberry Pi:"
curl -s -X POST "$BASE_URL/api/v1/devices/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "B8:27:EB:12:34:56",
    "ip_address": "192.168.1.100",
    "hostname": "raspberrypi"
  }' | jq .

echo -e "\n2. Classifier ESP32:"
curl -s -X POST "$BASE_URL/api/v1/devices/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "24:0A:C4:AA:BB:CC",
    "hostname": "esp32-sensor"
  }' | jq .

echo -e "\n3. Classifier appareil inconnu:"
curl -s -X POST "$BASE_URL/api/v1/devices/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "AA:BB:CC:DD:EE:FF"
  }' | jq .

echo -e "\n4. Classifier Amazon Echo:"
curl -s -X POST "$BASE_URL/api/v1/devices/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "68:A4:0E:11:22:33",
    "hostname": "echo-dot"
  }' | jq .

echo -e "\n5. Classification batch:"
curl -s -X POST "$BASE_URL/api/v1/devices/classify/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "devices": [
      {"mac_address": "B8:27:EB:11:11:11"},
      {"mac_address": "24:0A:C4:22:22:22"},
      {"mac_address": "AA:BB:CC:33:33:33", "hostname": "camera-front"}
    ]
  }' | jq .

echo -e "\n6. Niveaux de risque:"
curl -s "$BASE_URL/api/v1/devices/risk-levels" | jq .

# ==========================================
# CHATBOT
# ==========================================
echo -e "\n\n🤖 CHATBOT"
echo "----------------------------------------"

echo -e "\n1. Simple greeting:"
curl -s -X POST "$BASE_URL/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Bonjour",
    "user_id": "test-user",
    "user_role": "HOME_USER"
  }' | jq .

echo -e "\n2. Query devices:"
curl -s -X POST "$BASE_URL/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quels appareils sont connectés?",
    "user_id": "test-user",
    "user_role": "IT_MANAGER"
  }' | jq .

echo -e "\n3. Query alerts:"
curl -s -X POST "$BASE_URL/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Y a-t-il des alertes de sécurité?",
    "user_id": "test-user",
    "user_role": "ADMIN"
  }' | jq .

echo -e "\n4. Get suggestions:"
curl -s "$BASE_URL/api/v1/suggestions?user_role=IT_MANAGER" | jq .

# ==========================================
# WEBHOOKS
# ==========================================
echo -e "\n\n🔗 WEBHOOKS"
echo "----------------------------------------"

echo -e "\n1. Device event:"
curl -s -X POST "$BASE_URL/api/v1/webhooks/mqtt/device" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "safelink/devices/esp32-001",
    "payload": {"device_id": "esp32-001", "status": "online"},
    "timestamp": "2025-12-15T10:00:00Z"
  }' | jq .

echo -e "\n2. Alert event:"
curl -s -X POST "$BASE_URL/api/v1/webhooks/mqtt/alert" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "safelink/alerts",
    "payload": {"severity": "critical", "message": "Intrusion detected"},
    "timestamp": "2025-12-15T10:00:00Z"
  }' | jq .

echo -e "\n=========================================="
echo "✅ Tests terminés!"
echo "=========================================="
