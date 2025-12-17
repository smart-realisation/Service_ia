-- SafeLink Test Data
-- Données de test pour les mesures de capteurs

-- Mesures de température (type_mesure_id = 1)
INSERT INTO mesures (type_mesure_id, valeur, mesure_at) VALUES
    (1, 22.5, NOW() - INTERVAL '6 hours'),
    (1, 23.1, NOW() - INTERVAL '5 hours'),
    (1, 24.8, NOW() - INTERVAL '4 hours'),
    (1, 25.2, NOW() - INTERVAL '3 hours'),
    (1, 24.0, NOW() - INTERVAL '2 hours'),
    (1, 22.8, NOW() - INTERVAL '1 hour'),
    (1, 21.5, NOW());

-- Mesures d'humidité (type_mesure_id = 2)
INSERT INTO mesures (type_mesure_id, valeur, mesure_at) VALUES
    (2, 45.0, NOW() - INTERVAL '6 hours'),
    (2, 48.5, NOW() - INTERVAL '5 hours'),
    (2, 52.3, NOW() - INTERVAL '4 hours'),
    (2, 55.0, NOW() - INTERVAL '3 hours'),
    (2, 50.2, NOW() - INTERVAL '2 hours'),
    (2, 47.8, NOW() - INTERVAL '1 hour'),
    (2, 46.5, NOW());

-- Mesures de gaz (type_mesure_id = 3)
INSERT INTO mesures (type_mesure_id, valeur, mesure_at) VALUES
    (3, 15.0, NOW() - INTERVAL '6 hours'),
    (3, 18.2, NOW() - INTERVAL '5 hours'),
    (3, 22.5, NOW() - INTERVAL '4 hours'),
    (3, 25.0, NOW() - INTERVAL '3 hours'),
    (3, 20.3, NOW() - INTERVAL '2 hours'),
    (3, 16.8, NOW() - INTERVAL '1 hour'),
    (3, 14.5, NOW());

-- Données supplémentaires pour tests d'anomalies
-- Température anormale (haute)
INSERT INTO mesures (type_mesure_id, valeur, mesure_at) VALUES
    (1, 48.5, NOW() - INTERVAL '30 minutes');

-- Niveau de gaz élevé (alerte)
INSERT INTO mesures (type_mesure_id, valeur, mesure_at) VALUES
    (3, 150.0, NOW() - INTERVAL '15 minutes');
