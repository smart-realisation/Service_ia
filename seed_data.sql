-- SafeLink Test Data
-- Exécuter avec: psql -U postgres -d safelink -f seed_data.sql

-- Devices IoT
INSERT INTO devices (id, mac_address, ip_address, name, manufacturer, device_type, zone, status, is_authorized) VALUES
('DEV-001', 'AA:BB:CC:DD:EE:01', '192.168.1.101', 'Caméra Entrée', 'Hikvision', 'camera', 'VLAN_CAMERAS', 'online', true),
('DEV-002', 'AA:BB:CC:DD:EE:02', '192.168.1.102', 'Caméra Jardin', 'Dahua', 'camera', 'VLAN_CAMERAS', 'online', true),
('DEV-003', 'AA:BB:CC:DD:EE:03', '192.168.1.103', 'Thermostat Salon', 'Nest', 'thermostat', 'VLAN_IOT', 'online', true),
('DEV-004', 'AA:BB:CC:DD:EE:04', '192.168.1.104', 'Capteur Température Cave', 'ESP32-DHT22', 'sensor', 'VLAN_IOT', 'online', true),
('DEV-005', 'AA:BB:CC:DD:EE:05', '192.168.1.105', 'Détecteur Fumée Cuisine', 'ESP32-MQ2', 'sensor', 'VLAN_IOT', 'online', true),
('DEV-006', 'AA:BB:CC:DD:EE:06', '192.168.1.106', 'Assistant Vocal', 'Amazon Echo', 'assistant', 'VLAN_IOT', 'online', true),
('DEV-007', 'AA:BB:CC:DD:EE:07', '192.168.1.107', 'Ampoule Connectée', 'Philips Hue', 'light', 'VLAN_IOT', 'offline', true),
('DEV-008', 'AA:BB:CC:DD:EE:08', '192.168.1.108', 'Serrure Connectée', 'Nuki', 'lock', 'VLAN_IOT', 'online', true),
('DEV-009', 'AA:BB:CC:DD:EE:09', '192.168.1.199', 'Device Inconnu', 'Unknown', 'unknown', 'VLAN_IOT', 'suspicious', false),
('DEV-010', 'AA:BB:CC:DD:EE:10', '192.168.1.110', 'Capteur Mouvement Hall', 'ESP32-PIR', 'sensor', 'VLAN_IOT', 'online', true);

-- Alertes de sécurité
INSERT INTO alerts (id, type, severity, status, title, description, device_id, created_at) VALUES
('ALR-001', 'intrusion', 'critical', 'active', 'Tentative de connexion suspecte', 'Multiple tentatives de connexion échouées depuis IP externe 185.234.xx.xx sur la caméra entrée', 'DEV-001', NOW() - INTERVAL '2 hours'),
('ALR-002', 'anomaly', 'warning', 'active', 'Trafic réseau inhabituel', 'Le thermostat envoie des données vers un serveur chinois inconnu', 'DEV-003', NOW() - INTERVAL '5 hours'),
('ALR-003', 'gas', 'critical', 'resolved', 'Détection de fumée', 'Capteur MQ2 a détecté de la fumée dans la cuisine - Fausse alerte (cuisson)', 'DEV-005', NOW() - INTERVAL '1 day'),
('ALR-004', 'new_device', 'warning', 'active', 'Nouvel appareil détecté', 'Un appareil non autorisé a rejoint le réseau VLAN_IOT', 'DEV-009', NOW() - INTERVAL '30 minutes'),
('ALR-005', 'offline', 'info', 'active', 'Appareil hors ligne', 'Ampoule Philips Hue ne répond plus depuis 3 heures', 'DEV-007', NOW() - INTERVAL '3 hours'),
('ALR-006', 'motion', 'warning', 'active', 'Mouvement détecté', 'Mouvement dans le hall à 03:45 - Heure inhabituelle', 'DEV-010', NOW() - INTERVAL '6 hours'),
('ALR-007', 'temperature', 'warning', 'active', 'Température anormale', 'Température cave: 28°C (seuil: 20°C)', 'DEV-004', NOW() - INTERVAL '1 hour');

-- Anomalies détectées
INSERT INTO anomalies (id, type, device_id, description, confidence, detected_at) VALUES
('ANO-001', 'network', 'DEV-003', 'Connexion sortante vers IP chinoise non répertoriée', 0.85, NOW() - INTERVAL '5 hours'),
('ANO-002', 'network', 'DEV-006', 'Volume de données envoyées 3x supérieur à la normale', 0.72, NOW() - INTERVAL '12 hours'),
('ANO-003', 'physical', 'DEV-010', 'Mouvement détecté pendant période absence programmée', 0.91, NOW() - INTERVAL '6 hours'),
('ANO-004', 'environmental', 'DEV-004', 'Hausse température rapide (+8°C en 1h)', 0.88, NOW() - INTERVAL '1 hour');

-- Trafic réseau
INSERT INTO network_traffic (device_id, destination, bytes_in, bytes_out, protocol, timestamp) VALUES
('DEV-001', 'cloud.hikvision.com', 1024000, 512000, 'HTTPS', NOW() - INTERVAL '1 hour'),
('DEV-001', '185.234.72.15', 0, 2048, 'TCP', NOW() - INTERVAL '2 hours'),
('DEV-003', 'home.nest.com', 256000, 128000, 'HTTPS', NOW() - INTERVAL '30 minutes'),
('DEV-003', '47.88.12.99', 0, 4096, 'TCP', NOW() - INTERVAL '5 hours'),
('DEV-006', 'amazon.com', 2048000, 1024000, 'HTTPS', NOW() - INTERVAL '2 hours'),
('DEV-009', '91.234.56.78', 0, 8192, 'TCP', NOW() - INTERVAL '30 minutes');

-- Utilisateurs
INSERT INTO users (id, email, role) VALUES
('USR-001', 'admin@safelink.local', 'ADMIN'),
('USR-002', 'sophie.martin@entreprise.fr', 'IT_MANAGER'),
('USR-003', 'marc.dupont@gmail.com', 'HOME_USER'),
('USR-004', 'fatima.benali@ecole.edu', 'FACILITY_MANAGER');
