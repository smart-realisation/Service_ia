-- SafeLink Database Schema
-- Schéma simplifié pour les mesures de capteurs IoT

-- Type de mesure
CREATE TYPE type_mesure_enum AS ENUM ('TEMPERATURE','HUMIDITE','GAZ');

-- Unité de mesure
CREATE TYPE unite_mesure_enum AS ENUM ('CELSIUS','POURCENT','PPM');

-- Table des types de mesure
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

-- Index pour optimiser les requêtes
CREATE INDEX idx_mesures_type ON mesures(type_mesure_id);
CREATE INDEX idx_mesures_date ON mesures(mesure_at);

-- Données initiales des types de mesure
INSERT INTO types_mesure (code, unite, description) VALUES
    ('TEMPERATURE', 'CELSIUS', 'Température ambiante'),
    ('HUMIDITE', 'POURCENT', 'Humidité relative'),
    ('GAZ', 'PPM', 'Concentration de gaz');
