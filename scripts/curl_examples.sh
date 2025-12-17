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
# MESURES (NOUVEAU SCHEMA)
# ==========================================
echo -e "\n\n📊 MESURES CAPTEURS"
echo "----------------------------------------"

echo -e "\n1. Types de mesure disponibles:"
curl -s "$BASE_URL/api/v1/mesures/types" | jq .

echo -e "\n2. Seuils d'alerte:"
curl -s "$BASE_URL/api/v1/mesures/thresholds" | jq .

echo -e "\n3. Créer mesure température (22.5°C):"
curl -s -X POST "$BASE_URL/api/v1/mesures/" \
  -H "Content-Type: application/json" \
  -d '{
    "type_mesure_id": 1,
    "valeur": 22.5
  }' | jq .

echo -e "\n4. Créer mesure humidité (55%):"
curl -s -X POST "$BASE_URL/api/v1/mesures/" \
  -H "Content-Type: application/json" \
  -d '{
    "type_mesure_id": 2,
    "valeur": 55.0
  }' | jq .

echo -e "\n5. Créer mesure gaz (25 PPM):"
curl -s -X POST "$BASE_URL/api/v1/mesures/" \
  -H "Content-Type: application/json" \
  -d '{
    "type_mesure_id": 3,
    "valeur": 25.0
  }' | jq .

echo -e "\n6. Dernières mesures:"
curl -s "$BASE_URL/api/v1/mesures/latest" | jq .

echo -e "\n7. Toutes les mesures (24h):"
curl -s "$BASE_URL/api/v1/mesures/?period=24h&limit=10" | jq .

echo -e "\n8. Mesures température uniquement:"
curl -s "$BASE_URL/api/v1/mesures/?type_code=TEMPERATURE&period=24h" | jq .

echo -e "\n9. Statistiques des mesures:"
curl -s "$BASE_URL/api/v1/mesures/stats?period=24h" | jq .

echo -e "\n10. Vérifier alertes:"
curl -s "$BASE_URL/api/v1/mesures/alerts" | jq .

# ==========================================
# WEBHOOK MESURES (MQTT)
# ==========================================
echo -e "\n\n🔗 WEBHOOK MESURES"
echo "----------------------------------------"

echo -e "\n1. Envoyer mesure température via webhook:"
curl -s -X POST "$BASE_URL/api/v1/webhooks/mqtt/mesure" \
  -H "Content-Type: application/json" \
  -d '{
    "type_code": "TEMPERATURE",
    "valeur": 23.5
  }' | jq .

echo -e "\n2. Envoyer mesure humidité via webhook:"
curl -s -X POST "$BASE_URL/api/v1/webhooks/mqtt/mesure" \
  -H "Content-Type: application/json" \
  -d '{
    "type_code": "HUMIDITE",
    "valeur": 48.0
  }' | jq .

echo -e "\n3. Envoyer mesure gaz (alerte) via webhook:"
curl -s -X POST "$BASE_URL/api/v1/webhooks/mqtt/mesure" \
  -H "Content-Type: application/json" \
  -d '{
    "type_code": "GAZ",
    "valeur": 150.0
  }' | jq .

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

echo -e "\n3. Détection fuite de gaz (600 PPM):"
curl -s -X POST "$BASE_URL/api/v1/analysis/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "esp32-003",
    "temperature": 22,
    "gas_level": 600
  }' | jq .

echo -e "\n4. Détection humidité critique (95%):"
curl -s -X POST "$BASE_URL/api/v1/analysis/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "esp32-004",
    "temperature": 22,
    "humidity": 95
  }' | jq .

echo -e "\n5. Seuils de détection:"
curl -s "$BASE_URL/api/v1/analysis/thresholds" | jq .

# ==========================================
# DEVICE CLASSIFICATION
# ==========================================
echo -e "\n\n📱 DEVICE CLASSIFICATION"
echo "----------------------------------------"

echo -e "\n1. Classifier ESP32:"
curl -s -X POST "$BASE_URL/api/v1/devices/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "24:0A:C4:AA:BB:CC",
    "hostname": "esp32-sensor"
  }' | jq .

echo -e "\n2. Niveaux de risque:"
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

echo -e "\n2. Query température:"
curl -s -X POST "$BASE_URL/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quelle est la température actuelle?",
    "user_id": "test-user",
    "user_role": "HOME_USER"
  }' | jq .

echo -e "\n3. Query mesures:"
curl -s -X POST "$BASE_URL/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Montre-moi les dernières mesures",
    "user_id": "test-user",
    "user_role": "HOME_USER"
  }' | jq .

echo -e "\n4. Query alertes:"
curl -s -X POST "$BASE_URL/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Y a-t-il des alertes sur les capteurs?",
    "user_id": "test-user",
    "user_role": "ADMIN"
  }' | jq .

echo -e "\n5. Get suggestions:"
curl -s "$BASE_URL/api/v1/suggestions?user_role=HOME_USER" | jq .

echo -e "\n=========================================="
echo "✅ Tests terminés!"
echo "=========================================="
