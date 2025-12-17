-- SafeLink Database Schema

CREATE TABLE IF NOT EXISTS devices (
    id VARCHAR(50) PRIMARY KEY,
    mac_address VARCHAR(17) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    name VARCHAR(100),
    manufacturer VARCHAR(100),
    device_type VARCHAR(50),
    zone VARCHAR(50),
    status VARCHAR(20) DEFAULT 'online',
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    is_authorized BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR(50) PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    title VARCHAR(200) NOT NULL,
    description TEXT,
    device_id VARCHAR(50) REFERENCES devices(id),
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS anomalies (
    id VARCHAR(50) PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    device_id VARCHAR(50) REFERENCES devices(id),
    description TEXT,
    confidence FLOAT,
    detected_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS network_traffic (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) REFERENCES devices(id),
    destination VARCHAR(255),
    bytes_in BIGINT DEFAULT 0,
    bytes_out BIGINT DEFAULT 0,
    protocol VARCHAR(20),
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(30) DEFAULT 'HOME_USER',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_zone ON devices(zone);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_anomalies_type ON anomalies(type);
CREATE INDEX idx_traffic_device ON network_traffic(device_id);

-- Device Inventory for AI Classification
CREATE TABLE IF NOT EXISTS device_inventory (
    id SERIAL PRIMARY KEY,
    mac_address VARCHAR(17) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    hostname VARCHAR(255),
    device_type VARCHAR(50),
    vendor VARCHAR(100),
    risk_level VARCHAR(20) DEFAULT 'MEDIUM',
    confidence FLOAT DEFAULT 0.5,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    is_flagged BOOLEAN DEFAULT FALSE,
    notes TEXT
);

-- AI-generated alerts (separate from manual alerts)
CREATE TABLE IF NOT EXISTS ai_alerts (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50),
    sensor_id VARCHAR(50),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    anomaly_score FLOAT,
    details TEXT,
    is_acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    acknowledged_at TIMESTAMP,
    acknowledged_by VARCHAR(50)
);

-- Sensor readings history for ML training
CREATE TABLE IF NOT EXISTS sensor_readings (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50),
    sensor_id VARCHAR(50),
    temperature FLOAT,
    humidity FLOAT,
    gas_level FLOAT,
    motion BOOLEAN,
    light_level FLOAT,
    bytes_in BIGINT,
    bytes_out BIGINT,
    connection_count INT,
    unique_destinations INT,
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for AI tables
CREATE INDEX idx_device_inventory_risk ON device_inventory(risk_level);
CREATE INDEX idx_device_inventory_type ON device_inventory(device_type);
CREATE INDEX idx_ai_alerts_severity ON ai_alerts(severity);
CREATE INDEX idx_ai_alerts_created ON ai_alerts(created_at);
CREATE INDEX idx_sensor_readings_device ON sensor_readings(device_id);
CREATE INDEX idx_sensor_readings_time ON sensor_readings(recorded_at);
