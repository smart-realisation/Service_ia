"""
Script d'entraînement des modèles SafeLink AI

Usage:
    python scripts/train_models.py --generate    # Génère des données simulées et entraîne
    python scripts/train_models.py --file data.json  # Entraîne avec un fichier de données
    python scripts/train_models.py --db          # Entraîne avec les données de la DB
"""
import argparse
import json
import random
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.anomaly_detector import anomaly_detector


def generate_normal_data(n_samples: int = 500) -> list:
    """Génère des données de comportement NORMAL pour l'entraînement"""
    data = []
    base_time = datetime.now() - timedelta(days=7)
    
    for i in range(n_samples):
        timestamp = base_time + timedelta(minutes=i * 15)
        hour = timestamp.hour
        
        # Température normale: 18-28°C, légèrement plus chaude en journée
        temp_base = 22 + (2 if 10 <= hour <= 18 else -1)
        temperature = temp_base + random.gauss(0, 1.5)
        
        # Humidité normale: 40-60%
        humidity = 50 + random.gauss(0, 8)
        
        # Gaz: normalement très bas
        gas_level = max(0, random.gauss(5, 3))
        
        # Mouvement: plus fréquent en journée
        motion_prob = 0.3 if 8 <= hour <= 22 else 0.05
        motion = random.random() < motion_prob
        
        # Lumière: suit le cycle jour/nuit
        if 7 <= hour <= 19:
            light_level = random.gauss(600, 100)
        else:
            light_level = random.gauss(50, 30)
        
        # Trafic réseau normal
        bytes_in = int(random.gauss(50000, 20000))
        bytes_out = int(random.gauss(10000, 5000))
        connection_count = int(random.gauss(5, 2))
        unique_destinations = int(random.gauss(3, 1))
        
        data.append({
            "device_id": f"esp32-{random.randint(1, 5):03d}",
            "sensor_id": f"sensor-{random.randint(1, 10):02d}",
            "timestamp": timestamp.isoformat(),
            "temperature": max(10, min(35, temperature)),
            "humidity": max(20, min(80, humidity)),
            "gas_level": max(0, gas_level),
            "motion": motion,
            "light_level": max(0, light_level),
            "bytes_in": max(0, bytes_in),
            "bytes_out": max(0, bytes_out),
            "connection_count": max(0, connection_count),
            "unique_destinations": max(1, unique_destinations)
        })
    
    return data


def generate_anomaly_data(n_samples: int = 50) -> list:
    """Génère des données ANORMALES pour tester la détection"""
    anomalies = []
    
    # Température critique
    for _ in range(n_samples // 5):
        anomalies.append({
            "device_id": "esp32-001",
            "temperature": random.choice([random.gauss(55, 5), random.gauss(-5, 3)]),
            "humidity": 50,
            "gas_level": 5,
            "motion": False,
            "light_level": 500,
            "bytes_in": 50000,
            "bytes_out": 10000,
            "connection_count": 5,
            "unique_destinations": 3,
            "expected_alert": "TEMPERATURE"
        })
    
    # Fuite de gaz
    for _ in range(n_samples // 5):
        anomalies.append({
            "device_id": "esp32-002",
            "temperature": 22,
            "humidity": 50,
            "gas_level": random.gauss(300, 100),
            "motion": False,
            "light_level": 500,
            "bytes_in": 50000,
            "bytes_out": 10000,
            "connection_count": 5,
            "unique_destinations": 3,
            "expected_alert": "GAS_LEAK"
        })
    
    # Exfiltration de données
    for _ in range(n_samples // 5):
        anomalies.append({
            "device_id": "esp32-003",
            "temperature": 22,
            "humidity": 50,
            "gas_level": 5,
            "motion": False,
            "light_level": 500,
            "bytes_in": 50000,
            "bytes_out": random.randint(20_000_000, 100_000_000),
            "connection_count": 5,
            "unique_destinations": 3,
            "expected_alert": "DATA_EXFILTRATION"
        })
    
    # Connexions suspectes
    for _ in range(n_samples // 5):
        anomalies.append({
            "device_id": "esp32-004",
            "temperature": 22,
            "humidity": 50,
            "gas_level": 5,
            "motion": False,
            "light_level": 500,
            "bytes_in": 50000,
            "bytes_out": 10000,
            "connection_count": random.randint(150, 500),
            "unique_destinations": random.randint(50, 200),
            "expected_alert": "SUSPICIOUS_CONNECTIONS"
        })
    
    # Comportement anormal général
    for _ in range(n_samples // 5):
        anomalies.append({
            "device_id": "esp32-005",
            "temperature": random.gauss(22, 15),
            "humidity": random.gauss(50, 30),
            "gas_level": random.gauss(50, 30),
            "motion": True,
            "light_level": random.gauss(500, 300),
            "bytes_in": random.randint(500000, 2000000),
            "bytes_out": random.randint(100000, 500000),
            "connection_count": random.randint(20, 50),
            "unique_destinations": random.randint(10, 30),
            "expected_alert": "BEHAVIORAL"
        })
    
    return anomalies


def train_with_data(data: list):
    """Entraîne le modèle avec les données fournies"""
    print(f"📊 Entraînement avec {len(data)} échantillons...")
    
    result = anomaly_detector.train(data)
    
    if result.get("success"):
        print(f"✅ Modèle entraîné avec succès!")
        print(f"   Échantillons utilisés: {result.get('samples')}")
        print(f"   Modèle sauvegardé dans: app/models/trained/")
    else:
        print(f"❌ Erreur: {result.get('error')}")


def test_detection(anomalies: list):
    """Teste la détection sur des anomalies connues"""
    print(f"\n🔍 Test de détection sur {len(anomalies)} anomalies...")
    
    detected = 0
    results_by_type = {}
    
    for anomaly in anomalies:
        expected = anomaly.pop("expected_alert", "UNKNOWN")
        result = anomaly_detector.detect(anomaly)
        
        if result["is_anomaly"]:
            detected += 1
        
        if expected not in results_by_type:
            results_by_type[expected] = {"total": 0, "detected": 0}
        results_by_type[expected]["total"] += 1
        if result["is_anomaly"]:
            results_by_type[expected]["detected"] += 1
    
    print(f"\n📈 Résultats:")
    print(f"   Taux de détection global: {detected}/{len(anomalies)} ({100*detected/len(anomalies):.1f}%)")
    print(f"\n   Par type d'anomalie:")
    for alert_type, stats in results_by_type.items():
        rate = 100 * stats["detected"] / stats["total"]
        print(f"   - {alert_type}: {stats['detected']}/{stats['total']} ({rate:.0f}%)")


def main():
    parser = argparse.ArgumentParser(description="Entraînement des modèles SafeLink AI")
    parser.add_argument("--generate", action="store_true", help="Génère des données simulées")
    parser.add_argument("--file", type=str, help="Fichier JSON avec les données d'entraînement")
    parser.add_argument("--test", action="store_true", help="Teste la détection après entraînement")
    parser.add_argument("--samples", type=int, default=500, help="Nombre d'échantillons à générer")
    
    args = parser.parse_args()
    
    if args.file:
        print(f"📂 Chargement des données depuis {args.file}...")
        with open(args.file, "r") as f:
            data = json.load(f)
        train_with_data(data)
    
    elif args.generate:
        print("🎲 Génération de données simulées...")
        normal_data = generate_normal_data(args.samples)
        
        # Sauvegarde pour référence
        output_file = Path("scripts/training_data.json")
        with open(output_file, "w") as f:
            json.dump(normal_data, f, indent=2)
        print(f"   Données sauvegardées dans {output_file}")
        
        train_with_data(normal_data)
        
        if args.test:
            anomaly_data = generate_anomaly_data(50)
            test_detection(anomaly_data)
    
    else:
        parser.print_help()
        print("\n💡 Exemple:")
        print("   python scripts/train_models.py --generate --test")


if __name__ == "__main__":
    main()
