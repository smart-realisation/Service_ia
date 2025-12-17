"""Anomaly Detection Model using Isolation Forest"""
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent / "trained"
MODEL_PATH.mkdir(exist_ok=True)


class AnomalyDetector:
    def __init__(self):
        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self.is_trained: bool = False
        self.feature_names = ["temperature", "humidity", "gas_level", "motion",
            "light_level", "bytes_in", "bytes_out", "connection_count",
            "unique_destinations", "hour_of_day"]
        self._load_or_create_model()
    
    def _load_or_create_model(self):
        model_file = MODEL_PATH / "anomaly_model.pkl"
        scaler_file = MODEL_PATH / "anomaly_scaler.pkl"
        if model_file.exists() and scaler_file.exists():
            try:
                with open(model_file, "rb") as f:
                    self.model = pickle.load(f)
                with open(scaler_file, "rb") as f:
                    self.scaler = pickle.load(f)
                self.is_trained = True
                logger.info("Loaded pre-trained anomaly detection model")
                return
            except Exception as e:
                logger.warning(f"Failed to load model: {e}")
        
        self.model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42, n_jobs=-1)
        self.scaler = StandardScaler()
        
        # Auto-train with synthetic data if no model exists
        self._auto_train_with_synthetic_data()
    
    def _auto_train_with_synthetic_data(self):
        """Generate synthetic normal data and train the model automatically"""
        import random
        from datetime import timedelta
        
        logger.info("No trained model found. Auto-training with synthetic data...")
        
        synthetic_data = []
        base_time = datetime.now() - timedelta(days=7)
        
        for i in range(300):  # 300 samples of normal behavior
            timestamp = base_time + timedelta(minutes=i * 30)
            hour = timestamp.hour
            
            # Normal temperature: 18-28°C
            temp_base = 22 + (2 if 10 <= hour <= 18 else -1)
            temperature = temp_base + random.gauss(0, 1.5)
            
            # Normal humidity: 40-60%
            humidity = 50 + random.gauss(0, 8)
            
            # Gas: normally very low
            gas_level = max(0, random.gauss(5, 3))
            
            # Motion: more frequent during day
            motion = random.random() < (0.3 if 8 <= hour <= 22 else 0.05)
            
            # Light follows day/night cycle
            light_level = random.gauss(600, 100) if 7 <= hour <= 19 else random.gauss(50, 30)
            
            # Normal network traffic
            synthetic_data.append({
                "temperature": max(10, min(35, temperature)),
                "humidity": max(20, min(80, humidity)),
                "gas_level": max(0, gas_level),
                "motion": motion,
                "light_level": max(0, light_level),
                "bytes_in": max(0, int(random.gauss(50000, 20000))),
                "bytes_out": max(0, int(random.gauss(10000, 5000))),
                "connection_count": max(0, int(random.gauss(5, 2))),
                "unique_destinations": max(1, int(random.gauss(3, 1)))
            })
        
        # Train on synthetic data
        X = np.vstack([self._extract_features(d) for d in synthetic_data])
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_trained = True
        
        # Save the model
        try:
            with open(MODEL_PATH / "anomaly_model.pkl", "wb") as f:
                pickle.dump(self.model, f)
            with open(MODEL_PATH / "anomaly_scaler.pkl", "wb") as f:
                pickle.dump(self.scaler, f)
            logger.info("Auto-trained model saved successfully")
        except Exception as e:
            logger.warning(f"Could not save auto-trained model: {e}")
        
        logger.info(f"Model auto-trained with {len(synthetic_data)} synthetic samples")
    
    def _extract_features(self, data: Dict[str, Any]) -> np.ndarray:
        features = [
            data.get("temperature", 25.0), data.get("humidity", 50.0),
            data.get("gas_level", 0.0), float(data.get("motion", False)),
            data.get("light_level", 500.0), data.get("bytes_in", 0),
            data.get("bytes_out", 0), data.get("connection_count", 0),
            data.get("unique_destinations", 0), datetime.now().hour
        ]
        return np.array(features).reshape(1, -1)
    
    def detect(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hybrid detection: Rules first (for known thresholds), then ML (for behavioral anomalies).
        This ensures critical thresholds are always caught regardless of ML prediction.
        """
        # STEP 1: Check rule-based thresholds FIRST (critical safety checks)
        rule_result = self._check_thresholds(data)
        if rule_result["is_anomaly"]:
            return rule_result
        
        # STEP 2: ML-based behavioral anomaly detection
        features = self._extract_features(data)
        try:
            if hasattr(self.scaler, 'mean_') and self.is_trained:
                features_scaled = self.scaler.transform(features)
                prediction = self.model.predict(features_scaled)[0]
                score = self.model.decision_function(features_scaled)[0]
                
                is_anomaly = prediction == -1
                if is_anomaly:
                    severity = "HIGH" if score < -0.5 else "MEDIUM" if score < -0.3 else "LOW"
                    return {
                        "is_anomaly": True,
                        "anomaly_score": float(score),
                        "alert_type": "BEHAVIORAL_ANOMALY",
                        "severity": severity,
                        "details": {"ml_score": float(score)},
                        "timestamp": datetime.now().isoformat(),
                        "device_id": data.get("device_id"),
                        "sensor_id": data.get("sensor_id")
                    }
                else:
                    return self._make_result(False, "NORMAL", "NONE", {"ml_score": float(score)}, data)
            else:
                return self._make_result(False, "NORMAL", "NONE", {}, data)
        except Exception as e:
            logger.warning(f"ML detection failed: {e}")
            return self._make_result(False, "NORMAL", "NONE", {}, data)
    
    def _check_thresholds(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check critical thresholds - these always trigger regardless of ML"""
        temp = data.get("temperature", 25)
        humidity = data.get("humidity", 50)
        gas = data.get("gas_level", 0)
        bytes_out = data.get("bytes_out", 0)
        connections = data.get("connection_count", 0)
        
        # Temperature thresholds (CELSIUS)
        if temp > 60 or temp < 0:
            return self._make_result(True, "TEMPERATURE_CRITICAL", "CRITICAL", {"temperature": temp, "unite": "CELSIUS"}, data)
        if temp > 45 or temp < 5:
            return self._make_result(True, "TEMPERATURE_WARNING", "HIGH", {"temperature": temp, "unite": "CELSIUS"}, data)
        
        # Humidity thresholds (POURCENT)
        if humidity > 90 or humidity < 10:
            return self._make_result(True, "HUMIDITY_CRITICAL", "CRITICAL", {"humidity": humidity, "unite": "POURCENT"}, data)
        if humidity > 80 or humidity < 20:
            return self._make_result(True, "HUMIDITY_WARNING", "HIGH", {"humidity": humidity, "unite": "POURCENT"}, data)
        
        # Gas leak thresholds (PPM)
        if gas > 500:
            return self._make_result(True, "GAS_LEAK_CRITICAL", "CRITICAL", {"gas_level": gas, "unite": "PPM"}, data)
        if gas > 100:
            return self._make_result(True, "GAS_LEAK_WARNING", "HIGH", {"gas_level": gas, "unite": "PPM"}, data)
        
        # Network anomalies
        if bytes_out > 10_000_000:
            return self._make_result(True, "DATA_EXFILTRATION", "HIGH", {"bytes_out": bytes_out}, data)
        if connections > 100:
            return self._make_result(True, "SUSPICIOUS_CONNECTIONS", "MEDIUM", {"connections": connections}, data)
        
        # No threshold violation
        return {"is_anomaly": False}
    
    
    def _make_result(self, is_anomaly, alert_type, severity, details, data):
        return {"is_anomaly": is_anomaly, "anomaly_score": -0.5 if is_anomaly else 0.5,
                "alert_type": alert_type, "severity": severity, "details": details,
                "timestamp": datetime.now().isoformat(), "device_id": data.get("device_id"), "sensor_id": data.get("sensor_id")}
    
    def train(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(training_data) < 10: return {"success": False, "error": "Need at least 10 samples"}
        X = np.vstack([self._extract_features(d) for d in training_data])
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        with open(MODEL_PATH / "anomaly_model.pkl", "wb") as f: pickle.dump(self.model, f)
        with open(MODEL_PATH / "anomaly_scaler.pkl", "wb") as f: pickle.dump(self.scaler, f)
        return {"success": True, "samples": len(training_data)}
    
    def batch_detect(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.detect(d) for d in data_list]


anomaly_detector = AnomalyDetector()
