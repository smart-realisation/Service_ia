# SafeLink AI - Chatbot Cybersécurité IoT

Service d'intelligence artificielle pour la plateforme SafeLink, offrant un chatbot conversationnel intelligent pour le monitoring, l'analyse et la cybersécurité des appareils IoT.

## Table des matières

- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Stack Technique](#stack-technique)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Rôles Utilisateurs](#rôles-utilisateurs)
- [Modèles ML](#modèles-ml)
- [Scripts Utilitaires](#scripts-utilitaires)
- [Tests](#tests)
- [Structure du Projet](#structure-du-projet)
- [Déploiement](#déploiement)

## Fonctionnalités

### Chatbot IA Conversationnel
- Interaction en langage naturel avec les utilisateurs
- Compréhension contextuelle des requêtes
- Suggestions personnalisées par rôle utilisateur
- Support multi-langues (français/anglais)
- Streaming SSE pour réponses en temps réel

### Analyse et Monitoring IoT
- Détection d'anomalies en temps réel
- Classification automatique des appareils
- Analyse des tendances de consommation
- Surveillance des métriques de sécurité
- Alertes intelligentes et recommandations

### Intégrations
- Webhooks pour événements temps réel
- MQTT pour communication IoT
- API RESTful complète
- Interface web de test intégrée

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Client    │─────▶│  FastAPI     │─────▶│  Groq LLM   │
│   (Web/App) │      │  Backend     │      │  (llama-3.3)│
└─────────────┘      └──────────────┘      └─────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────▼────┐       ┌─────▼─────┐      ┌─────▼─────┐
   │PostgreSQL│       │   Redis   │      │ InfluxDB  │
   │ (Données)│       │  (Cache)  │      │(TimeSeries)│
   └──────────┘       └───────────┘      └───────────┘
        │
   ┌────▼────┐
   │  MQTT   │◀─── Appareils IoT
   │Mosquitto│
   └─────────┘
```

## Stack Technique

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Server**: Uvicorn avec support asynchrone
- **Validation**: Pydantic v2

### Intelligence Artificielle
- **LLM**: Groq API avec llama-3.3-70b-versatile
- **ML**: scikit-learn, XGBoost
- **Détection d'anomalies**: Isolation Forest, DBSCAN
- **Classification**: Random Forest, XGBoost

### Bases de données
- **PostgreSQL**: Données relationnelles (appareils, utilisateurs, alertes)
- **InfluxDB**: Séries temporelles (métriques IoT)
- **Redis**: Cache et sessions

### IoT & Messaging
- **MQTT**: Mosquitto pour la communication IoT
- **Protocole**: MQTT v5 avec QoS

### DevOps
- **Containerisation**: Docker, Docker Compose
- **Tests**: Pytest, pytest-asyncio
- **Monitoring**: Logging structuré, Health checks

## Prérequis

- Python 3.11 ou supérieur
- Docker et Docker Compose (recommandé)
- PostgreSQL 15+ (si installation locale)
- Redis 7+ (si installation locale)
- Compte Groq API avec clé d'accès

## Installation

### Option 1: Docker (Recommandé)

```bash
# Cloner le repository
git clone https://github.com/smart-realisation/Service_ia.git
cd Service_ia

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec votre clé Groq API

# Lancer tous les services
docker-compose up -d

# Vérifier les logs
docker-compose logs -f app
```

L'application sera accessible sur `http://localhost:8000`

### Option 2: Installation locale

```bash
# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer la base de données
psql -U postgres -f init.sql
psql -U postgres -d safelink -f seed_data.sql

# Lancer l'application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration

### Variables d'environnement (.env)

```bash
# Application
APP_NAME=SafeLink AI
ENVIRONMENT=development
DEBUG=true

# LLM Groq
GROQ_API_KEY=your-groq-api-key-here
LLM_MODEL=llama-3.3-70b-versatile
LLM_ENABLED=true

# Base de données
DATABASE_URL=postgresql://safelink:password@localhost:5432/safelink

# Redis
REDIS_URL=redis://localhost:6379

# MQTT
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USER=safelink
MQTT_PASSWORD=password

# Rate Limiting
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW=60
```

### Obtenir une clé API Groq

1. Créer un compte sur [console.groq.com](https://console.groq.com)
2. Générer une nouvelle clé API
3. Copier la clé dans `.env` → `GROQ_API_KEY`

## API Endpoints

### Chatbot

#### `POST /api/v1/query`
Envoyer une requête au chatbot

**Request:**
```json
{
  "message": "Montre-moi les alertes critiques",
  "user_id": "user123",
  "user_role": "IT_MANAGER",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "response": "Voici les 3 alertes critiques actives...",
  "session_id": "abc123",
  "timestamp": "2024-12-17T10:30:00Z"
}
```

#### `GET /api/v1/query/stream`
Stream SSE pour réponses en temps réel

**Query params:**
- `message`: Le message utilisateur
- `user_id`: ID de l'utilisateur
- `user_role`: Rôle (ADMIN, IT_MANAGER, etc.)

#### `GET /api/v1/suggestions`
Obtenir des suggestions contextuelles

**Query params:**
- `user_role`: Rôle de l'utilisateur

**Response:**
```json
{
  "suggestions": [
    "Afficher les alertes critiques",
    "Analyser la consommation énergétique",
    "Vérifier les appareils déconnectés"
  ]
}
```

#### `DELETE /api/v1/sessions/{session_id}`
Supprimer une session de conversation

### Webhooks

#### `POST /api/v1/webhooks/alert`
Recevoir des alertes depuis la plateforme principale

#### `POST /api/v1/webhooks/device-status`
Notification de changement d'état d'appareil

#### `POST /api/v1/webhooks/anomaly`
Notification de détection d'anomalie

### Analyse

#### `POST /api/v1/analysis/anomaly`
Détecter des anomalies dans les données de capteurs

**Request:**
```json
{
  "device_id": "device123",
  "metrics": {
    "temperature": 25.5,
    "humidity": 60,
    "power_consumption": 150
  }
}
```

#### `GET /api/v1/analysis/trends`
Obtenir les tendances de consommation

**Query params:**
- `device_id`: ID de l'appareil (optionnel)
- `days`: Nombre de jours (défaut: 7)

### Appareils

#### `GET /api/v1/devices`
Lister tous les appareils

#### `GET /api/v1/devices/{device_id}`
Détails d'un appareil

#### `POST /api/v1/devices/classify`
Classifier automatiquement un appareil

### Health & Monitoring

#### `GET /api/v1/health`
Vérifier l'état du système

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "llm": "available",
  "mqtt": "connected",
  "timestamp": "2024-12-17T10:30:00Z"
}
```

#### `GET /`
Page d'accueil avec informations API

#### `GET /chatbot`
Interface de test du chatbot

#### `GET /docs`
Documentation Swagger interactive

#### `GET /redoc`
Documentation ReDoc

## Rôles Utilisateurs

Le chatbot adapte ses réponses selon le rôle :

### ADMIN
- Accès complet à toutes les fonctionnalités
- Gestion des utilisateurs et permissions
- Configuration système
- Analyses avancées

### IT_MANAGER
- Responsable IT de PME
- Monitoring de l'infrastructure
- Gestion des alertes de sécurité
- Rapports et statistiques

### HOME_USER
- Passionné de domotique
- Gestion de maison connectée
- Automatisations simples
- Consommation énergétique

### FACILITY_MANAGER
- Gestionnaire d'établissement
- Surveillance des équipements
- Optimisation énergétique
- Maintenance préventive

## Modèles ML

### Détection d'anomalies
Localisation: `app/models/anomaly_detector.py`

**Algorithmes:**
- Isolation Forest pour détection d'outliers
- DBSCAN pour clustering
- Z-score normalisé

**Entraînement:**
```bash
python scripts/train_models.py
```

Modèles entraînés sauvegardés dans `app/models/trained/`

### Classification d'appareils
Localisation: `app/models/device_classifier.py`

**Features:**
- Pattern de consommation
- Fréquence d'utilisation
- Caractéristiques réseau
- Métriques temporelles

## Scripts Utilitaires

### `scripts/train_models.py`
Entraîner les modèles ML d'anomalie et classification

```bash
python scripts/train_models.py
```

### `scripts/test_api.py`
Tester les endpoints de l'API

```bash
python scripts/test_api.py
```

### `scripts/curl_examples.sh`
Exemples d'appels API avec curl

```bash
bash scripts/curl_examples.sh
```

## Tests

### Lancer tous les tests

```bash
pytest tests/ -v
```

### Tests par catégorie

```bash
# Tests du chatbot
pytest tests/test_chatbot.py -v

# Tests d'analyse
pytest tests/test_analysis.py -v

# Tests des appareils
pytest tests/test_devices.py -v

# Tests des webhooks
pytest tests/test_webhooks.py -v

# Tests d'intégration
pytest tests/test_integration.py -v
```

### Couverture de code

```bash
pytest --cov=app --cov-report=html
```

## Structure du Projet

```
safelink-ai/
├── app/
│   ├── core/                   # Configuration et services core
│   │   ├── config.py          # Settings Pydantic
│   │   ├── database.py        # Connexion PostgreSQL
│   │   └── mqtt_client.py     # Client MQTT
│   ├── endpoints/             # Routes API
│   │   ├── chatbot.py         # Endpoints chatbot
│   │   ├── webhooks.py        # Webhooks externes
│   │   ├── analysis.py        # Analyse et ML
│   │   └── devices.py         # Gestion appareils
│   ├── models/                # Modèles ML
│   │   ├── anomaly_detector.py
│   │   ├── device_classifier.py
│   │   └── trained/           # Modèles entraînés (.pkl)
│   ├── schemas/               # Schémas Pydantic
│   │   └── chatbot.py
│   ├── services/              # Logique métier
│   │   ├── llm_service.py            # Intégration Groq
│   │   ├── chatbot_function_calling.py
│   │   ├── prompt_builder.py
│   │   ├── anomaly_service.py
│   │   ├── classification_service.py
│   │   ├── device_service.py
│   │   ├── sensor_service.py
│   │   └── alert_service.py
│   ├── utils/                 # Utilitaires
│   │   └── intent_classifier.py
│   ├── static/                # Interface web
│   │   ├── chatbot.html
│   │   └── index.html
│   └── main.py                # Point d'entrée FastAPI
├── scripts/                   # Scripts utilitaires
│   ├── train_models.py
│   ├── test_api.py
│   ├── curl_examples.sh
│   └── training_data.json
├── tests/                     # Tests unitaires/intégration
│   ├── test_chatbot.py
│   ├── test_analysis.py
│   ├── test_devices.py
│   ├── test_webhooks.py
│   └── test_integration.py
├── static/                    # Assets statiques
├── docker-compose.yml         # Orchestration Docker
├── Dockerfile                 # Image Docker app
├── init.sql                   # Schéma base de données
├── seed_data.sql             # Données de test
├── requirements.txt          # Dépendances Python
├── pytest.ini               # Configuration pytest
├── .env.example             # Template variables d'env
└── README.md                # Cette documentation
```

## Déploiement

### Docker Production

```bash
# Build l'image
docker build -t safelink-ai:latest .

# Lancer avec docker-compose
docker-compose -f docker-compose.yml up -d

# Scaler l'application
docker-compose up -d --scale app=3
```

### Variables d'environnement Production

```bash
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@prod-db:5432/safelink
REDIS_URL=redis://prod-redis:6379
# Configurer CORS pour votre domaine
```

### Health Checks

L'application expose un endpoint de santé pour les orchestrateurs:

```bash
curl http://localhost:8000/api/v1/health
```

## Exemple d'utilisation

### Python

```python
import httpx

# Requête simple
response = httpx.post("http://localhost:8000/api/v1/query", json={
    "message": "Quels appareils consomment le plus d'énergie ?",
    "user_id": "user123",
    "user_role": "IT_MANAGER"
})
print(response.json()["response"])

# Streaming SSE
import sseclient

response = httpx.get(
    "http://localhost:8000/api/v1/query/stream",
    params={
        "message": "Analyse les anomalies de cette semaine",
        "user_id": "user123",
        "user_role": "ADMIN"
    },
    timeout=30.0
)

client = sseclient.SSEClient(response)
for event in client.events():
    print(event.data, end="", flush=True)
```

### cURL

```bash
# Requête chatbot
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Affiche les alertes critiques",
    "user_id": "user123",
    "user_role": "IT_MANAGER"
  }'

# Health check
curl http://localhost:8000/api/v1/health

# Suggestions
curl "http://localhost:8000/api/v1/suggestions?user_role=IT_MANAGER"
```

## Support et Contribution

Pour toute question ou contribution :
- Issues: [GitHub Issues](https://github.com/smart-realisation/Service_ia/issues)
- Documentation: `/docs` endpoint
- Contact: smart-realisation team

## Licence

Propriété de Smart Réalisation - Tous droits réservés
