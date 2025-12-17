# SafeLink AI - Chatbot Cybersécurité IoT

Chatbot IA intelligent pour la plateforme SafeLink de monitoring et cybersécurité IoT.

## Stack Technique

- **Backend**: FastAPI (Python 3.11+)
- **LLM**: Groq API (llama-3.3-70b-versatile)
- **Database**: PostgreSQL
- **Time-series**: InfluxDB
- **Cache/Sessions**: Redis
- **IoT Protocol**: MQTT (Mosquitto)

## Installation

```bash
# Cloner et configurer
cp .env.example .env
# Éditer .env avec votre clé Groq

# Lancer avec Docker
docker-compose up -d

# Ou en local
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API Endpoints

- `POST /api/v1/query` - Envoyer une requête au chatbot
- `GET /api/v1/health` - Vérifier l'état du système
- `GET /api/v1/suggestions` - Obtenir des suggestions par rôle

## Rôles Utilisateurs

- **ADMIN**: Accès complet
- **IT_MANAGER**: Responsable IT PME
- **HOME_USER**: Passionné domotique
- **FACILITY_MANAGER**: Gestionnaire établissement

## Exemple d'utilisation

```python
import httpx

response = httpx.post("http://localhost:8000/api/v1/query", json={
    "message": "Montre-moi les alertes critiques",
    "user_id": "user123",
    "user_role": "IT_MANAGER"
})
print(response.json())
```

## Tests

```bash
pytest tests/ -v
```
