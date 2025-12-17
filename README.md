# SafeLink AI - Chatbot Cybersécurité IoT

Service d'intelligence artificielle pour la plateforme SafeLink, offrant un chatbot conversationnel intelligent pour le monitoring, l'analyse et la cybersécurité des appareils IoT.

## Fonctionnalités

### Chatbot IA Conversationnel
- Interaction en langage naturel avec les utilisateurs
- Compréhension contextuelle des requêtes
- Suggestions personnalisées par rôle utilisateur
- Support multi-langues (français/anglais)

### Gestion des Mesures Capteurs
- **Température** (CELSIUS) - Mesure de la température ambiante
- **Humidité** (POURCENT) - Mesure de l'humidité relative
- **Gaz** (PPM) - Concentration de gaz

### Analyse et Monitoring IoT
- Détection d'anomalies en temps réel
- Classification automatique des appareils
- Alertes intelligentes basées sur les seuils
- Statistiques et tendances

## Architecture Base de Données

```sql
-- Types de mesure
CREATE TYPE type_mesure_enum AS ENUM ('TEMPERATURE','HUMIDITE','GAZ');
CREATE TYPE unite_mesure_enum AS ENUM ('CELSIUS','POURCENT','PPM');

-- Table des types
CREATE TABLE types_mesure (
    id          SERIAL PRIMARY KEY,
    code        type_mesure_enum NOT NULL UNIQUE,
    unite       unite_mesure_enum NOT NULL,
    description TEXT
);

-- Table des mesures
CREATE TABLE mesures (
    id              BIGSERIAL PRIMARY KEY,
    type_mesure_id  INT NOT NULL REFERENCES types_mesure(id),
    valeur          NUMERIC(10,3) NOT NULL,
    mesure_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## Installation

### Docker (Recommandé)

```bash
# Cloner et configurer
git clone https://github.com/smart-realisation/Service_ia.git
cd Service_ia
cp .env.example .env
# Éditer .env avec votre clé Groq API

# Lancer
docker-compose up -d
```

### Installation locale

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Base de données
psql -U postgres -f init.sql
psql -U postgres -d safelink -f seed_data.sql

# Lancer
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Mesures Capteurs

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/v1/mesures/types` | Types de mesure disponibles |
| GET | `/api/v1/mesures/` | Liste des mesures (filtrable) |
| GET | `/api/v1/mesures/latest` | Dernière mesure de chaque type |
| GET | `/api/v1/mesures/stats` | Statistiques par type |
| GET | `/api/v1/mesures/alerts` | Vérifier les alertes |
| GET | `/api/v1/mesures/thresholds` | Seuils d'alerte |
| POST | `/api/v1/mesures/` | Créer une mesure |

#### Créer une mesure
```bash
curl -X POST http://localhost:8000/api/v1/mesures/ \
  -H "Content-Type: application/json" \
  -d '{"type_mesure_id": 1, "valeur": 22.5}'
```

#### Récupérer les mesures
```bash
# Toutes les mesures des dernières 24h
curl "http://localhost:8000/api/v1/mesures/?period=24h"

# Mesures de température uniquement
curl "http://localhost:8000/api/v1/mesures/?type_code=TEMPERATURE"

# Dernières mesures
curl http://localhost:8000/api/v1/mesures/latest
```

### Webhook MQTT pour Mesures

```bash
# Envoyer une mesure via webhook
curl -X POST http://localhost:8000/api/v1/webhooks/mqtt/mesure \
  -H "Content-Type: application/json" \
  -d '{"type_code": "TEMPERATURE", "valeur": 23.5}'
```

### Chatbot

```bash
# Requête chatbot
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quelle est la température actuelle?",
    "user_id": "user123",
    "user_role": "HOME_USER"
  }'
```

### Analyse d'Anomalies

```bash
curl -X POST http://localhost:8000/api/v1/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 65,
    "humidity": 45,
    "gas_level": 5
  }'
```

## Seuils d'Alerte

| Type | Unité | Warning | Critical |
|------|-------|---------|----------|
| TEMPERATURE | CELSIUS | > 35°C ou < 5°C | > 45°C ou < 0°C |
| HUMIDITE | POURCENT | > 80% ou < 20% | > 90% ou < 10% |
| GAZ | PPM | > 100 PPM | > 500 PPM |

## Configuration (.env)

```bash
# Application
APP_NAME=SafeLink AI
ENVIRONMENT=development
DEBUG=true

# LLM Groq
GROQ_API_KEY=your-groq-api-key
LLM_MODEL=llama-3.3-70b-versatile

# Base de données
DATABASE_URL=postgresql://safelink:password@localhost:5432/safelink

# Redis
REDIS_URL=redis://localhost:6379

# MQTT
MQTT_BROKER=localhost
MQTT_PORT=1883
```

## Tests

```bash
# Tous les tests
pytest tests/ -v

# Tests des mesures
pytest tests/test_mesures.py -v

# Tests d'analyse
pytest tests/test_analysis.py -v
```

## Structure du Projet

```
safelink-ai/
├── app/
│   ├── core/                   # Configuration
│   ├── endpoints/              # Routes API
│   │   ├── mesures.py         # API mesures
│   │   ├── chatbot.py         # API chatbot
│   │   ├── analysis.py        # API analyse
│   │   └── webhooks.py        # Webhooks MQTT
│   ├── models/                 # Modèles ML
│   ├── schemas/                # Schémas Pydantic
│   │   └── mesure.py          # Schémas mesures
│   ├── services/               # Logique métier
│   │   └── mesure_service.py  # Service mesures
│   └── main.py
├── tests/
│   └── test_mesures.py
├── init.sql                    # Schéma BD
├── seed_data.sql              # Données test
└── requirements.txt
```

## Licence

Propriété de Smart Réalisation - Tous droits réservés
